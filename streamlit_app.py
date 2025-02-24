import streamlit as st
import sqlite3
import pandas as pd

# Funzione per ottenere le pubblicazioni dal database
def get_pubblicazioni(filtro_testo="", tipo_atto="", data_da=None, data_a=None):
    conn = sqlite3.connect("pubblicazioni.db")
    query = "SELECT * FROM pubblicazioni WHERE 1=1"
    params = []
    
    if filtro_testo:
        query += " AND (oggetto_atto LIKE ? OR mittente LIKE ? OR numero_pubblicazione LIKE ? )"
        params.extend([f"%{filtro_testo}%"] * 3)
    
    if tipo_atto:
        query += " AND tipo_atto = ?"
        params.append(tipo_atto)
    
    if data_da:
        query += " AND data_inizio_pubblicazione >= ?"
        params.append(data_da)
    
    if data_a:
        query += " AND data_fine_pubblicazione <= ?"
        params.append(data_a)
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# Layout della pagina
st.title("Elenco Pubblicazioni")

# Sezione filtri
filtro_testo = st.text_input("Ricerca testuale")
tipo_atto = st.selectbox("Tipologia di atto", ["", "Determina", "Delibera", "Avviso"], index=0)
col1, col2 = st.columns(2)
with col1:
    data_da = st.date_input("Data da", None)
with col2:
    data_a = st.date_input("Data a", None)

# Mostra la tabella con i risultati
pubblicazioni = get_pubblicazioni(filtro_testo, tipo_atto, data_da, data_a)
st.dataframe(pubblicazioni)

# Sezione ricerca per numero pubblicazione
st.header("Dettaglio Pubblicazione")
num_pub = st.text_input("Inserisci numero pubblicazione")
if num_pub:
    dettaglio = get_pubblicazioni(filtro_testo=num_pub)
    if not dettaglio.empty:
        st.write(dettaglio)
    else:
        st.warning("Nessuna pubblicazione trovata.")
