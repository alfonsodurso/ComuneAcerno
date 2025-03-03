import streamlit as st
import datetime
from common import filter_data

def page_elenco(df):
    st.header("ELENCO")
    st.markdown("Vista tabellare di tutte le pubblicazioni, ordinate dalla più recente alla meno recente.")
    
    # default_start = datetime.date(1900, 1, 1)
    # default_end = datetime.date(2100, 1, 1)
    
    col1, col2 = st.columns(2)
    ricerca = col1.text_input("🔍 Ricerca", key="elenco_ricerca")
    tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
    tipologia_selezionata = col2.selectbox("Filtra per Tipologia di Atto", tipologie, key="elenco_tipologia")
    
    col_date1, col_date2 = st.columns(2)
    data_da = col_date1.date_input("Data inizio", value=default_start, key="elenco_data_da")
    data_a = col_date2.date_input("Data fine", value=default_end, key="elenco_data_a")
    
    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)
    
    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
    else:
        # Rinominiamo le colonne per la visualizzazione
        filtered.columns = [col.replace('_', ' ').title() for col in filtered.columns]
        st.dataframe(filtered, use_container_width=True)
