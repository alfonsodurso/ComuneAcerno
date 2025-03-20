import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data_by_sender(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    I mittenti nel df sono in uppercase.
    """
    # Converte la data di pubblicazione e filtra eventuali errori
    df_copy = df.copy()
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_inizio_pubblicazione"])
    df_copy["data"] = df_copy["data_inizio_pubblicazione"].dt.date

    # Crea una tabella pivot che raggruppa per data e mittente
    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()

    # Calcola il totale (TOTALE) per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)  # assicura che siano tipi Python (evita numpy.int64)

    # Mappatura per i mittenti principali (assumendo che nel df i nomi siano in uppercase)
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    desired_order = ["AREA TECNICA 1", "AREA TECNICA 2", "AREA VIGILANZA", "AREA AMMINISTRATIVA", "COMUNE DI ACERNO"]

    existing_senders = set(pivot.columns) - {"TOTAL"}
    active = [sender for sender in desired_order if sender in existing_senders]
    inactive = list(existing_senders - set(active))

    pivot["ALTRI"] = pivot[inactive].sum(axis=1) if inactive else 0

    rename_dict = {"TOTAL": "TOTALE", "ALTRI": "Altri"}
    for sender in active:
        rename_dict[sender] = active_mapping[sender]

    final_order = ["data", "TOTALE"] + [active_mapping[s] for s in desired_order if s in active] + ["Altri"]

    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------

def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    """
    source = dataset.values.tolist()
    source = [[cell.strftime("%d-%m-%Y") if hasattr(cell, "strftime") else cell for cell in row] for row in source]
    return {
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_cols,
            "source": source
        }],
        "tooltip": {"trigger": "axis"},
        "legend": {"data": selected_cols[1:], "orient": "horizontal", "top": "bottom"},
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
    Visualizza i grafici temporali con possibilità di filtrare i dati tramite una multiselect.
    """
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)
    # Escludiamo "data" per la multiselect (assicurandoci di mantenerla sempre)
    available_cols = daily_data.columns.tolist()[1:]
    selected_cols = st.multiselect("Seleziona i dati da visualizzare:", available_cols, default=available_cols)
    selected_cols.insert(0, "data")

    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data[selected_cols], selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data[selected_cols], selected_cols),
    }

    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
    }
    selected_label = st.radio("Seleziona il grafico", list(tab_labels.keys()), horizontal=True)
    selected_key = tab_labels[selected_label]

    with st.container():
        try:
            st_echarts(options=schede[selected_key], key=selected_key)
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

# Esempio di utilizzo (assicurati che il DataFrame 'df' contenga le colonne attese,
# in particolare 'data_inizio_pubblicazione' e 'mittente' in uppercase)
if __name__ == "__main__":
    # Creazione di un DataFrame di esempio per testare l'app
    data = {
        "data_inizio_pubblicazione": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "mittente": ["AREA TECNICA 1", "COMUNE DI ACERNO", "AREA VIGILANZA"]
    }
    df_example = pd.DataFrame(data)
    page_analisi(df_example)
