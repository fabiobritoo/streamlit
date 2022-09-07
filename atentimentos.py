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
    options=df[column].dropna().unique(),
    default=df[column].dropna().unique())

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def load_data(nrows):
    df = pd.read_sql_query('select * from "atendimentos"',con=conn)
    df['hora_emissao'] = df['data_emissao'].dt.hour
    df['hora_atendimento'] = df['data_atendimento'].dt.hour
    return df

st.set_page_config(page_title="Serviço de Atendimentos", page_icon=":bar_chart:", layout="wide")

st.title("Serviço de Atendimentos")

data = load_data(10000)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

tipo_senha = create_filter(data, "Type", "tipo_senha" )

df_selection = data.query(
    "tipo_senha == @tipo_senha"
)

# ---- MAINPAGE ----
st.title(":bar_chart: Serviço de Atendimentos")
st.markdown("##")

# TOP KPI's

tipos = data['tipo_senha'].unique()

senhas_atendidas_sp = int(len(data[~data["data_atendimento"].isna() & data["tipo_senha"] == "SP"]))

left_column, middle_column, right_column = st.columns(3)
with left_column:
    cond1 = ~data["data_atendimento"].isna()
    senhas_atendidas = int(len(data[cond1]))
    st.subheader(f"Senhas Atendidas: {senhas_atendidas}")
    for tipo in tipos:        
        cond2 = data["tipo_senha"] == tipo
        senha_por_tipo = int(len(data[cond1 & cond2]))
        st.subheader(f"Senhas Atendidas {tipo}: {senha_por_tipo}")

with middle_column:
    cond1 = ~data["data_emissao"].isna()
    senhas_emitidas = int(len(data[cond1]))
    st.subheader(f"Senhas Emitidas: {senhas_emitidas}")
    for tipo in tipos:        
        cond2 = data["tipo_senha"] == tipo
        senha_por_tipo = int(len(data[cond1 & cond2]))
        st.subheader(f"Senhas Emitidas {tipo}: {senha_por_tipo}")

st.markdown("""---""")

# SALES BY PRODUCT LINE [BAR CHART]
senhas_por_tipo = (
    df_selection.rename(columns = {"tipo_senha":"Type", "id":"Count"}).groupby(by=["Type"]).count()[["Count"]].sort_values(by="Count")
)
fig_senhas_por_tipo = px.bar(
    senhas_por_tipo,
    x="Count",
    y=senhas_por_tipo.index,
    orientation="h",
    title="<b>Senhas Por Tipo</b>",
    color_discrete_sequence=["#0083B8"] * len(senhas_por_tipo),
    template="plotly_white",
)
fig_senhas_por_tipo.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False))
)

st.plotly_chart(fig_senhas_por_tipo)

# EMISSAO POR HORA [BAR CHART]
emissao_por_hora = df_selection.rename(columns = {"hora_emissao":"Hora Emissao", "id":"Count"}).groupby(by=["Hora Emissao"]).count()[["Count"]].sort_values(by="Count")
fig_emissao_por_hora = px.bar(
    emissao_por_hora,
    x=emissao_por_hora.index,
    y="Count",
    title="<b>Emissao de Fichas por Hora</b>",
    color_discrete_sequence=["#0083B8"] * len(emissao_por_hora),
    template="plotly_white",
)
fig_emissao_por_hora.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
)

# ATENDIMENTO POR HORA [BAR CHART]
atendimento_por_hora = df_selection.rename(columns = {"hora_atendimento":"Hora Atendimento", "id":"Count"}).groupby(by=["Hora Atendimento"]).count()[["Count"]].sort_values(by="Count")
fig_atendimento_por_hora = px.bar(
    atendimento_por_hora,
    x=atendimento_por_hora.index,
    y="Count",
    title="<b>Atendimento de Fichas por Hora</b>",
    color_discrete_sequence=["#0083B8"] * len(atendimento_por_hora),
    template="plotly_white",
)
fig_atendimento_por_hora.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
)


left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_emissao_por_hora, use_container_width=True)
right_column.plotly_chart(fig_atendimento_por_hora, use_container_width=True)


# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.table(df_selection)
