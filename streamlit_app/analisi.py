import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

# ⚙️ Configurazione toolbar (Zoom con due dita, Pan disattivato)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,  # Zoom con due dita su mobile
    "modeBarButtonsToRemove": [
        "pan2d", "select2d", "lasso2d", "autoScale2d",
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
    # Genera una palette dinamica per il grafico mensile in base al numero di mesi
    palette_mese = sns.color_palette("pastel", len(pub_per_mese)).as_hex()

    # Distribuzione Giornaliera per l'Andamento Cumulato:
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date
    daily_counts = df_time.groupby("data").size().rename("Pubblicazioni Giorno")
    # Generiamo un intervallo continuo di date
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
    daily_cumsum = daily_counts.cumsum()
    cumulative_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values,
        "Pubblicazioni Cumulative": daily_cumsum.values
    })
    # Palette dinamica per il grafico cumulato (1 sola linea)
    palette_cumul = sns.color_palette("pastel", 1).as_hex()

    # ----- Layout dei grafici -----
    tab1, tab2 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti"])

    with tab1:
        # Suddividiamo in due colonne per i grafici
        col1, col2 = st.columns(2)
        
        # Grafico 1: Distribuzione Mensile (Bar Chart)
        fig1 = px.bar(pub_per_mese, x="mese", y="Pubblicazioni Mese",
                      title="Distribuzione mensile delle pubblicazioni",
                      color_discrete_sequence=palette_mese)
        # Disattiviamo il pan (modalità interazione lasciata a due dita per lo zoom)
        fig1.update_layout(dragmode=False, showlegend=False)
        col1.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)
        
        # Grafico 2: Andamento Cumulato (Line Chart)
        fig2 = px.line(cumulative_df, x="data", y="Pubblicazioni Cumulative",
                       title="Andamento cumulato delle pubblicazioni",
                       markers=True, color_discrete_sequence=palette_cumul)
        fig2.update_layout(dragmode=False, showlegend=False)
        col2.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    with tab2:
        st.subheader("Distribuzione per Tipologia e Mittente")
        col1, col2 = st.columns(2)

        # Grafico per Tipologie
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            # Genera una palette dinamica in base al numero di tipologie
            palette_tipologie = sns.color_palette("pastel", len(tipologia_counts)).as_hex()
            fig3 = px.bar(tipologia_counts, x="Numero di Pubblicazioni", y="Tipo Atto",
                          orientation="h",
                          color="Tipo Atto", color_discrete_sequence=palette_tipologie,
                          title="Tipologie di Atto")
            fig3.update_layout(showlegend=False)
            col1.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col1.warning("Dati sulle tipologie non disponibili.")

        # Grafico per Mittenti
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            palette_mittenti = sns.color_palette("pastel", len(mittente_counts)).as_hex()
            fig4 = px.bar(mittente_counts, x="Numero di Pubblicazioni", y="Mittente",
                          orientation="h",
                          color="Mittente", color_discrete_sequence=palette_mittenti,
                          title="Mittenti")
            fig4.update_layout(showlegend=False)
            col2.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col2.warning("Dati sui mittenti non disponibili.")
