import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

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

def page_analisi(df):
    st.header("📊 ANALISI")

    # ----- Preparazione dati per il tab "Andamento Temporale" -----
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()

    # Distribuzione Mensile: raggruppa per mese (formato "YYYY-MM")
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")
    palette_mese = sns.color_palette("pastel", len(pub_per_mese)).as_hex()

    # Distribuzione Giornaliera per l'Andamento Cumulato:
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date
    daily_counts = df_time.groupby("data").size().rename("Pubblicazioni Giorno")
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
    daily_cumsum = daily_counts.cumsum()
    cumulative_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values,
        "Pubblicazioni Cumulative": daily_cumsum.values
    })
    palette_cumul = sns.color_palette("pastel", 1).as_hex()

    # ----- Layout dei grafici -----
    tab1, tab2 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti"])

    with tab1:
        col1, col2 = st.columns(2)
        
        # Grafico 1: Andamento mensile (Line Chart non cumulativo)
        fig1 = px.line(pub_per_mese, x="mese", y="Pubblicazioni Mese",
                       title="Andamento mensile",
                       markers=True, color_discrete_sequence=palette_mese)
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
