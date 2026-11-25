"""Streamlit UI: ask business questions about the sales database in plain English."""
import streamlit as st

from sql_agent import SQLAgent

st.set_page_config(page_title="Text-to-SQL Chatbot", page_icon="🗄️", layout="wide")


@st.cache_resource
def get_agent() -> SQLAgent:
    return SQLAgent()


agent = get_agent()

st.title("🗄️ Text-to-SQL Chatbot")
st.caption("Ask questions about the sample sales database. The bot writes the SQL, runs it read-only and explains the result.")

with st.sidebar:
    st.header("Try asking")
    examples = [
        "Which 3 cities generated the most revenue in 2025?",
        "Show monthly revenue for 2025",
        "Which product category sells the most units?",
        "Top 5 customers by revenue and their segment",
        "What percentage of orders were cancelled?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex
    with st.expander("Database schema"):
        st.code(agent.schema.split("\n\n")[0], language="sql")

if "history" not in st.session_state:
    st.session_state.history = []

for item in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(item["q"])
    with st.chat_message("assistant"):
        st.markdown(item["answer"])
        st.code(item["sql"], language="sql")
        if item["data"] is not None:
            st.dataframe(item["data"], use_container_width=True)

question = st.chat_input("e.g. Which month had the highest revenue?") or st.session_state.pop("pending", None)
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Writing and running SQL..."):
            out = agent.ask(question)
        st.markdown(out["answer"])
        st.code(out["sql"], language="sql")
        if out["data"] is not None:
            st.dataframe(out["data"], use_container_width=True)
            num_cols = out["data"].select_dtypes("number").columns
            if len(out["data"]) > 1 and len(num_cols) == 1 and out["data"].shape[1] == 2:
                st.bar_chart(out["data"].set_index(out["data"].columns[0]))
    st.session_state.history.append({"q": question, **out})
