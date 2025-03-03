import streamlit as st
import pandas as pd
import plotly.express as px

def page_analisi(df):
    st.header("ANALISI")
    st.markdown("Dashboard interattiva per analizzare l'andamento delle pubblicazioni.")

    tab1, tab2, tab3, tab4 = st.tabs(["Andamento Temporale", "Tipologie", "Mittenti", "Giorni"])
    
    with tab1:
        if "Data Inizio Pubblicazione" in df.columns:
            df_time = df.dropna(subset=["Data Inizio Pubblicazione"]).copy()
            df_time["Giorno"] = df_time["Data Inizio Pubblicazione"].dt.date
            pub_per_giorno = df_time.groupby("Giorno").size().reset_index(name="Numero Pubblicazioni")
            fig1 = px.line(pub_per_giorno, x="Giorno", y="Numero Pubblicazioni", title="Andamento Temporale")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.write("Dati temporali non disponibili.")
    
    with tab2:
        if "Tipo Atto" in df.columns:
            tipologia_counts = df["Tipo Atto"].value_counts().reset_index()
            tipologia_counts.columns = ["Tipo Atto", "Conteggio"]
            fig2 = px.bar(tipologia_counts, x="Tipo Atto", y="Conteggio", title="Tipologie di Atto")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write("Dati sulle tipologie non disponibili.")
    
    with tab3:
        if "Mittente" in df.columns:
            mittente_counts = df["Mittente"].value_counts().reset_index()
            mittente_counts.columns = ["Mittente", "Conteggio"]
            fig3 = px.bar(mittente_counts, x="Mittente", y="Conteggio", title="Principali Mittenti")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.write("Dati sui mittenti non disponibili.")
    
    with tab4:
        if "Data Inizio Pubblicazione" in df.columns:
            df_time = df.dropna(subset=["Data Inizio Pubblicazione"]).copy()
            df_time["GiornoSettimana"] = df_time["Data Inizio Pubblicazione"].dt.day_name()
            giorno_counts = df_time["GiornoSettimana"].value_counts().reset_index()
            giorno_counts.columns = ["Giorno della settimana", "Conteggio"]
            fig4 = px.bar(giorno_counts, x="Giorno della settimana", y="Conteggio", title="Distribuzione per Giorno")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.write("Dati temporali non disponibili.")
