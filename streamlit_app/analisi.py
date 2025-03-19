import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONI DI PREPARAZIONE DATI ----------------------

def prepara_dati_serie_temporali(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list]:
    df_temp = df.copy()
    df_temp["data_inizio_pubblicazione"] = pd.to_datetime(df_temp["data_inizio_pubblicazione"], errors="coerce")
    df_temp = df_temp.dropna(subset=["data_inizio_pubblicazione"])
    df_temp["data"] = df_temp["data_inizio_pubblicazione"].dt.date

    pivot = df_temp.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()
    pivot["TOTALE"] = pivot.sum(axis=1)
    senders = sorted([col for col in pivot.columns if col != "TOTAL"])
    daily_dataset = pivot.reset_index()

    cumulative_dataset = daily_dataset.copy()
    for col in cumulative_dataset.columns:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    cumulative_dataset["data"] = cumulative_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))

    return daily_dataset, cumulative_dataset, senders

def prepara_dati_calendario(df: pd.DataFrame) -> list:
    df["data"] = pd.to_datetime(df["data"], format="%d-%m-%Y")
    total_per_day = df.groupby(df["data"].dt.date)["TOTALE"].sum().reset_index()
    total_per_day.columns = ["date", "total"]
    return [[str(row["date"]), row["total"]] for _, row in total_per_day.iterrows()]

# ---------------------- FUNZIONI DI VISUALIZZAZIONE ----------------------

def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    return {
        "animationDuration": 500,
        "dataset": [{"id": "dataset_raw", "dimensions": selected_cols, "source": dataset.values.tolist()}],
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

# ---------------------- LAYOUT A SCHEDE ----------------------

def display_temporal_tab(container, df: pd.DataFrame):
    daily_data, cumulative_data, senders = prepara_dati_serie_temporali(df)
    calendar_data = prepara_dati_calendario(daily_data)

    selected_cols = ["data", "TOTAL"] + senders

    schede = {
        "📈 Andamento Giornaliero": crea_config_chart("Andamento giornaliero", daily_data, selected_cols),
        "📉 Andamento Cumulato": crea_config_chart("Andamento cumulato", cumulative_data, selected_cols),
        "📅 Heatmap Calendario": crea_config_calendar(calendar_data),
    }

    # Variabile per la selezione della scheda
    selected_tab = st.radio("Seleziona il grafico", list(schede.keys()), horizontal=True)

    # Applica un'animazione di transizione tra i grafici
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

    st.markdown('<div class="echarts-container">', unsafe_allow_html=True)
    st_echarts(options=schede[selected_tab], key=selected_tab)
    st.markdown("</div>", unsafe_allow_html=True)

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
