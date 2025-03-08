import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
from datetime import datetime, timedelta
from bertopic import BERTopic

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

"""
RITARDI
"""

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
    # Assuming this function calculates the 'ritardo_pubblicazione' column
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df["ritardo_pubblicazione"] = df.apply(
        lambda row: calculate_working_days(row["data_registro_generale"], row["data_inizio_pubblicazione"]) - 1,
        axis=1
    )
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].apply(lambda x: max(x, 0))
    return df


def analyze_mittenti_performance(df):
    """Analizza il ritardo medio di pubblicazione per ogni mittente."""
    mittente_performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    mittente_performance.columns = ["Mittente", "Ritardo medio"]
    mittente_performance = mittente_performance.sort_values(by="Ritardo medio", ascending=False)
    return mittente_performance

"""
TOPIC
"""

def perform_topic_modeling(texts):
    """
    Perform topic modeling on a list of publication subjects using BERTopic.
    Returns the BERTopic model, the topic assignments, and topic probabilities.
    """
    # Create a BERTopic instance. The parameter 'language="italian"' helps to use language-specific stopwords.
    topic_model = BERTopic(language="italian")
    topics, probs = topic_model.fit_transform(texts)
    return topic_model, topics, probs

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
    tab1, tab2, tab3, tab4 = st.tabs(["📆 Andamento Temporale", 
                                      "📋 Tipologie & Mittenti", 
                                      "⏳ Ritardi",
                                     "Topic"])

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
        
        # Calcola i ritardi di pubblicazione e aggiorna il DataFrame
        df = analyze_publication_delays(df)
    
   
    
        # Analizza la performance dei mittenti
        mittente_performance = analyze_mittenti_performance(df)
        
        # Arrotonda i giorni di ritardo medi e converti in intero (senza decimali)
        mittente_performance["Ritardo medio"] = mittente_performance["Ritardo medio"].round(0).astype(int)
        
        st.write("Tabella con i ritardi medi di pubblicazione per mittente:")
        st.dataframe(mittente_performance, use_container_width=True)

    with tab4:
        
        # Extract publication subjects
        texts = df["oggetto_atto"].tolist()
        
        st.write("Performing semantic topic modeling on publication subjects. Please wait...")
        # Perform topic modeling using BERTopic
        topic_model, topics, probs = perform_topic_modeling(texts)
        
        # Add the identified topics to the DataFrame
        df["topic"] = topics
        
        # Compute the number of publications per topic
        topic_counts = df["topic"].value_counts().reset_index()
        topic_counts.columns = ["Topic", "Count"]
        
        st.subheader("Topic Distribution")
        st.write("The table below shows how many publications belong to each identified topic:")
        st.dataframe(topic_counts)
        
        # Plot the topic distribution using a bar chart
        fig1 = px.bar(topic_counts, x="Topic", y="Count",
                      title="Number of Publications per Topic",
                      labels={"Topic": "Topic ID", "Count": "Publications"})
        st.plotly_chart(fig1)
        
        # Create a 'month' column from the publication date
        df["month"] = df["data_inizio_pubblicazione"].dt.to_period("M").astype(str)
        
        # Group by month and topic to count publications over time
        time_topic = df.groupby(["month", "topic"]).size().reset_index(name="Count")
        
        # For the time trend graph, select only the main topics (for example, topics with at least 5 publications)
        main_topics = topic_counts[topic_counts["Count"] >= 5]["Topic"].tolist()
        filtered_time_topic = time_topic[time_topic["topic"].isin(main_topics)]
        
        st.subheader("Time Trend of Main Topics")
        st.write("The following line chart shows the monthly trend of the main topics.")
        fig2 = px.line(filtered_time_topic, x="month", y="Count", color="topic",
                       title="Monthly Time Trend of Main Topics",
                       labels={"month": "Month", "Count": "Number of Publications", "topic": "Topic ID"})
        st.plotly_chart(fig2)
    
