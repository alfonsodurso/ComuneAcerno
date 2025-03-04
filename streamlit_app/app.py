import streamlit as st
from common import load_data
from sfoglia import page_sfoglia
from elenco import page_elenco
from analisi import page_analisi

# Sidebar chiusa di default su mobile
st.set_page_config(page_title="Albo Pretorio", layout="wide", initial_sidebar_state="collapsed")

st.sidebar.title("Navigazione")
pagina = st.sidebar.radio("Seleziona pagina", ("SFOGLIA", "ELENCO", "ANALISI"))

# Carica i dati
df = load_data()

# Mostra la pagina selezionata
if pagina == "SFOGLIA":
    page_sfoglia(df)
elif pagina == "ELENCO":
    page_elenco(df)
elif pagina == "ANALISI":
    page_analisi(df)
