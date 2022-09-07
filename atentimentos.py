import streamlit as st
import pandas as pd
import numpy as np

import psycopg2
import plotly.express as px

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

def create_filter(df, label, column):
    return st.sidebar.multiselect(
    f"Select the {label}:",
    options=df[column].unique(),
    default=df[column].unique())



# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def load_data(nrows):
    df = pd.read_sql_query('select * from "atendimentos"',con=conn)
    return df

st.set_page_config(page_title="Serviço de Atendimentos", page_icon=":bar_chart:", layout="wide")

st.title("Serviço de Atendimentos")


data = load_data(10000)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

tipo_senha = create_filter(data, "Type", "tipo_senha" )
guiche = create_filter(data, "Counter", "guiche")

df_selection = data.query(
    "tipo_senha == @tipo_senha & guiche ==@guiche"
)

st.table(df_selection)
