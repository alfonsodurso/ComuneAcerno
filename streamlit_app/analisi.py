import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
from datetime import timedelta

# ⚙️ Configurazione per Plotly
PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,  # 🔹 Zoom con due dita su mobile
    "modeBarButtonsToRemove": [
        "pan2d", "select2d", "lasso2d", "zoom",
        "resetScale2d", "toggleSpikelines"
    ],
    "displayModeBar": "hover",
}

# ---------------------- FUNZIONI DI UTILITÀ ----------------------

def calculate_working_days(start_date, end_date):
    """
    Calcola il numero di giorni lavorativi (lun-ven) tra due date,
    includendo entrambe le estremità e sottraendo 1 (per non contare il giorno di partenza).
    """
    start = np.datetime64(start_date.date()) if isinstance(start_date, pd.Timestamp) else np.datetime64(start_date)
    end = np.datetime64(end_date.date()) if isinstance(end_date, pd.Timestamp) else np.datetime64(end_date)
    # np.busday_count conta i giorni lavorativi escludendo il giorno finale: per includerlo aggiungiamo 1 giorno e poi sottraiamo 1
    days = np.busday_count(start, end + np.timedelta64(1, 'D')) - 1
    return max(days, 0)
    

def analyze_publication_delays(df):
    """
    Calcola il ritardo di pubblicazione in giorni lavorativi tra 'data_registro_generale'
    e 'data_inizio_pubblicazione', escludendo le pubblicazioni senza 'data_registro_generale'.
    Restituisce un DataFrame con i ritardi calcolati e uno con le pubblicazioni escluse.
    """
    # Pulizia: convertiamo stringhe vuote in NaN per facilitare il parsing delle date
    df["data_registro_generale"] = df["data_registro_generale"].replace("", np.nan)
    df["data_inizio_pubblicazione"] = df["data_inizio_pubblicazione"].replace("", np.nan)

    # Separiamo le pubblicazioni senza "data_registro_generale"
    df_missing = df[df["data_registro_generale"].isna()][
        ["numero_pubblicazione", "mittente", "oggetto_atto", "data_inizio_pubblicazione"]
    ]
    
    # Filtriamo solo le righe con entrambe le date presenti
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    
    # Conversione in datetime con gestione degli errori
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    
    # Rimuoviamo eventuali righe dove la conversione ha fallito (date ancora NaT)
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    
    # Conversione a datetime64[D] per compatibilità con np.busday_count
    start_dates = df["data_registro_generale"].values.astype("datetime64[D]")
    end_dates = df["data_inizio_pubblicazione"].values.astype("datetime64[D]")
    
    # Calcolo del ritardo in giorni lavorativi:
    # np.busday_count conta esclusivamente il giorno finale; per includerlo aggiungiamo 1 giorno e poi sottraiamo 1
    df["ritardo_pubblicazione"] = np.busday_count(start_dates, end_dates + np.timedelta64(1, "D")) - 1
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].clip(lower=0)
    
    return df, df_missing

def analyze_mittenti_performance(df):
    """
    Analizza il ritardo medio di pubblicazione per ogni mittente.
    Restituisce un DataFrame con il mittente e il ritardo medio ordinato in modo decrescente.
    (Questa funzione viene ora sostituita dall'aggregazione presente in display_ritardi_tab.)
    """
    performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    performance.columns = ["Mittente", "Ritardo medio"]
    performance = performance.sort_values(by="Ritardo medio", ascending=False)
    return performance

# ---------------------- FUNZIONI DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data(df):
    """
    Prepara i dati temporali per il calcolo dei grafici:
    - Andamento giornaliero
    - Andamento cumulato
    """
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    df_time = df.dropna(subset=["data_inizio_pubblicazione"]).copy()
    
    # Creazione della colonna 'data'
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date
    
    # Raggruppamento per giorno
    daily_counts = df_time.groupby("data").size().rename("Pubblicazioni Giorno")
    full_date_range = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
    
    daily_counts_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values
    })
    
    # Calcolo del cumulativo
    daily_cumsum = daily_counts.cumsum()
    cumulative_df = pd.DataFrame({
        "data": daily_counts.index.date,
        "Pubblicazioni Giorno": daily_counts.values,
        "Pubblicazioni Cumulative": daily_cumsum.values
    })
    
    return daily_counts_df, cumulative_df

# ---------------------- FUNZIONI DI VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, daily_counts_df, cumulative_df):
    """
    Visualizza i grafici relativi all'andamento temporale:
    - Pubblicazioni giornaliere
    - Pubblicazioni cumulative
    """
    palette = sns.color_palette("pastel", 1).as_hex()
    
    col1, col2 = container.columns(2)
    
    # Grafico giornaliero
    fig_daily = px.line(
        daily_counts_df, x="data", y="Pubblicazioni Giorno",
        title="Andamento giornaliero",
        markers=True, color_discrete_sequence=palette
    )
    fig_daily.update_layout(dragmode=False, showlegend=False)
    col1.plotly_chart(fig_daily, use_container_width=True, config=PLOTLY_CONFIG)
    
    # Grafico cumulativo
    fig_cumulative = px.line(
        cumulative_df, x="data", y="Pubblicazioni Cumulative",
        title="Andamento cumulato",
        markers=True, color_discrete_sequence=palette
    )
    fig_cumulative.update_layout(dragmode=False, showlegend=False)
    col2.plotly_chart(fig_cumulative, use_container_width=True, config=PLOTLY_CONFIG)


