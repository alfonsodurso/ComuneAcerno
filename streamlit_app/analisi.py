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

# ------------------------Tipologie & Mittenti----------------------------

def prepare_tipo_atto_data(df: pd.DataFrame) -> list:
    """
    Prepara i dati per la distribuzione delle tipologie di atto pubblicate.
    """
    tipo_counts = df["tipo_atto"].value_counts().to_dict()
    return [{"value": count, "name": tipo} for tipo, count in tipo_counts.items()]

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

# ------------------------Tipologie & Mittenti----------------------------

def crea_doughnut_chart(data: list) -> dict:
    """
    Configura il grafico a ciambella (doughnut chart) per la distribuzione delle tipologie di atto.
    """
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Tipologie Atto",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": "20", "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": data,
            }
        ],
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

# ------------------------Tipologie & Mittenti----------------------------

def display_tipologie_mittenti_tab(container, df: pd.DataFrame):
    """
    Visualizza la scheda Tipologie & Mittenti con la selezione delle tipologie di atto e il grafico a ciambella.
    """
    with container:
        # Selezione della visualizzazione
        selected_view = st.radio("Seleziona la visualizzazione:", ["Tipologie Atto"], horizontal=True)

        # Filtriamo i dati in base alla multiselect
        available_types = df["tipo_atto"].unique().tolist()
        selected_types = st.multiselect("Filtra per tipologia di atto:", available_types, default=available_types)
        filtered_df = df[df["tipo_atto"].isin(selected_types)]

        if selected_view == "Tipologie Atto":
            tipo_data = prepare_tipo_atto_data(filtered_df)
            if tipo_data:
                st_echarts(options=crea_doughnut_chart(tipo_data), height="500px")
            else:
                st.warning("Nessun dato disponibile per la selezione attuale.")

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
    with tab_tipologie:
        display_tipologie_mittenti_tab(tab_tipologie, df)

if __name__ == "__main__":
    page_analisi(df_example)
