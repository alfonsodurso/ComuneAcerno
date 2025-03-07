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
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()

    # Distribuzione Mensile: raggruppa per mese (formato "YYYY-MM")
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")
    palette_mese = sns.color_palette("pastel", len(pub_per_mese)).as_hex()

    # ----- Analisi Ritardi -----
    df = analyze_publication_delays(df)

    # ----- Layout dei grafici -----
    tab1, tab2, tab3 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti", "⏳ Ritardi"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # Grafico 1: Distribuzione Mensile (Bar Chart)
        fig1 = px.bar(pub_per_mese, x="mese", y="Pubblicazioni Mese",
                      title="Distribuzione mensile delle pubblicazioni",
                      color_discrete_sequence=palette_mese)
        fig1.update_layout(dragmode=False, showlegend=False)
        col1.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

    with tab2:
        col1, col2 = st.columns(2)

        # Grafico per Tipologie
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            palette_tipologie = sns.color_palette("pastel", len(tipologia_counts)).as_hex()
            fig3 = px.bar(tipologia_counts, x="Numero di Pubblicazioni", y="Tipo Atto",
                          title="Tipologie di Atto",
                          orientation="h",
                          color="Tipo Atto", color_discrete_sequence=palette_tipologie)
            fig3.update_layout(showlegend=False)
            col1.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)

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

        # Performance dei ritardi
        publication_delays = analyze_publication_delays(df)
        st.write("Tabella con la distribuzione dei ritardi:")
        st.dataframe(publication_delays, use_container_width=True)
        

        # Performance dei mittenti
        mittente_performance = analyze_mittenti_performance(df)
        st.write("Tabella con i ritardi medi di pubblicazione per mittente:")
        st.dataframe(mittente_performance, use_container_width=True)


