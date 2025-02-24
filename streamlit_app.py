import streamlit as st
import sqlite3
import pandas as pd

# Funzione per ottenere i dati dal database
def get_pubblicazioni():
    conn = sqlite3.connect("pubblicazioni.db")
    query = "SELECT * FROM pubblicazioni"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Funzione per filtrare i dati
def filtra_pubblicazioni(df, ricerca, tipo_atto, data_da, data_a):
    if ricerca:
        df = df[df.apply(lambda row: row.astype(str).str.contains(ricerca, case=False, na=False).any(), axis=1)]
    if tipo_atto and tipo_atto != "Tutti":
        df = df[df["tipo_atto"] == tipo_atto]
    if data_da:
        df = df[df["data_inizio_pubblicazione"] >= data_da]
    if data_a:
        df = df[df["data_fine_pubblicazione"] <= data_a]
    return df

# Interfaccia Streamlit
st.title("Elenco Pubblicazioni")

# Caricamento dati
df = get_pubblicazioni()

# Modifica nomi delle colonne per leggibilità
df.columns = [col.replace('_', ' ').title() for col in df.columns]

# Filtri
col1, col2, col3 = st.columns([3, 1, 2])
ricerca = col1.text_input("Ricerca testuale")
tipo_atto_options = ["Tutti"] + sorted(df["Tipo Atto"].unique().tolist())
tipo_atto = col2.selectbox("Filtra per Tipologia di Atto", tipo_atto_options)
data_da = col3.date_input("Data inizio pubblicazione", None)
data_a = col3.date_input("Data fine pubblicazione", None)

# Applica filtri
df_filtrato = filtra_pubblicazioni(df, ricerca, tipo_atto, data_da, data_a)

# Mostra tabella
st.dataframe(df_filtrato)

# Ricerca per Numero Pubblicazione
st.subheader("Dettagli Pubblicazione")
numero_pubblicazione = st.text_input("Inserisci il numero di pubblicazione")

if numero_pubblicazione:
    dettagli = df[df["Numero Pubblicazione"] == numero_pubblicazione]
    if not dettagli.empty:
        for col in dettagli.columns:
            st.write(f"**{col}:** {dettagli.iloc[0][col]}")
    else:
        st.write("Nessuna pubblicazione trovata con questo numero.")
