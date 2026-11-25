# 🗄️ Text-to-SQL Chatbot

Ask business questions in plain English. The bot reads the database schema, **writes the SQL, runs it safely (read-only), fixes its own query if it fails**, and explains the result in simple words.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

## How it works
```
Question ──► LLM + schema & sample rows ──► SQL
         ──► guard: SELECT-only, no multi-statements, read-only connection
         ──► execute ──(error?)──► send error back to LLM, retry (self-correction)
         ──► result table + chart + plain-English summary
```

**Example**
> *Which 3 cities generated the most revenue in 2025?*
```sql
SELECT c.city, SUM(o.quantity * p.unit_price) AS revenue
FROM orders o JOIN customers c ON c.id = o.customer_id JOIN products p ON p.id = o.product_id
WHERE o.status != 'cancelled' AND strftime('%Y', o.order_date) = '2025'
GROUP BY c.city ORDER BY revenue DESC LIMIT 3
```

## Safety
- The database is opened in **read-only mode** (`mode=ro`), so no query can change data
- Generated SQL must start with `SELECT`/`WITH`; `DROP`, `DELETE`, `UPDATE`, `PRAGMA` etc. are rejected
- Results are capped at 200 rows

## Run it
```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # add your free Groq API key
python seed_db.py              # creates sales.db (customers, products, 400 orders)
streamlit run app.py
```
CLI: `python sql_agent.py "Show monthly revenue for 2025"`

To use your own database, point `SQLAgent(db_path=...)` at any SQLite file; the schema is read automatically.

## Project structure
```
seed_db.py      builds the sample sales database
sql_agent.py    schema reader, SQL generation, validation, self-correction, summary
app.py          Streamlit chat UI with SQL, table and chart
```

---
Built by **[Sunil Date](https://github.com/sachindate2210)**
