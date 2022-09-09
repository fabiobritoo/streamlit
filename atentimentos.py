import streamlit as st
import pandas as pd
import numpy as np

import psycopg2
import plotly.express as px

from dateutil.relativedelta import relativedelta
import datetime
import pytz

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

def create_filter(df, label, column):
    return st.sidebar.multiselect(
    f"Select the {label}:",
    options=np.append(df[column].dropna().unique(),['All']),
    default='All')

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
# @st.experimental_memo(ttl=600)
def load_data(nrows):
    df = pd.read_sql_query('select * from "atendimentos"',con=conn)
    df['hora_emissao'] = df['data_emissao'].dt.hour
    df['hora_atendimento'] = df['data_atendimento'].dt.hour

    df['data_emissao_tz'] = df.data_emissao.dt.tz_localize(pytz.timezone('America/Recife'))
    df['data_atendimento_tz'] = df.data_atendimento.dt.tz_localize(pytz.timezone('America/Recife'))

    hoje = datetime.datetime.now(pytz.timezone('America/Recife')).replace(hour = 0, minute= 0, second=0, microsecond=0)
    final_hoje = hoje.replace(hour = 23, minute=59, second=59)

    inicio_mes = hoje.replace(day = 1)
    final_mes = hoje.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)

    df['emissao_this_month'] = df['data_emissao_tz'].apply(lambda x : True if x > inicio_mes and x < final_mes else False)
    df['atendimento_this_month'] = df['data_atendimento_tz'].apply(lambda x : True if x > inicio_mes and x < final_mes else False)

    df['emissao_this_day'] = df['data_emissao_tz'].apply(lambda x : True if x > hoje and x < final_hoje else False)
    df['atendimento_this_day'] = df['data_atendimento_tz'].apply(lambda x : True if x > hoje and x < final_hoje else False)

    return df


def timedelta_to_string(x):
    if pd.isnull(x):
        return '-'
    total_sec = x.total_seconds()
    hours = int(total_sec / 3600)
    minutes = int(total_sec / 60) % 60
    sec = int(total_sec - minutes*60 - hours*60*60)
    time_string = str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(sec).zfill(2)
    return time_string

def treat_data(data):
    data_show = data[["tipo_senha","numeracao","data_emissao","data_atendimento","guiche"]]
    data_show = data_show.sort_values(by = "data_emissao")
    data_show["guiche"] = data_show["guiche"].astype('string').fillna('---').str[:-2]
    data_show["tempo_atendimento"] = data_show["data_atendimento"] - data_show["data_emissao"]

    ### Tempo Médio
    tempo_medio_por_tipo = data_show[['tipo_senha','tempo_atendimento']].groupby('tipo_senha').mean()
    if len(tempo_medio_por_tipo) == 0:
        tempo_medio_por_tipo = pd.DataFrame(columns=["Tipo","Tempo Médio"])
    else:
        tempo_medio_por_tipo["tempo_atendimento"] = tempo_medio_por_tipo["tempo_atendimento"].apply(lambda x : timedelta_to_string(x))
        tempo_medio_por_tipo = tempo_medio_por_tipo.reset_index()
        tempo_medio_por_tipo.rename(columns = {
            "tipo_senha":"Tipo"
            , "tempo_atendimento":"Tempo Médio"
            }, inplace=True)

    ## Beautify
    data_show["data_emissao"] = data_show["data_emissao"].dt.strftime('%Y-%m-%d, %H:%M:%S')
    data_show["data_atendimento"] = data_show["data_atendimento"].dt.strftime('%Y-%m-%d, %H:%M:%S')
    data_show["tempo_atendimento"] = data_show["tempo_atendimento"].apply(lambda x : timedelta_to_string(x))


    data_show.rename(columns = {
        "tipo_senha":"Tipo"
        ,"numeracao":"Numeração"
        , "data_emissao":"Data de Emissão"
        , "data_atendimento":"Data de Atendimento"
        , "guiche":"Guichê"
        , "tempo_atendimento":"Tempo de Espera"
        }, inplace=True)
    
    if len(data_show) == 0:
        data_show = pd.DataFrame(columns=["Tipo", "Numeração", "Data de Emissão", "Data de Atendimento", "Guichê", "Tempo de Espera"])
    return tempo_medio_por_tipo, data_show



st.set_page_config(page_title="Serviço de Atendimentos", page_icon=":hospital:", layout="wide")

data = load_data(10000)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

tipo_senha = create_filter(data, "Type", "tipo_senha" )
if "All" in tipo_senha:
    tipo_senha = list(data['tipo_senha'].dropna().unique())

today = st.sidebar.checkbox('Only Today')
month = st.sidebar.checkbox('Only This Month')

cond_filter = ''
if (today):
    cond_filter = "& (emissao_this_day | atendimento_this_day) == @today"
if (month):
    cond_filter = "& (emissao_this_month | atendimento_this_month) == @month"

df_selection = data.query(
    "tipo_senha == @tipo_senha" + cond_filter    
)

tempo_medio, beautify_data = treat_data(df_selection)

# ---- MAINPAGE ----
st.title(":hospital: Serviço de Atendimentos")
st.markdown("##")

st.header("Estatísticas Gerais")

# TOP KPI's

data = df_selection

tipos = data['tipo_senha'].unique()

senhas_atendidas_sp = int(len(data[~data["data_atendimento"].isna() & data["tipo_senha"] == "SP"]))


left_column, middle_column, right_column = st.columns(3)
with middle_column:
    cond1 = ~data["data_atendimento"].isna()
    senhas_atendidas = int(len(data[cond1]))
    st.markdown(f"- Senhas Atendidas: {senhas_atendidas}\n")
    for tipo in tipos:        
        cond2 = data["tipo_senha"] == tipo
        senha_por_tipo = int(len(data[cond1 & cond2]))
        st.markdown(f"- Senhas Atendidas {tipo}: {senha_por_tipo}\n")

with left_column:
    cond1 = ~data["data_emissao"].isna()
    senhas_emitidas = int(len(data[cond1]))
    st.markdown(f"- Senhas Emitidas: {senhas_emitidas}")
    for tipo in tipos:        
        cond2 = data["tipo_senha"] == tipo
        senha_por_tipo = int(len(data[cond1 & cond2]))
        st.markdown(f"- Senhas Emitidas {tipo}: {senha_por_tipo}")

st.markdown("""---""")

st.header("Gráficos de Análise")

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

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

st.markdown("""---""")
st.header("Relatório de Tempo Médio")
st.table(tempo_medio)

st.markdown("""---""")
st.header("Relatório Completo")
st.table(beautify_data)
