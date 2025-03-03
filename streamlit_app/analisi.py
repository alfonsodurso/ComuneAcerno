import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Imposta il locale italiano per i giorni della settimana
try:
    locale.setlocale(locale.LC_TIME, "it_IT.utf8")
except locale.Error:
    st.warning("⚠️ Attenzione: Impossibile impostare il locale italiano. Il formato potrebbe non essere corretto.")

def page_analisi(df):
    st.header("📊 ANALISI")
    st.markdown("Dashboard interattiva per analizzare l'andamento delle pubblicazioni.")

    # Controlla se esiste la colonna "data_inizio_pubblicazione"
    if "data_inizio_pubblicazione" not in df.columns:
        st.error("⚠️ Errore: La colonna 'data_inizio_pubblicazione' non è presente nel database.")
        return
    
    # Conversione in datetime se non lo è già
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")

    # Creazione del DataFrame per l'andamento temporale
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()
    df_time["giorno"] = df_time["data_inizio_pubblicazione"].dt.date

    # Conta il numero di pubblicazioni per ogni giorno
    pub_per_giorno = df_time.groupby("giorno").size().reset_index(name="Pubblicazioni Giorno")
    
    # Calcola il numero cumulativo di pubblicazioni nel tempo
    pub_per_giorno["Pubblicazioni Cumulative"] = pub_per_giorno["Pubblicazioni Giorno"].cumsum()

    # Creazione del DataFrame per i giorni della settimana (tradotti in italiano)
    df_time["giorno_settimana"] = df_time["data_inizio_pubblicazione"].dt.strftime("%A")  # Giorni in italiano
    giorno_counts = df_time["giorno_settimana"].value_counts().reset_index()
    giorno_counts.columns = ["Giorno della settimana", "Numero di Pubblicazioni"]

    # Creazione dei grafici
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Andamento Temporale", "📊 Tipologie", "🏢 Mittenti", "📆 Giorni della Settimana"])
    
    with tab1:
        st.subheader("📅 Pubblicazioni per Giorno")
        fig1 = px.bar(pub_per_giorno, x="giorno", y="Pubblicazioni Giorno", title="Pubblicazioni Effettive per Giorno")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📈 Pubblicazioni Cumulative nel Tempo")
        fig2 = px.line(pub_per_giorno, x="giorno", y="Pubblicazioni Cumulative", title="Pubblicazioni Cumulative")
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            fig3 = px.bar(tipologia_counts, x="Tipo Atto", y="Numero di Pubblicazioni", title="Distribuzione delle Tipologie di Atto")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'tipo_atto' non è presente nei dati.")

    with tab3:
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            fig4 = px.bar(mittente_counts, x="Mittente", y="Numero di Pubblicazioni", title="Chi Pubblica Maggiormente")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'mittente' non è presente nei dati.")

    with tab4:
        fig5 = px.bar(giorno_counts, x="Giorno della settimana", y="Numero di Pubblicazioni", title="Distribuzione delle Pubblicazioni per Giorno della Settimana")
        st.plotly_chart(fig5, use_container_width=True)
