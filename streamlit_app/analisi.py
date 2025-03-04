import streamlit as st
import pandas as pd
import plotly.express as px

# 🎨 Palette Pantone Soft
COLOR_PALETTE = ["#A7C7E7", "#A8E6CF", "#FFAAA5", "#FFD3B6", "#D4A5A5"]

# ⚙️ Configurazione toolbar (Solo Fullscreen e Download)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "pan2d", "select2d", "lasso2d", "resetScale2d",
        "zoomIn2d", "zoomOut2d", "autoScale2d"
    ]
}

def page_analisi(df):
    # Titolo e descrizione
    st.title("📊 Analisi delle Pubblicazioni")
    st.markdown("Questa dashboard mostra l'andamento delle pubblicazioni nel tempo e la distribuzione per tipologia e mittente.")

    # 🗓️ Conversione della data
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)

    # 📆 Numero pubblicazioni per mese
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")
    pub_per_mese["Pubblicazioni Cumulative"] = pub_per_mese["Pubblicazioni Mese"].cumsum()

    # Creazione di due tab per separare le analisi
    tab1, tab2 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti"])

    with tab1:
        st.subheader("Andamento delle Pubblicazioni")
        col1, col2 = st.columns(2)

        # Grafico a barre
        fig_bar = px.bar(
            pub_per_mese, 
            x="Mese", 
            y="Numero",
            title="Numero di pubblicazioni per mese",
            color_discrete_sequence=[COLOR_PALETTE[0]]
        )
        col1.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

        # Grafico cumulativo
        st.subheader("Andamento cumulato delle pubblicazioni")
        fig_line = px.line(
            pub_per_mese, 
            x="Mese", 
            y="Numero",
            title="Numero di pubblicazioni cumulate nel tempo",
            markers=True,
            color_discrete_sequence=[COLOR_PALETTE[2]]
        )
        col2.plotly_chart(fig_line, use_container_width=True, config=PLOTLY_CONFIG)

    with tab2:
        st.subheader("Distribuzione per Tipologia e Mittente")
        col1, col2 = st.columns(2)

        # 🍩 Donut per Tipologie
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipologia", "Numero"]
            fig_pie_tipo = px.pie(
                tipologia_counts, 
                names="Tipo Atto", 
                values="Numero di Pubblicazioni",
                title="Distribuzione per Tipologia",
                hole=0.4,
                color_discrete_sequence=COLOR_PALETTE
            )
            col1.plotly_chart(fig_pie_tipo, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col1.warning("⚠️ Dati sulle tipologie non disponibili.")

        # 🍩 Donut per Mittenti
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero"]
            fig4 = px.pie(mittente_counts, names="Mittente", values="Numero di Pubblicazioni",
                          title="Mittenti",
                          hole=0.4, color_discrete_sequence=COLOR_PALETTE)
            col2.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)  # ✅ Toolbar personalizzata
        else:
            col2.warning("⚠️ Dati sui mittenti non disponibili.")
