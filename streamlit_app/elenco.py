import streamlit as st
import pandas as pd

def page_elenco(df):
    st.header("📋 ELENCO")

    # Filtro dei dati (come nel codice originale)
    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipo_atto = col2.selectbox("Tipologia di Atto", tipologie)

        # Intervallo di date
        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None)
        data_a = col_date2.date_input("Data fine", None)

    # Filtro dei dati
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    # Controllo se ci sono risultati
    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
    else:
        # Colonne disponibili
        available_columns = set(filtered.columns)
        columns_to_keep = ["numero_pubblicazione", "mittente", "tipo_atto", "data_inizio_pubblicazione", "oggetto_atto", "documento_principale", "allegati"]
        valid_columns = [col for col in columns_to_keep if col in available_columns]
        df_reduced = filtered[valid_columns].copy()

        # Converti NaN in stringhe per colonne con allegati e documenti
        if "documento" in df_reduced:
            df_reduced["documento"] = df_reduced["documento"].fillna("").astype(str)
        if "allegati" in df_reduced:
            df_reduced["allegati"] = df_reduced["allegati"].fillna("").astype(str)

        # Stile per impostare la larghezza minima delle colonne con numeri e date
        def style_min_width(val):
            if isinstance(val, (int, float)):  # Se il valore è numerico
                return "width: 80px;"
            elif isinstance(val, pd.Timestamp):  # Se il valore è una data
                return "width: 120px;"
            return ""

        # Mostra la tabella con scorrimento orizzontale
        st.dataframe(
            df_reduced.style.applymap(style_min_width),
            use_container_width=True,
        )
