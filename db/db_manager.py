import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

def prepara_dati_serie_temporali(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dataset giornaliero e cumulato con le colonne:
      - Area Tecnica 1, Area Tecnica 2, Area Vigilanza,
        Area Amministrativa, Comune di Acerno, Altri, TOTALE
    """
    # Copia e preparazione della data
    df_temp = df.copy()
    df_temp["data_inizio_pubblicazione"] = pd.to_datetime(df_temp["data_inizio_pubblicazione"], errors="coerce")
    df_temp = df_temp.dropna(subset=["data_inizio_pubblicazione"])
    df_temp["data"] = df_temp["data_inizio_pubblicazione"].dt.date

    # Crea la pivot: ogni riga rappresenta una data, ogni colonna un mittente
    pivot = df_temp.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0)
    pivot = pivot.sort_index()

    # Definisci i mittenti da mostrare
    active_senders = ["Area Tecnica 1", "Area Tecnica 2", "Area Vigilanza", "Area Amministrativa", "Comune di Acerno"]

    # Se un mittente attivo non compare nel pivot, aggiungilo con valore 0
    for sender in active_senders:
        if sender not in pivot.columns:
            pivot[sender] = 0

    # Calcola "Altri": la somma di tutti i mittenti che non sono nei mittenti attivi
    others = [col for col in pivot.columns if col not in active_senders]
    pivot["Altri"] = pivot[others].sum(axis=1) if others else 0

    # Calcola "TOTALE" come somma degli active senders e della colonna "Altri"
    pivot["TOTALE"] = pivot[active_senders + ["Altri"]].sum(axis=1)

    # Riordina le colonne nel seguente ordine:
    # [Area Tecnica 1, Area Tecnica 2, Area Vigilanza, Area Amministrativa, Comune di Acerno, Altri, TOTALE]
    ordered_columns = active_senders + ["Altri", "TOTALE"]
    pivot = pivot[ordered_columns]

    # Dataset giornaliero: resetta l'indice e formatta la data
    daily_dataset = pivot.reset_index()
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))

    # Dataset cumulato: somma cumulativa per ogni colonna (escludendo la data)
    cumulative_dataset = daily_dataset.copy()
    for col in ordered_columns:
        cumulative_dataset[col] = cumulative_dataset[col].cumsum()
    # La colonna data rimane uguale (è la stessa per tutte le righe)
    
    return daily_dataset, cumulative_dataset

# Funzione di visualizzazione (manteniamo il lazy loading e le animazioni già implementate)
def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    # Converte i valori per evitare problemi di serializzazione (ad esempio Timestamp)
    source = dataset.values.tolist()
    def convert_cell(cell):
        if hasattr(cell, "strftime"):
            return cell.strftime("%d-%m-%Y")
        return cell
    source = [[convert_cell(cell) for cell in row] for row in source]
    
    return {
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_cols,
            "source": source
        }],
        "title": {"text": title},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": selected_cols[1:], "bottom": "0%"},
        "xAxis": {"type": "category"},
        "yAxis": {},
        "grid": {"bottom": "5%"},
        "series": [{
            "type": "line",
            "name": col,
            "encode": {"x": "data", "y": col},
            "smooth": True
        } for col in selected_cols[1:]]
    }

def crea_config_calendar(calendar_data: list) -> dict:
    return {
        "tooltip": {"position": "top"},
        "visualMap": {
            "min": 0,
            "max": max([x[1] for x in calendar_data]) if calendar_data else 0,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "top": "top",
        },
        "calendar": {
            "range": [calendar_data[0][0], calendar_data[-1][0]] if calendar_data else "",
            "cellSize": ["auto", 20],
            "dayLabel": {"nameMap": "it"},
            "monthLabel": {"nameMap": "it"},
            "yearLabel": {"position": "top"},
        },
        "series": [{
            "type": "heatmap",
            "coordinateSystem": "calendar",
            "data": calendar_data
        }]
    }

def prepara_dati_calendario(df: pd.DataFrame) -> list:
    # Converte la colonna data (già in formato stringa) in datetime per il raggruppamento
    df["data"] = pd.to_datetime(df["data"], format="%d-%m-%Y")
    total_per_day = df.groupby(df["data"].dt.date)["TOTALE"].sum().reset_index()
    total_per_day.columns = ["date", "total"]
    return [[str(row["date"]), row["total"]] for _, row in total_per_day.iterrows()]

def display_temporal_tab(container, df: pd.DataFrame):
    daily_data, cumulative_data = prepara_dati_serie_temporali(df)
    calendar_data = prepara_dati_calendario(daily_data)

    # Le colonne da usare includono "data" e poi i valori nell'ordine desiderato
    selected_cols = ["data", "Area Tecnica 1", "Area Tecnica 2", "Area Vigilanza", 
                     "Area Amministrativa", "Comune di Acerno", "Altri", "TOTALE"]

    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data, selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data, selected_cols),
        "heatmap_calendario": crea_config_calendar(calendar_data),
    }

    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
        "Heatmap Calendario": "heatmap_calendario",
    }
    
    selected_label = st.radio("Seleziona il grafico", list(tab_labels.keys()), horizontal=True)
    selected_key = tab_labels[selected_label]

    st.markdown("""
        <style>
            .echarts-container { 
                transition: opacity 0.5s ease-in-out; 
                opacity: 1;
            }
            .echarts-container.hidden {
                opacity: 0;
            }
        </style>
        """, unsafe_allow_html=True)

    with st.container():
        try:
            st_echarts(options=schede[selected_key], key=selected_key)
        except Exception as e:
            st.error("Errore durante il caricamento del grafico.")
            st.exception(e)

def page_analisi(df: pd.DataFrame):
    st.header("📊 ANALISI")
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])
    with tab_temporale:
        display_temporal_tab(tab_temporale, df)
