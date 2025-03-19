import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------- PREPARAZIONE DATI ----------------------

def prepare_time_series_data_by_sender(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    
    I valori visualizzati saranno:
      - Area Tecnica 1
      - Area Tecnica 2
      - Area Vigilanza
      - Area Amministrativa
      - Comune di Acerno
      - Altri (somma dei mittenti non specificati sopra)
      - TOTALE (somma di tutto)
      
    La funzione mappa i nomi (in uppercase) in nomi formattati correttamente.
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

    # Definizione della mappatura per i 5 mittenti principali
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    desired_order = ["AREA TECNICA 1", "AREA TECNICA 2", "AREA VIGILANZA", "AREA AMMINISTRATIVA", "COMUNE DI ACERNO"]

    # Determina quali mittenti esistono nel pivot
    existing_senders = set(pivot.columns) - {"TOTAL"}
    # Seleziona quelli che corrispondono ai mittenti attivi desiderati
    active = [sender for sender in desired_order if sender in existing_senders]
    # Tutti gli altri saranno accorpati in "ALTRI"
    inactive = list(existing_senders - set(active))

    # Calcola la colonna "ALTRI" come somma dei mittenti non attivi (se ce ne sono)
    pivot["ALTRI"] = pivot[inactive].sum(axis=1) if inactive else 0

    # Costruisci il dizionario per rinominare le colonne:
    # - "TOTAL" diventa "TOTALE"
    # - "ALTRI" diventa "Altri"
    # - I mittenti attivi vengono mappati al formato desiderato
    rename_dict = {"TOTAL": "TOTALE", "ALTRI": "Altri"}
    for sender in active:
        rename_dict[sender] = active_mapping[sender]

    # Ordine finale delle colonne: data, TOTALE, i 5 mittenti in ordine (se esistono) e Altri
    final_order = ["data", "TOTALE"] + [active_mapping[s] for s in desired_order if s in active] + ["Altri"]

    # Prepara il DataFrame giornaliero
    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    # Format data come stringa per visualizzazione
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    # Prepara il DataFrame cumulativo (cumulativo per ogni colonna, tranne "data")
    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------

def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    Converte ogni cella in un formato nativo serializzabile (es. se è un Timestamp, lo formatta come stringa).
    Su PC la legenda è a destra e orientata verticalmente; su smartphone la legenda è in basso, sempre verticale.
    """
    # Converte il dataset in lista di liste
    source = dataset.values.tolist()

    # Helper per convertire eventuali Timestamp in stringa
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
        # Configurazione base per PC
        "legend": {
            "data": selected_cols[1:],
            "orient": "vertical",
            "right": "0%",
            "top": "middle"
        },
        "xAxis": {"type": "category"},
        "yAxis": {},
        "grid": {"right": "15%"},
        "series": [{
            "type": "line",
            "name": col,
            "encode": {"x": "data", "y": col},
            "smooth": True
        } for col in selected_cols[1:]],
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
        # Configurazione mobile: legenda in basso e orizzontale per evitare sovrapposizioni
        "media": [{
            "query": { "maxWidth": 768 },
            "option": {
                "legend": {
                    "top": "1000%",
                    "orient": "horizontal"
                },
                "grid": {
                    "top": "0%"  # Fa spazio alla legenda
                }
            }
        }]
    }

def crea_config_calendar(calendar_data: list) -> dict:
    """
    Crea la configurazione per il calendario heatmap.
    """
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

# ---------------------- VISUALIZZAZIONE CON LAYOUT A SCHEDE ----------------------

def display_temporal_tab(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali in un layout a schede (card layout) con lazy loading, animazioni e dimensioni responsive.
    """
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)
    
    # Prepara i dati per il calendario partendo dal dataset giornaliero
    df_calendar = daily_data.copy()
    df_calendar["data"] = pd.to_datetime(df_calendar["data"], format="%d-%m-%Y")
    total_per_day = df_calendar.groupby(df_calendar["data"].dt.date)["TOTALE"].sum().reset_index()
    total_per_day.columns = ["date", "total"]
    calendar_data = [[str(row["date"]), row["total"]] for _, row in total_per_day.iterrows()]

    # L'ordine delle colonne, come definito nella funzione di preparazione, è:
    # data, TOTALE, Area Tecnica 1, Area Tecnica 2, Area Vigilanza, Area Amministrativa, Comune di Acerno, Altri
    selected_cols = daily_data.columns.tolist()

    # Configurazioni per i grafici
    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data, selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data, selected_cols),
        "heatmap_calendario": crea_config_calendar(calendar_data),
    }

    # Mappa etichette utente -> chiavi interne (semplici, senza caratteri speciali)
    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
        "Heatmap Calendario": "heatmap_calendario",
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
