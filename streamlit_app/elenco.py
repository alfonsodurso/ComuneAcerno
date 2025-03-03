import streamlit as st
from common import filter_data

def page_elenco(df):
    st.header("📋 ELENCO")

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca", key="elenco_ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipologia_selezionata = col2.selectbox("Tipologia di Atto", tipologie, key="elenco_tipologia")

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None, key="elenco_data_da")
        data_a = col_date2.date_input("Data fine", None, key="elenco_data_a")

        if st.button("❌ Cancella Filtri"):
            st.experimental_rerun()

    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)
    
    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
    else:
        filtered = filtered.sort_values(by=filtered.columns[0], ascending=False)
  
        filtered.columns = [col.replace('_', ' ').title() for col in filtered.columns]
        st.dataframe(filtered, use_container_width=True)
