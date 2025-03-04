import streamlit as st
import pandas as pd
import plotly.express as px

# 🎨 Palette Pantone Soft
COLOR_PALETTE = ["#A7C7E7", "#A8E6CF", "#FFAAA5", "#FFD3B6", "#D4A5A5"]

def page_analisi(df):
    st.header("📊 ANALISI")

    # 🗓️ Conversione della data
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)

    # 📆 Numero pubblicazioni per mese
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")
    pub_per_mese["Pubblicazioni Cumulative"] = pub_per_mese["Pubblicazioni Mese"].cumsum()

    # 📊 Creazione tab
    tab1, tab2 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti"])

    with tab1:
        st.subheader("📆 Pubblicazioni per Mese")
        fig1 = px.bar(pub_per_mese, x="mese", y="Pubblicazioni Mese",
                      title="Pubblicazioni Mensili",
                      color_discrete_sequence=[COLOR_PALETTE[0]])  # 🎨 Usa il blu tenue
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📈 Funzione Cumulata delle Pubblicazioni")
        fig2 = px.line(pub_per_mese, x="mese", y="Pubblicazioni Cumulative",
                       title="Andamento Cumulato",
                       markers=True, color_discrete_sequence=[COLOR_PALETTE[2]])  # 🎨 Pesca chiaro
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("📋 Distribuzione delle Pubblicazioni per Tipologia e Mittente")

        col1, col2 = st.columns(2)

        # 🍩 Donut per Tipologie
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            fig3 = px.pie(tipologia_counts, names="Tipo Atto", values="Numero di Pubblicazioni",
                          title="Tipologie di Atto",
                          hole=0.4, color_discrete_sequence=COLOR_PALETTE)  # 🎨 Colori Pantone Soft
            col1.plotly_chart(fig3, use_container_width=True)
        else:
            col1.warning("⚠️ Dati sulle tipologie non disponibili.")

        # 🍩 Donut per Mittenti
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            fig4 = px.pie(mittente_counts, names="Mittente", values="Numero di Pubblicazioni",
                          title="Mittenti",
                          hole=0.4, color_discrete_sequence=COLOR_PALETTE)  # 🎨 Colori Pantone Soft
            col2.plotly_chart(fig4, use_container_width=True)
        else:
            col2.warning("⚠️ Dati sui mittenti non disponibili.")
