import streamlit as st
import sqlite3
import pandas as pd

# Funzione per connettersi al database
def get_data(query, params=()):
    with sqlite3.connect("pubblicazioni.db") as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

# Layout dell'interfaccia
st.title("📜 Albo Pretorio - Ricerca e Filtri")

# Opzioni di ricerca e filtro
col1, col2 = st.columns(2)

with col1:
    search_term = st.text_input("🔍 Cerca per parola chiave (oggetto, mittente, tipo atto):")

with col2:
    filtro_tipo_atto = st.selectbox("📌 Filtra per Tipo Atto", ["Tutti"] + get_data("SELECT DISTINCT tipo_atto FROM pubblicazioni")['tipo_atto'].tolist())

# Query dinamica
query = "SELECT * FROM pubblicazioni WHERE 1=1"
params = []

if search_term:
    query += " AND (oggetto_atto LIKE ? OR mittente LIKE ? OR tipo_atto LIKE ?)"
    params.extend([f"%{search_term}%"] * 3)

if filtro_tipo_atto != "Tutti":
    query += " AND tipo_atto = ?"
    params.append(filtro_tipo_atto)

# Ottenere dati filtrati
df = get_data(query, params)

# Mostrare la tabella
st.dataframe(df)

# Mostrare dettagli quando si seleziona una riga
if not df.empty:
    selected_index = st.selectbox("📄 Seleziona una pubblicazione per dettagli:", df.index.tolist())
    selected_data = df.iloc[selected_index]
    st.write(selected_data)
    
    # Link documento principale e allegati
    st.markdown(f"**📎 Documento:** [Link]({selected_data['documento']})")
    allegati_links = selected_data['allegati'].split(',') if selected_data['allegati'] else []
    for i, link in enumerate(allegati_links):
        st.markdown(f"**📂 Allegato {i+1}:** [Link]({link})")
