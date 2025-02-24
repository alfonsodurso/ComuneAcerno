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
        df = df[pd.to_datetime(df["data_inizio_pubblicazione"]) >= pd.to_datetime(data_da)]
    if data_a:
        df = df[pd.to_datetime(df["data_fine_pubblicazione"]) <= pd.to_datetime(data_a)]
    return df

# Caricamento dati
df = get_pubblicazioni()

# Modifica nomi delle colonne per leggibilità
df.columns = [col.replace('_', ' ').title() for col in df.columns]

# Interfaccia Streamlit
st.set_page_config(page_title="Albo Pretorio", layout="wide")
st.title("📜 Elenco Pubblicazioni")

# Filtri
with st.expander("Filtri di Ricerca"):
    col1, col2, col3 = st.columns([3, 1, 2])
    ricerca = col1.text_input("🔍 Ricerca testuale")
    tipo_atto_options = ["Tutti"] + sorted(df["Tipo Atto"].dropna().unique().tolist())
    tipo_atto = col2.selectbox("📂 Filtra per Tipologia di Atto", tipo_atto_options)
    col3_1, col3_2 = col3.columns(2)
    data_da = col3_1.date_input("📅 Data inizio", None)
    data_a = col3_2.date_input("📅 Data fine", None)

# Applica filtri
df_filtrato = filtra_pubblicazioni(df, ricerca, tipo_atto, data_da, data_a)

# Mostra tabella con formattazione migliorata
st.dataframe(df_filtrato, use_container_width=True)

# Ricerca per Numero Pubblicazione
st.subheader("🔎 Dettagli Pubblicazione")
numero_pubblicazione = st.text_input("Inserisci il numero della pubblicazione")

if numero_pubblicazione:
    dettagli = df[df["Numero Pubblicazione"] == numero_pubblicazione]
    if not dettagli.empty:
        st.write("### 📄 Dettagli")
        for col in dettagli.columns:
            st.write(f"**{col}:** {dettagli.iloc[0][col]}")
    else:
        st.warning("⚠️ Nessuna pubblicazione trovata con questo numero.")
