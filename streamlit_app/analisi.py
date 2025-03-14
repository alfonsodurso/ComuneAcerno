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

# ---------------------- FUNZIONI DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data(df):
    """
    Prepara i dati temporali per i grafici dell'andamento giornaliero e cumulato.
    """
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date

    daily_counts = df_time.groupby("data").size().rename("Pubblicazioni Giorno")
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)

    daily_counts_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values
    })

    cumulative_df = daily_counts_df.copy()
    cumulative_df["Pubblicazioni Cumulative"] = cumulative_df["Pubblicazioni Giorno"].cumsum()

    return daily_counts_df, cumulative_df

# ---------------------- FUNZIONI DI VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, daily_counts_df, cumulative_df):
    """
    Visualizza i grafici relativi all'andamento temporale con ECharts.
    """

    # Grafico giornaliero
    options_daily = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": daily_counts_df["data"].astype(str).tolist()},
        "yAxis": {"type": "value"},
        "series": [{"data": daily_counts_df["Pubblicazioni Giorno"].tolist(), "type": "line"}]
    }
    
    # Grafico cumulativo
    options_cumulative = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": cumulative_df["data"].astype(str).tolist()},
        "yAxis": {"type": "value"},
        "series": [{"data": cumulative_df["Pubblicazioni Cumulative"].tolist(), "type": "line"}]
    }

    col1, col2 = container.columns(2)
    
    col1.markdown("### 📈 Andamento giornaliero")
    st_echarts(options=options_daily, height="400px", key="daily_chart")

    col2.markdown("### 📊 Andamento cumulativo")
    st_echarts(options=options_cumulative, height="400px", key="cumulative_chart")


def display_tipologie_mittenti_tab(container, df):
    """
    Visualizza i grafici a barre per Tipologie e Mittenti usando ECharts.
    """
    col1, col2 = container.columns(2)

    # Grafico Tipologie
    if "tipo_atto" in df.columns:
        tipologia_counts = df["tipo_atto"].value_counts().reset_index()
        tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]

        options_tipologie = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": tipologia_counts["Tipo Atto"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": tipologia_counts["Numero di Pubblicazioni"].tolist(), "type": "bar"}]
        }
        
        col1.markdown("### 📌 Tipologie di atti")
        st_echarts(options=options_tipologie, height="400px", key="tipologie_chart")
    else:
        col1.warning("Dati sulle tipologie non disponibili.")

    # Grafico Mittenti
    if "mittente" in df.columns:
        mittente_counts = df["mittente"].value_counts().reset_index()
        mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]

        options_mittenti = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": mittente_counts["Mittente"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": mittente_counts["Numero di Pubblicazioni"].tolist(), "type": "bar"}]
        }
        
        col2.markdown("### 🏛 Mittenti")
        st_echarts(options=options_mittenti, height="400px", key="mittenti_chart")
    else:
        col2.warning("Dati sui mittenti non disponibili.")


def display_ritardi_tab(container, df):
    """
    Calcola e visualizza i ritardi medi di pubblicazione per ogni mittente con un grafico a barre.
    """
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df["ritardo_pubblicazione"] = (df["data_inizio_pubblicazione"] - df["data_registro_generale"]).dt.days
    df = df.dropna(subset=["ritardo_pubblicazione"])

    aggregated = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    aggregated.columns = ["Mittente", "Ritardo Medio"]
    aggregated = aggregated.sort_values(by="Ritardo Medio", ascending=False)

    options_ritardi = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": aggregated["Mittente"].tolist()},
        "yAxis": {"type": "value"},
        "series": [{"data": aggregated["Ritardo Medio"].tolist(), "type": "bar"}]
    }

    container.markdown("### ⏳ Ritardi medi per mittente")
    st_echarts(options=options_ritardi, height="400px", key="ritardi_chart")


# ---------------------- FUNZIONE PRINCIPALE ----------------------

def page_analisi(df):
    st.header("📊 ANALISI")

    # Preparazione dati per i grafici temporali
    daily_counts_df, cumulative_df = prepare_time_series_data(df)

    # Creazione dei tab
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])

    with tab_temporale:
        display_temporal_tab(tab_temporale, daily_counts_df, cumulative_df)

    with tab_tipologie:
        display_tipologie_mittenti_tab(tab_tipologie, df)

    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)

