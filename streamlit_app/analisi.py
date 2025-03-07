import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
from datetime import datetime, timedelta

# ⚙️ Configurazione toolbar (Zoom con due dita, Pan disattivato)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,  # 🔹 Zoom con due dita su mobile
    "modeBarButtonsToRemove": [
        "pan2d", "select2d", "lasso2d", "zoom",
        "resetScale2d", "toggleSpikelines"
    ],
    "displayModeBar": True
}

def calculate_working_days(start_date, end_date):
    """Calcola il numero di giorni lavorativi (lun-ven) tra due date."""
    current_date = start_date
    working_days = 0

    while current_date <= end_date:
        if current_date.weekday() < 5:  # Lunedì-Venerdì
            working_days += 1
        current_date += timedelta(days=1)

    return working_days

def analyze_publication_delays(df):

    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")

    """Calcola il ritardo di pubblicazione in giorni lavorativi."""
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    
    df["ritardo_pubblicazione"] = df.apply(lambda row: 
        calculate_working_days(row["data_registro_generale"], row["data_inizio_pubblicazione"]) - 1, axis=1)
    
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].apply(lambda x: max(x, 0))  # Evita valori negativi

    return df

def analyze_mittenti_performance(df):
    """Analizza il ritardo medio di pubblicazione per ogni mittente."""
    mittente_performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    mittente_performance.columns = ["Mittente", "Ritardo medio"]
    mittente_performance = mittente_performance.sort_values(by="Ritardo medio", ascending=False)
    return mittente_performance

def page_analisi(df):
    st.header("📊 ANALISI")

    # ----- Preparazione dati per il tab "Andamento Temporale" -----
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()

    # Raggruppamento per giorno
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date
    daily_counts = df_time.groupby("data").size().rename("Pubblicazioni Giorno")
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
    daily_counts_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values
    })

    palette_giornaliera = sns.color_palette("pastel", 1).as_hex()

    # Distribuzione Mensile: raggruppa per mese (formato "YYYY-MM")
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")
    pub_per_mese["mese_dt"] = pd.to_datetime(pub_per_mese["mese"], format="%Y-%m")
    palette_mese = sns.color_palette("pastel", len(pub_per_mese)).as_hex()

    # Distribuzione Giornaliera per l'Andamento Cumulato:
    daily_cumsum = daily_counts.cumsum()
    cumulative_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values,
        "Pubblicazioni Cumulative": daily_cumsum.values
    })
    palette_cumul = sns.color_palette("pastel", 1).as_hex()

    # ----- Layout dei grafici -----
    tab1, tab2, tab3 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti", "⏳ Ritardi"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # Grafico 1: Andamento giornaliero delle pubblicazioni (Line Chart spezzata per ogni giorno)
        fig1 = px.line(daily_counts_df, x="data", y="Pubblicazioni Giorno",
                       title="Andamento giornaliero",
                       markers=True, color_discrete_sequence=palette_giornaliera)
        fig1.update_layout(dragmode=False, showlegend=False)
        col1.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)
        
        # Grafico 2: Andamento Cumulato (Line Chart)
        fig2 = px.line(cumulative_df, x="data", y="Pubblicazioni Cumulative",
                       title="Andamento cumulato",
                       markers=True, color_discrete_sequence=palette_cumul)
        fig2.update_layout(dragmode=False, showlegend=False)
        col2.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    with tab2:
        col1, col2 = st.columns(2)

        # Grafico per Tipologie (NUMERO SU Y, Tipologie su X)
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            palette_tipologie = sns.color_palette("pastel", len(tipologia_counts)).as_hex()
            fig3 = px.bar(tipologia_counts, x="Tipo Atto", y="Numero di Pubblicazioni",
                          title="Tipologie",
                          color="Tipo Atto", color_discrete_sequence=palette_tipologie)
            fig3.update_layout(dragmode=False, showlegend=False)
            col1.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col1.warning("Dati sulle tipologie non disponibili.")
        
        # Grafico per Mittenti (NUMERO SU Y, Mittenti su X)
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            palette_mittenti = sns.color_palette("pastel", len(mittente_counts)).as_hex()
            fig4 = px.bar(mittente_counts, x="Mittente", y="Numero di Pubblicazioni",
                          title="Mittenti",
                          color="Mittente", color_discrete_sequence=palette_mittenti)
            fig4.update_layout(dragmode=False, showlegend=False)
            col2.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col2.warning("Dati sui mittenti non disponibili.")

    with tab3:

        col1, col2 = st.columns(2)

        # Performance dei ritardi
        publication_delays = analyze_publication_delays(df)
        st.write("Tabella con la distribuzione dei ritardi:")
        st.dataframe(publication_delays, use_container_width=True)
        

        # Performance dei mittenti
        mittente_performance = analyze_mittenti_performance(df)
        st.write("Tabella con i ritardi medi di pubblicazione per mittente:")
        st.dataframe(mittente_performance, use_container_width=True)


