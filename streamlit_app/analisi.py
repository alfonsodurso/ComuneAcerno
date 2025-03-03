import streamlit as st
import pandas as pd
import plotly.express as px

def page_analisi(df):
    st.header("📊 ANALISI")
    st.markdown("Dashboard interattiva per analizzare l'andamento delle pubblicazioni.")

    if "data_inizio_pubblicazione" not in df.columns:
        st.error("⚠️ Errore: La colonna 'data_inizio_pubblicazione' non è presente nel database.")
        return
    
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()

    # Raggruppamento per mese
    df_time["mese"] = df_time["data_inizio_pubblicazione"].dt.to_period("M").astype(str)  # YYYY-MM

    # Conta il numero di pubblicazioni per ogni mese
    pub_per_mese = df_time.groupby("mese").size().reset_index(name="Pubblicazioni Mese")

    tab1, tab2, tab3 = st.tabs(["📆 Andamento Mensile", "📊 Tipologie", "🏢 Mittenti"])
    
    with tab1:
        st.subheader("📆 Pubblicazioni per Mese")
        fig1 = px.bar(pub_per_mese, x="mese", y="Pubblicazioni Mese", title="Pubblicazioni Mensili")
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        if "tipo_atto" in df.columns:
            tipologia_counts = df["tipo_atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
            fig2 = px.bar(tipologia_counts, x="Tipo Atto", y="Numero di Pubblicazioni", title="Distribuzione delle Tipologie di Atto")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'tipo_atto' non è presente nei dati.")

    with tab3:
        if "mittente" in df.columns:
            mittente_counts = df["mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
            fig3 = px.bar(mittente_counts, x="Mittente", y="Numero di Pubblicazioni", title="Chi Pubblica Maggiormente")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'mittente' non è presente nei dati.")
