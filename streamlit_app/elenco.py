import streamlit as st
from common import filter_data

def page_elenco(df):
    st.header("ELENCO")
    st.markdown("Vista tabellare di tutte le pubblicazioni, ordinate dalla più recente alla meno recente.")
    
    col1, col2 = st.columns(2)
    ricerca = col1.text_input("🔍 Ricerca", key="elenco_ricerca")
    tipologie = ["Tutti"] + sorted(df["Tipo Atto"].dropna().unique().tolist()) if "Tipo Atto" in df.columns else ["Tutti"]
    tipologia_selezionata = col2.selectbox("Tipologia", tipologie, key="elenco_tipologia")
    
    col_date1, col_date2 = st.columns(2)
    data_da = col_date1.date_input("Data Inizio", key="elenco_data_da")
    data_a = col_date2.date_input("Data Fine", key="elenco_data_a")
    
    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)
    
    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
    else:
        st.dataframe(filtered, use_container_width=True)
