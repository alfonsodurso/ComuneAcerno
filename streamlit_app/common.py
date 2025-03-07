import sqlite3
import pandas as pd

def load_data():
    conn = sqlite3.connect("pubblicazioni.db")
    query = "SELECT * FROM pubblicazioni"
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def filter_data(df, ricerca, tipo_atto, data_da, data_a):
    filtered = df.copy()
    if ricerca:
        filtered = filtered[filtered.apply(lambda row: row.astype(str).str.contains(ricerca, case=False, na=False).any(), axis=1)]
    if tipo_atto and tipo_atto != "Tutti":
        filtered = filtered[filtered["tipo_atto"] == tipo_atto]
    if data_da:
        filtered = filtered[pd.to_datetime(filtered["data_inizio_pubblicazione"]) >= pd.to_datetime(data_da)]
    if data_a:
        filtered = filtered[pd.to_datetime(filtered["data_fine_pubblicazione"]) <= pd.to_datetime(data_a)]
    return filtered
