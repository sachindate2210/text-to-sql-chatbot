"""Text-to-SQL: schema-aware SQL generation, safe read-only execution, self-correction and a plain-English summary."""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DB_PATH = Path(__file__).with_name("sales.db")
MAX_ROWS = 200

SQL_PROMPT = """You are an expert SQLite analyst. Write ONE SQLite SELECT query that answers the question.
Rules:
- Use only the tables and columns in the schema.
- Revenue = orders.quantity * products.unit_price. Exclude orders with status = 'cancelled' from revenue unless asked.
- Use strftime('%Y-%m', order_date) for months.
- Add LIMIT 50 unless the question asks for a single number.
- Return only the SQL, no explanation, no markdown.

Schema:
{schema}"""

SUMMARY_PROMPT = """Question: {question}
SQL used: {sql}
Result (first rows, CSV):
{rows}

Answer the question in 1-3 plain-English sentences for a business user. Use the numbers from the result; format money in INR with commas."""

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma|vacuum)\b", re.I)


class SQLAgent:
    def __init__(self, db_path: Path = DB_PATH):
        if not Path(db_path).exists():
            from seed_db import build
            build(Path(db_path))
        self.db_path = Path(db_path)
        self.llm = Groq()
        self.schema = self._schema()

    def _connect(self) -> sqlite3.Connection:
        # Read-only connection: even a bad query cannot change data.
        return sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)

    def _schema(self) -> str:
        with self._connect() as con:
            rows = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
            samples = []
            for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                df = pd.read_sql_query(f"SELECT * FROM {name} LIMIT 2", con)
                samples.append(f"-- sample rows from {name}:\n{df.to_csv(index=False)}")
        return "\n".join(r[0] for r in rows) + "\n\n" + "\n".join(samples)

    def _chat(self, system: str, user: str) -> str:
        resp = self.llm.chat.completions.create(
            model=MODEL, temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content.strip()

    @staticmethod
    def clean_sql(text: str) -> str:
        text = re.sub(r"^```(?:sql)?|```$", "", text.strip(), flags=re.I | re.M).strip()
        return text.rstrip(";").strip()

    @staticmethod
    def validate(sql: str) -> None:
        if not re.match(r"^\s*(select|with)\b", sql, re.I):
            raise ValueError("Only SELECT queries are allowed.")
        if FORBIDDEN.search(sql) or ";" in sql:
            raise ValueError("Query contains a forbidden statement.")

    def generate_sql(self, question: str, error: str | None = None, previous: str | None = None) -> str:
        user = f"Question: {question}"
        if error:
            user += f"\n\nYour previous query failed.\nQuery: {previous}\nError: {error}\nWrite a corrected query."
        return self.clean_sql(self._chat(SQL_PROMPT.format(schema=self.schema), user))

    def run_sql(self, sql: str) -> pd.DataFrame:
        self.validate(sql)
        with self._connect() as con:
            return pd.read_sql_query(sql, con).head(MAX_ROWS)

    def ask(self, question: str, retries: int = 2) -> dict:
        sql, error = None, None
        for _ in range(retries + 1):
            sql = self.generate_sql(question, error, sql)
            try:
                df = self.run_sql(sql)
                break
            except Exception as exc:  # self-correction loop: feed the error back to the model
                error = str(exc)
        else:
            return {"sql": sql, "data": None, "answer": f"Sorry, I couldn't build a working query ({error})."}
        summary = self._chat(
            "You explain data results clearly and briefly.",
            SUMMARY_PROMPT.format(question=question, sql=sql, rows=df.head(20).to_csv(index=False)),
        )
        return {"sql": sql, "data": df, "answer": summary}


if __name__ == "__main__":
    import sys

    agent = SQLAgent()
    q = " ".join(sys.argv[1:]) or "Which 3 cities generated the most revenue in 2025?"
    out = agent.ask(q)
    print("Q:", q)
    print("SQL:", out["sql"])
    if out["data"] is not None:
        print(out["data"].to_string(index=False))
    print("Answer:", out["answer"])
