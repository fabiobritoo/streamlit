import streamlit as st
import pandas as pd
import numpy as np

import psycopg2


def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

rows = run_query("SELECT * from atendimentos;")
df = pd.read_sql_query('select * from "atendimentos"',con=conn)

# Print results.
for row in rows:
    st.write(f"{row[0]} has a :{row[1]}:")

st.title('Serviço de Atendimentos')
