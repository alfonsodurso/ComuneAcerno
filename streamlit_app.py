import streamlit as st
import sqlite3
import pandas as pd

# Funzione per ottenere i dati dal database
def get_data():
    with sqlite3.connect("pubblicazioni.db") as conn:
        query = "SELECT * FROM pubblicazioni"
        df = pd.read_sql(query, conn)
    return df

# Carica i dati
df = get_data()

# Rinomina le colonne
column_mapping = {col: col.replace("_", " ").title() for col in df.columns}
df.rename(columns=column_mapping, inplace=True)

# Nascondi la chiave primaria
if "Numero Pubblicazione" in df.columns:
    df_display = df.drop(columns=["Numero Pubblicazione"])
else:
    df_display = df

# Sidebar con filtri
st.sidebar.header("Filtri")
search_text = st.sidebar.text_input("Cerca nelle pubblicazioni")
tipo_atto = st.sidebar.selectbox("Filtra per Tipo Atto", ["Tutti"] + sorted(df["Tipo Atto"].dropna().unique().tolist()))
data_da = st.sidebar.date_input("Data Inizio", None)
data_a = st.sidebar.date_input("Data Fine", None)

# Applica filtri
if search_text:
    df_display = df_display[df_display.apply(lambda row: row.astype(str).str.contains(search_text, case=False, na=False).any(), axis=1)]
if tipo_atto != "Tutti":
    df_display = df_display[df_display["Tipo Atto"] == tipo_atto]
if data_da:
    df_display = df_display[pd.to_datetime(df_display["Data Inizio Pubblicazione"], errors="coerce") >= pd.to_datetime(data_da)]
if data_a:
    df_display = df_display[pd.to_datetime(df_display["Data Fine Pubblicazione"], errors="coerce") <= pd.to_datetime(data_a)]

# Mostra tabella con risultati filtrati
st.title("Elenco Pubblicazioni")
st.dataframe(df_display)

# Sezione per la ricerca dettagliata
st.header("Dettagli Pubblicazione")
numero_pubblicazione = st.text_input("Inserisci Numero Pubblicazione")
if numero_pubblicazione:
    dettaglio = df[df["Numero Pubblicazione"] == numero_pubblicazione]
    if not dettaglio.empty:
        for col, val in dettaglio.iloc[0].items():
            st.write(f"**{col}**: {val}")
    else:
        st.write("Nessuna pubblicazione trovata.")
