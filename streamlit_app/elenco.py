import streamlit as st
import pandas as pd

# Impostazione di un numero fisso di righe per pagina
ROWS_PER_PAGE = 20

# Funzione per paginare i dati
def paginate_data(df, page):
    start = page * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE
    return df[start:end]

# Funzione per la visualizzazione della tabella con le specifiche richieste
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
        # Numero totale di pagine
        total_pages = len(filtered) // ROWS_PER_PAGE + (1 if len(filtered) % ROWS_PER_PAGE > 0 else 0)

        # Pagina corrente
        page = st.slider("Pagina", min_value=0, max_value=total_pages-1, step=1)

        # Pagina dei dati filtrati
        df_paginated = paginate_data(filtered, page)

        # Colonne disponibili
        available_columns = set(df_paginated.columns)
        columns_to_keep = ["numero_pubblicazione", "mittente", "tipo_atto", "data_inizio_pubblicazione", "oggetto_atto", "documento_principale", "allegati"]
        valid_columns = [col for col in columns_to_keep if col in available_columns]
        df_reduced = df_paginated[valid_columns].copy()

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

        # Mostra la tabella con scorrimento orizzontale e verticale
        st.dataframe(
            df_reduced.style.applymap(style_min_width),
            use_container_width=True,
        )

        # Navigazione tra le pagine
        st.text(f"Pagina {page+1} di {total_pages}")
