import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONI DI UTILITÀ ----------------------

def calculate_working_days(start_date, end_date):
    """
    Calcola il numero di giorni lavorativi (lun-ven) tra due date,
    includendo entrambe le estremità e sottraendo 1 (per non contare il giorno di partenza).
    """
    start = np.datetime64(start_date.date()) if isinstance(start_date, pd.Timestamp) else np.datetime64(start_date)
    end = np.datetime64(end_date.date()) if isinstance(end_date, pd.Timestamp) else np.datetime64(end_date)
    days = np.busday_count(start, end + np.timedelta64(1, 'D')) - 1
    return max(days, 0)


def analyze_publication_delays(df):
    """
    Calcola il ritardo di pubblicazione in giorni lavorativi tra 'data_registro_generale'
    e 'data_inizio_pubblicazione'.
    """
    df = df.copy()
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"])
    start_dates = df["data_registro_generale"].values.astype("datetime64[D]")
    end_dates = df["data_inizio_pubblicazione"].values.astype("datetime64[D]")
    df["ritardo_pubblicazione"] = np.busday_count(start_dates, end_dates + np.timedelta64(1, "D")) - 1
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].clip(lower=0)
    return df


def prepare_time_series_data(df):
    """
    Prepara i dati temporali per i grafici:
    - Andamento giornaliero
    - Andamento cumulato
    """
    df = df.copy()
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df.dropna(subset=["data_inizio_pubblicazione"], inplace=True)
    df["data"] = df["data_inizio_pubblicazione"].dt.date
    daily_counts = df.groupby("data").size()
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
    cumulative_counts = daily_counts.cumsum()
    return daily_counts, cumulative_counts

# ---------------------- FUNZIONI DI VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, daily_counts, cumulative_counts):
    """ Visualizza i grafici temporali con ECharts """
    x_data = daily_counts.index.astype(str).tolist()
    y_daily = daily_counts.values.tolist()
    y_cumulative = cumulative_counts.values.tolist()
    
    options_daily = {
        "title": {"text": "Andamento giornaliero"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": {"type": "value"},
        "series": [{"type": "line", "data": y_daily, "smooth": True}]
    }
    container.echarts(options_daily, height="400px")
    
    options_cumulative = {
        "title": {"text": "Andamento cumulato"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": {"type": "value"},
        "series": [{"type": "line", "data": y_cumulative, "smooth": True}]
    }
    container.echarts(options_cumulative, height="400px")


def display_ritardi_tab(container, df):
    """ Visualizza i ritardi medi di pubblicazione per mittente. """
    df = analyze_publication_delays(df)
    performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    performance = performance.sort_values(by="ritardo_pubblicazione", ascending=False)
    x_data = performance["mittente"].tolist()
    y_data = performance["ritardo_pubblicazione"].tolist()
    
    options = {
        "title": {"text": "Ritardi medi per mittente"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": y_data}]
    }
    container.echarts(options, height="400px")

# ---------------------- FUNZIONE PRINCIPALE ----------------------

def page_analisi(df):
    st.header("📊 ANALISI")
    daily_counts, cumulative_counts = prepare_time_series_data(df)
    tab_temporale, tab_ritardi = st.tabs(["📆 Andamento Temporale", "⏳ Ritardi"])
    with tab_temporale:
        display_temporal_tab(tab_temporale, daily_counts, cumulative_counts)
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)
