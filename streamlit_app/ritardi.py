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
        "pan2d", "select2d", "lasso2d", "autoScale2d",
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
    mittente_performance.columns = ["Mittente", "Ritardo Medio (giorni lavorativi)"]
    mittente_performance = mittente_performance.sort_values(by="Ritardo Medio (giorni lavorativi)", ascending=False)
    return mittente_performance

def page_ritardi(df):
    st.header("⏳ ANALISI RITARDI PUBBLICAZIONE")

    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")

    # Calcola i ritardi
    df = analyze_publication_delays(df)

    # **Istogramma dei ritardi**
    st.subheader("📊 Distribuzione dei Ritardi di Pubblicazione")
    fig1 = px.histogram(df, x="ritardo_pubblicazione", nbins=15,
                        title="Distribuzione dei Ritardi (Giorni Lavorativi)",
                        labels={"ritardo_pubblicazione": "Ritardo (Giorni Lavorativi)", "count": "Numero di Pubblicazioni"})
    st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

    # **Performance dei mittenti**
    mittente_performance = analyze_mittenti_performance(df)
    
    st.subheader("📌 Performance dei Mittenti (Ritardo Medio)")
    st.write("Tabella con i ritardi medi di pubblicazione per mittente:")
    st.dataframe(mittente_performance, use_container_width=True)

    # **Grafico ritardi per mittente**
    fig2 = px.bar(mittente_performance, x="Ritardo Medio (giorni lavorativi)", y="Mittente",
                  orientation="h", title="Ritardo Medio per Mittente",
                  labels={"Ritardo Medio (giorni lavorativi)": "Ritardo Medio (Giorni Lavorativi)", "Mittente": "Mittente"},
                  color="Mittente", color_discrete_sequence=sns.color_palette("pastel", len(mittente_performance)).as_hex())
    st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)