def display_tipologie_mittenti_tab(container, df):
    """
    Visualizza i grafici a barre per:
    - Tipologie (se la colonna 'tipo_atto' è presente)
    - Mittenti (se la colonna 'mittente' è presente)
    """
    col1, col2 = container.columns(2)
    
    # Grafico Tipologie
    if "tipo_atto" in df.columns:
        tipologia_counts = df["tipo_atto"].value_counts().reset_index()
        tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
        palette = sns.color_palette("pastel", len(tipologia_counts)).as_hex()
        fig_tipologie = px.bar(
            tipologia_counts, x="Tipo Atto", y="Numero di Pubblicazioni",
            title="Tipologie", color="Tipo Atto", color_discrete_sequence=palette
        )
        fig_tipologie.update_layout(dragmode=False, showlegend=False)
        col1.plotly_chart(fig_tipologie, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        col1.warning("Dati sulle tipologie non disponibili.")
    
    # Grafico Mittenti
    if "mittente" in df.columns:
        mittente_counts = df["mittente"].value_counts().reset_index()
        mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
        
        # Troncamento dei nomi troppo lunghi
        mittente_counts["Mittente"] = mittente_counts["Mittente"].apply(lambda x: x[:15] + "…" if len(x) > 20 else x)
        
        palette = sns.color_palette("pastel", len(mittente_counts)).as_hex()
        fig_mittenti = px.bar(
            mittente_counts, x="Mittente", y="Numero di Pubblicazioni",
            title="Mittenti", color="Mittente", color_discrete_sequence=palette
        )
        fig_mittenti.update_layout(dragmode=False, showlegend=False)
        col2.plotly_chart(fig_mittenti, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        col2.warning("Dati sui mittenti non disponibili.")

def display_ritardi_tab(container, df):
    """
    Calcola e visualizza la tabella con i ritardi medi di pubblicazione per mittente,
    includendo una tabella separata delle pubblicazioni escluse.
    """
    df_delays, df_missing = analyze_publication_delays(df)
    
    # Se non esiste una colonna che identifica univocamente la pubblicazione, usiamo l'indice
    if "numero_pubblicazione" not in df_delays.columns:
        df_delays = df_delays.reset_index().rename(columns={"index": "numero_pubblicazione"})
    
    # Aggregazione per mittente:
    aggregated = df_delays.groupby("mittente").agg(
         ritardo_medio=('ritardo_pubblicazione', 'mean'),
         numero_pubblicazioni_totali=('ritardo_pubblicazione', 'count'),
         ritardo_massimo=('ritardo_pubblicazione', 'max')
    ).reset_index()
    
    # Per ogni mittente, individuiamo il record con il ritardo massimo e ne estraiamo il numero della pubblicazione
    max_idx = df_delays.groupby("mittente")["ritardo_pubblicazione"].idxmax()
    max_publications = df_delays.loc[max_idx, ["mittente", "numero_pubblicazione"]].rename(
         columns={"numero_pubblicazione": "pub_max_ritardo"}
    )
    
    performance = aggregated.merge(max_publications, on="mittente", how="left")
    performance["ritardo_medio"] = performance["ritardo_medio"].round(0).astype(int)

    performance = performance.sort_values("ritardo_medio", ascending=False)
    
    # Rinominiamo le colonne per maggiore chiarezza
    performance = performance.rename(columns={
         "mittente": "Mittente",
         "ritardo_medio": "Ritardo medio",
         "ritardo_massimo": "Ritardo massimo",
         "numero_pubblicazioni_totali": "Pubblicazioni totali",
         "pub_max_ritardo": "Pubblicazione max ritardo"
    })
    
    # Mostriamo la tabella dei ritardi medi
    st.markdown("**Analisi dei ritardi per mittente**")
    #container.write("# Analisi dei ritardi per mittente:")
    container.dataframe(performance, use_container_width=True)
    
     # Visualizziamo la tabella delle pubblicazioni escluse
    if not df_missing.empty:
        st.markdown("**Pubblicazioni senza la data registro**")

        # container.write("# Pubblicazioni senza la data registro:")
        df_missing_copy = df_missing.copy()
        df_missing_copy = df_missing_copy.rename(columns={
            "numero_pubblicazione": "Numero",
            "mittente": "Mittente",
            "oggetto_atto": "Oggetto",
            "data_inizio_pubblicazione": "Data Pubblicazione"
        })
        # Formatto la colonna Data Pubblicazione nel formato gg-mm-aaaa
        df_missing_copy["Data Pubblicazione"] = pd.to_datetime(
            df_missing_copy["Data Pubblicazione"], errors="coerce"
        ).dt.strftime("%d-%m-%Y")
        
        container.dataframe(df_missing_copy, use_container_width=True)

# ---------------------- FUNZIONE PRINCIPALE ----------------------

def page_analisi(df):
    st.header("📊 ANALISI")
    
    # Preparazione dati per i grafici temporali
    daily_counts_df, cumulative_df = prepare_time_series_data(df)
    
    # Creazione dei tab
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])
    
    with tab_temporale:
        display_temporal_tab(tab_temporale, daily_counts_df, cumulative_df)
    
    with tab_tipologie:
        display_tipologie_mittenti_tab(tab_tipologie, df)
    
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)
