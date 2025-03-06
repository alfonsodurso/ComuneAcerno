import streamlit as st
import pandas as pd
import plotly.express as px

# 🎨 Palette colori Pantone Soft
COLOR_PALETTE = ["#A7C7E7", "#A8E6CF", "#FFAAA5", "#FFD3B6", "#D4A5A5"]

# ⚙️ Configurazione toolbar (Zoom con due dita, Pan disattivato)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,  # 🔹 Zoom con due dita su mobile
    "modeBarButtonsToRemove": [
        "pan2d", "select2d", "lasso2d", "autoScale2d", "resetScale2d", "toggleSpikelines"
    ],
    "displayModeBar": True
}

def page_analisi(df):
    st.header("📊 ANALISI")

    # **Conversione della data**
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()

    # **Distribuzione Mensile**
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")

    # **Distribuzione Giornaliera per l'Andamento Cumulato**
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date
    df_time = df_time.groupby("data").size().reset_index(name="Pubblicazioni Giorno")

    # **Generiamo un intervallo continuo di date**
    min_date, max_date = df_time["data"].min(), df_time["data"].max()
    all_dates = pd.DataFrame(pd.date_range(min_date, max_date), columns=["data"])

    # **Convertiamo entrambe in datetime64 per evitare errori**
    all_dates["data"] = all_dates["data"].dt.date
    df_time["data"] = pd.to_datetime(df_time["data"]).dt.date

    # **Unione per ottenere una serie temporale completa**
    df_time = all_dates.merge(df_time, on="data", how="left").fillna(0)

    # **Calcolo della funzione cumulata**
    df_time["Pubblicazioni Cumulative"] = df_time["Pubblicazioni Giorno"].cumsum()

    tab1, tab2 = st.tabs(["📆 Andamento Temporale", "📋 Tipologie & Mittenti"])

    with tab1:
        st.subheader("📆 Distribuzione e andamento")

        col1, col2 = st.columns(2)

        # **Grafico Distribuzione Mensile**
        fig1 = px.bar(pub_per_mese, x="mese", y="Pubblicazioni Mese",
                      title="Distribuzione mensile delle pubblicazioni",
                      color_discrete_sequence=[COLOR_PALETTE[0]])
        col1.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

        # **Grafico Andamento Cumulato Giornaliero**
        fig2 = px.line(df_time, x="data", y="Pubblicazioni Cumulative",
                       title="Andamento cumulato delle pubblicazioni",
                       markers=True, color_discrete_sequence=[COLOR_PALETTE[2]])
        col2.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    with tab2:
        st.subheader("📋 Distribuzione per Tipologia e Mittente")

        col1, col2 = st.columns(2)

        # 🍩 **Donut per Tipologie**
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            fig3 = px.pie(tipologia_counts, names="Tipo Atto", values="Numero di Pubblicazioni",
                          title="Tipologie di Atto", hole=0.4, height=350,
                          color_discrete_sequence=COLOR_PALETTE)
            fig3.update_layout(legend=dict(orientation="h", y=-0.2, font=dict(size=10)))  # 🔹 Legenda in basso
            col1.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col1.warning("⚠️ Dati sulle tipologie non disponibili.")

        # 🍩 **Donut per Mittenti**
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            fig4 = px.pie(mittente_counts, names="Mittente", values="Numero di Pubblicazioni",
                          title="Mittenti", hole=0.4, height=350,
                          color_discrete_sequence=COLOR_PALETTE)
            fig4.update_layout(legend=dict(orientation="h", y=-0.2, font=dict(size=10)))  # 🔹 Legenda in basso
            col2.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            col2.warning("⚠️ Dati sui mittenti non disponibili.")
