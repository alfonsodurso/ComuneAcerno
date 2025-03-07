import streamlit as st
from common import load_data
from sfoglia import page_sfoglia
from elenco import page_elenco
from analisi import page_analisi
from ritardi import page_ritardi  # 🔹 Nuova pagina ritardi

# Sidebar chiusa di default su mobile
st.set_page_config(page_title="Albo Pretorio", layout="wide", initial_sidebar_state="collapsed")

# Barra di navigazione
menu = st.sidebar.radio("Seleziona una pagina:", ["📖 SFOGLIA", "📋 ELENCO", "📊 ANALISI", "⏳ RITARDI"])

df = load_data()

# Richiama la pagina selezionata
if menu == "📖 SFOGLIA":
    page_sfoglia(df)
elif menu == "📋 ELENCO":
    page_elenco(df)
elif menu == "📊 ANALISI":
    page_analisi(df)
elif menu == "⏳ RITARDI":
    page_ritardi(df)
