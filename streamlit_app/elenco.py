import streamlit as st
from common import filter_data

def page_elenco(df):
    st.header("📋 ELENCO")

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipo_atto = col2.selectbox("Tipologia di Atto", tipologie)

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None)
        data_a = col_date2.date_input("Data fine", None)

    # **Filtriamo i dati automaticamente**
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
    else:
        # **Mantieni solo le colonne principali**
        columns_to_keep = ["numero_pubblicazione", "mittente", "tipo_atto", "data_inizio_pubblicazione", "oggetto_atto", "documento", "allegati"]
        df_reduced = filtered[columns_to_keep].copy()

        # **Mostra URL intere senza icone**
        df_reduced["Documento"] = df_reduced["documento"].astype(str)  # Convertiamo NaN in stringhe per evitare errori
        df_reduced["Allegati"] = df_reduced["allegati"].astype(str)

        st.dataframe(df_reduced, use_container_width=True)
