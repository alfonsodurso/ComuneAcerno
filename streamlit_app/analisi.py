import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI MAPPATURA DEI MITTENTI ----------------------
def mappa_mittenti(colonne: list) -> tuple[list, list, dict]:
    """
    Data la lista delle colonne (mittenti) presenti nel pivot, determina:
    - I mittenti attivi secondo l'ordine desiderato.
    - I mittenti inattivi.
    - Il dizionario di rinominazione per i mittenti attivi.
    
    I nomi originali sono in uppercase.
    """
    # Mapping e ordine desiderato
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    desired_order = ["AREA TECNICA 1", "AREA TECNICA 2", "AREA VIGILANZA", "AREA AMMINISTRATIVA", "COMUNE DI ACERNO"]
    
    # Determina mittenti attivi e inattivi
    # Escludiamo la colonna "TOTAL" se presente
    esistenti = set(colonne) - {"TOTAL"}
    attivi = [sender for sender in desired_order if sender in esistenti]
    inattivi = list(esistenti - set(attivi))
    
    # Dizionario per la rinominazione
    rename_dict = {sender: active_mapping[sender] for sender in attivi}
    rename_dict.update({"TOTAL": "TOTALE", "ALTRI": "Altri"})
    
    return attivi, inattivi, rename_dict

    
# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------
def prepare_time_series_data_by_sender(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    I nomi dei mittenti nel df sono in uppercase.
    """
    df_copy = df.copy()
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_inizio_pubblicazione"])
    df_copy["data"] = df_copy["data_inizio_pubblicazione"].dt.date

    # Creazione della tabella pivot raggruppata per data e mittente
    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()
    
    # Totale per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)

    # Otteniamo le mappature dei mittenti
    attivi, inattivi, rename_dict = mappa_mittenti(list(pivot.columns))
    
    # Sommiamo i mittenti inattivi in una colonna "ALTRI"
    pivot["ALTRI"] = pivot[inattivi].sum(axis=1) if inattivi else 0

    # Ordiniamo le colonne come desiderato
    final_order = ["data", "TOTALE"] + [rename_dict[s] for s in attivi] + ["Altri"]

    # Reset dell'indice e rinominazione delle colonne
    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    # Creazione del dataset cumulativo
    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

    
# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------
def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    Includiamo la legenda per permettere il filtraggio tramite interazione.
    """
    # Prepara i dati
    source = dataset.values.tolist()
    source = [[cell.strftime("%d-%m-%Y") if hasattr(cell, "strftime") else cell for cell in row] for row in source]
    
    return {
        "title": {"text": title},
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_cols,
            "source": source
        }],
        "tooltip": {"trigger": "axis"},
        "legend": {
            # Mostriamo tutte le serie (esclusa la colonna "data")
            "data": selected_cols[1:]
        },
        "xAxis": {"type": "category"},
        "yAxis": {},
        "series": [{
            "type": "line",
            "name": col,
            "encode": {"x": "data", "y": col},
            "smooth": True
        } for col in selected_cols[1:]],
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
    }

    
# ---------------------- VISUALIZZAZIONE ----------------------
def display_temporal_tab(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali.
    Il filtraggio delle serie avviene tramite la legenda del grafico.
    """
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)
    
    # Utilizziamo tutte le colonne generate, la prima è "data"
    selected_cols = daily_data.columns.tolist()

    # Configurazione dei grafici
    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data, selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data, selected_cols),
    }

    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
    }
    selected_label = st.radio("Seleziona il grafico", list(tab_labels.keys()), horizontal=True)
    selected_key = tab_labels[selected_label]

    with container:
        try:
            st_echarts(options=schede[selected_key], key=selected_key, height="500px")
        except Exception as e:
            st.error("Errore durante il caricamento del grafico.")
            st.exception(e)

        
# ---------------------- FUNZIONE PRINCIPALE ----------------------
def page_analisi(df: pd.DataFrame):
    st.header("📊 ANALISI")
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])
    with tab_temporale:
        display_temporal_tab(tab_temporale, df)


if __name__ == "__main__":
    # Assicurarsi di avere un dataframe df_example già definito
    page_analisi(df_example)
