import streamlit as st
import pandas as pd
import sqlite3

def get_pubblicazioni():
    conn = sqlite3.connect("pubblicazioni.db")
    query = "SELECT * FROM pubblicazioni"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def filtra_pubblicazioni(df, ricerca, tipo_atto, data_da, data_a):
    # Filtra per testo in tutte le colonne
    if ricerca:
        df = df[df.apply(lambda row: row.astype(str).str.contains(ricerca, case=False, na=False).any(), axis=1)]
    # Filtra per "Tipo Atto" (colonna rinominata)
    if tipo_atto and tipo_atto != "Tutti":
        df = df[df["Tipo Atto"] == tipo_atto]
    # Filtra per date utilizzando i nomi rinominati
    if data_da:
        df = df[pd.to_datetime(df["Data Inizio Pubblicazione"]) >= pd.to_datetime(data_da)]
    if data_a:
        df = df[pd.to_datetime(df["Data Fine Pubblicazione"]) <= pd.to_datetime(data_a)]
    return df

st.set_page_config(page_title="Albo Pretorio", layout="wide")
st.title("📜 Elenco Pubblicazioni")

# Carica i dati dal database
df = get_pubblicazioni()

# Rinomina le colonne per una migliore leggibilità
df.columns = [col.replace('_', ' ').title() for col in df.columns]

with st.expander("Filtri di Ricerca"):
    col1, col2, col3 = st.columns([3, 1, 2])
    ricerca = col1.text_input("🔍 Ricerca testuale")
    tipo_atto_options = ["Tutti"] + sorted(df["Tipo Atto"].dropna().unique().tolist())
    tipo_atto = col2.selectbox("📂 Filtra per Tipologia di Atto", tipo_atto_options)
    col3_1, col3_2 = col3.columns(2)
    data_da = col3_1.date_input("📅 Data inizio", None)
    data_a = col3_2.date_input("📅 Data fine", None)

# Applica i filtri usando i nomi rinominati
df_filtrato = filtra_pubblicazioni(df, ricerca, tipo_atto, data_da, data_a)
st.dataframe(df_filtrato, use_container_width=True)

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
