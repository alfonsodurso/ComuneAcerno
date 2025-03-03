import streamlit as st
from common import filter_data

def page_sfoglia(df):
    st.header("SFOGLIA")

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipologia_selezionata = col2.selectbox("Tipologia di Atto", tipologie)

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None, key="sfoglia_data_da")
        data_a = col_date2.date_input("Data fine", None, key="sfoglia_data_a")

    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)

    if filtered.em
