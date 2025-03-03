import sqlite3
import pandas as pd

def load_data():
    conn = sqlite3.connect("pubblicazioni.db")
    query = "SELECT * FROM pubblicazioni"
    df = pd.read_sql(query, conn)
    conn.close()
    # Rinomina le colonne per una visualizzazione più leggibile
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    # Converte in datetime (se possibile)
    if "Data Inizio Pubblicazione" in df.columns:
        df["Data Inizio Pubblicazione"] = pd.to_datetime(df["Data Inizio Pubblicazione"], errors="coerce")
    if "Data Fine Pubblicazione" in df.columns:
        df["Data Fine Pubblicazione"] = pd.to_datetime(df["Data Fine Pubblicazione"], errors="coerce")
    # Ordina dalla più recente alla meno recente
    if "Data Inizio Pubblicazione" in df.columns:
        df.sort_values("Data Inizio Pubblicazione", ascending=False, inplace=True)
    return df

def filter_data(df, ricerca, tipologia, data_da, data_a):
    filtered = df.copy()
    if ricerca:
        filtered = filtered[filtered.apply(lambda row: row.astype(str).str.contains(ricerca, case=False, na=False).any(), axis=1)]
    if tipologia and tipologia != "Tutti":
        filtered = filtered[filtered["Tipo Atto"] == tipologia]
    if data_da:
        filtered = filtered[filtered["Data Inizio Pubblicazione"] >= pd.to_datetime(data_da)]
    if data_a:
        filtered = filtered[
            (filtered["Data Fine Pubblicazione"].isnull()) |
            (filtered["Data Fine Pubblicazione"] <= pd.to_datetime(data_a))
        ]

    return filtered
