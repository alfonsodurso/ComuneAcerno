import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
from datetime import timedelta
from streamlit_echarts import st_echarts


# ⚙️ Configurazione per Plotly (per i tab non modificati)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "scrollZoom": True,
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
    days = np.busday_count(start, end + np.timedelta64(1, 'D')) - 1
    return max(days, 0)
    

def analyze_publication_delays(df):
    """
    Calcola il ritardo di pubblicazione in giorni lavorativi tra 'data_registro_generale'
    e 'data_inizio_pubblicazione', escludendo le pubblicazioni senza 'data_registro_generale'.
    Restituisce un DataFrame con i ritardi calcolati e uno con le pubblicazioni escluse.
    """
    df["data_registro_generale"] = df["data_registro_generale"].replace("", np.nan)
    df["data_inizio_pubblicazione"] = df["data_inizio_pubblicazione"].replace("", np.nan)

    df_missing = df[df["data_registro_generale"].isna()][
        ["numero_pubblicazione", "mittente", "oggetto_atto", "data_inizio_pubblicazione"]
    ]
    
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    
    df["data_registro_generale"] = pd.to_datetime(df["data_registro_generale"], errors="coerce")
    df["data_inizio_pubblicazione"] = pd.to_datetime(df["data_inizio_pubblicazione"], errors="coerce")
    
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"]).copy()
    
    start_dates = df["data_registro_generale"].values.astype("datetime64[D]")
    end_dates = df["data_inizio_pubblicazione"].values.astype("datetime64[D]")
    
    df["ritardo_pubblicazione"] = np.busday_count(start_dates, end_dates + np.timedelta64(1, "D")) - 1
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].clip(lower=0)
    
    return df, df_missing

def analyze_mittenti_performance(df):
    performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    performance.columns = ["Mittente", "Ritardo medio"]
    performance = performance.sort_values(by="Ritardo medio", ascending=False)
    return performance

# ---------------------- FUNZIONI DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data_by_sender(df):
    """
    Prepara due dataset (giornaliero e cumulato) raggruppati per data e mittente.
    Restituisce:
      - daily_dataset: DataFrame con le pubblicazioni giornaliere (con colonna 'TOTAL' e una colonna per ogni mittente)
      - cumulative_dataset: DataFrame con le versioni cumulative dei dati
      - senders: lista dei mittenti (escluso il totale)
    """
    df_time = df.copy()
    df_time["data_inizio_pubblicazione"] = pd.to_datetime(df_time["data_inizio_pubblicazione"], errors="coerce")
    df_time = df_time.dropna(subset=["data_inizio_pubblicazione"]).copy()
    df_time["data"] = df_time["data_inizio_pubblicazione"].dt.date

    # Raggruppamento per data e mittente
    pivot = df_time.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0)
    pivot = pivot.sort_index()
    # Calcola il totale per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    # Riordina le colonne: mettiamo il totale come prima colonna
    senders = sorted([col for col in pivot.columns if col != "TOTAL"])
    pivot = pivot[["TOTAL"] + senders]
    # Resetta l'indice per avere la colonna data
    daily_dataset = pivot.reset_index()

    # Prepara il dataset cumulato
    cumulative_dataset = daily_dataset.copy()
    for col in cumulative_dataset.columns:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    # Formatta la colonna data come stringa (per visualizzazione su asse x)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    cumulative_dataset["data"] = cumulative_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    
    return daily_dataset, cumulative_dataset, senders

# ---------------------- FUNZIONI DI VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, df):
    """
    Visualizza due grafici (giornaliero e cumulato) che mostrano l'andamento
    totale e per ciascun mittente, utilizzando echarts. I mittenti non attivi di default
    vengono raggruppati sotto la dicitura 'Altri'.

    Le modifiche ai nomi delle colonne sono applicate solo a livello di visualizzazione.
    """
    # Prepara i dataset aggregati per data e mittente
    daily_dataset, cumulative_dataset, senders = prepare_time_series_data_by_sender(df)
    
    # Definisci i mittenti da attivare di default (in formato "display")
    default_active_senders = {
        "Area tecnica 1",
        "Area tecnica 2",
        "Area vigilanza",
        "Area amministrativa",
        "Comune di acerno"
    }
    # Normalizziamo in title-case (il formato visualizzato)
    default_active_senders_display = {s.title() for s in default_active_senders}
    
    # Crea una mappa per la visualizzazione:
    # - "data" resta invariato
    # - "TOTAL" viene visualizzato come "TOTALE"
    # - Tutti gli altri mittenti sono convertiti in title-case
    display_map = {}
    for col in daily_dataset.columns:
        if col == "data":
            display_map[col] = col
        elif col == "TOTAL":
            display_map[col] = "TOTALE"
        else:
            display_map[col] = col.title()

    # Determina i mittenti attivi e inattivi usando i nomi originali e la mappa di visualizzazione.
    # Escludiamo "TOTAL" dal confronto.
    active_senders_original = {s for s in senders if display_map[s] in default_active_senders_display}
    inactive_senders_original = {s for s in senders if s not in active_senders_original}
    
    # Aggiungi la colonna "Altri" sommando le colonne dei mittenti inattivi
    daily_dataset["Altri"] = daily_dataset[list(inactive_senders_original)].sum(axis=1)
    cumulative_dataset["Altri"] = cumulative_dataset[list(inactive_senders_original)].sum(axis=1)
    
    # Crea versioni per la visualizzazione (senza modificare i dataset originali)
    daily_display = daily_dataset.copy()
    cumulative_display = cumulative_dataset.copy()
    # Applica la mappatura per la visualizzazione (escludendo le colonne 'data' e 'Altri')
    rename_columns = {col: display_map[col] for col in daily_display.columns if col not in {"data", "Altri"}}
    daily_display = daily_display.rename(columns=rename_columns)
    cumulative_display = cumulative_display.rename(columns=rename_columns)
    # La colonna "Altri" la lasciamo invariata
    
    # Ricostruisci l'ordine delle colonne per la visualizzazione:
    # - "data"
    # - il totale (visualizzato come "TOTALE")
    # - i mittenti attivi (nella loro forma visualizzata), ordinati secondo l'ordine originale
    # - "Altri"
    active_senders_ordered = [s for s in sorted(senders) if s in active_senders_original]
    active_senders_display_ordered = [display_map[s] for s in active_senders_ordered]
    selected_display_columns = ["data", display_map["TOTAL"]] + active_senders_display_ordered + ["Altri"]
    
    # Filtra i dataset di visualizzazione per avere solo le colonne selezionate
    daily_filtered = daily_display[selected_display_columns]
    cumulative_filtered = cumulative_display[selected_display_columns]
    
    # Configura la legenda: le serie attive (e il totale) sono selezionate di default
    legend_selected = {
        col: (col in active_senders_display_ordered or col == display_map["TOTAL"])
        for col in selected_display_columns[1:]  # escludi "data"
    }
    
    # Imposta le opzioni per il grafico giornaliero
    option_daily = {
        "animationDuration": 100,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_display_columns,
            "source": daily_filtered.values.tolist()
        }],
        "title": {"text": "Andamento giornaliero"},
        "tooltip": {"trigger": "axis", "triggerOn": "click"},
        "legend": {
            "data": selected_display_columns[1:],  # Escludi "data"
            "selected": legend_selected,
            "left": "0%",
            "orient": "vertical",
            "textStyle": {"fontSize": 10}
        },
        "grid": {"left": "15%", "right": "5%", "bottom": "10%"},
        "xAxis": {"type": "category"},
        "yAxis": {},
        "series": [
            {
                "type": "line",
                "showSymbol": True,
                "name": col,
                "encode": {"x": "data", "y": col},
                "smooth": True
            }
            for col in selected_display_columns[1:]
        ],
        "media": [
            {
                "query": {"maxWidth": 768},
                "option": {
                    "legend": {"orient": "horizontal", "left": "center", "bottom": "0%"},
                    "grid": {"left": "5%", "right": "5%", "bottom": "15%"}
                }
            }
        ]
    }
    
    # Imposta le opzioni per il grafico cumulato
    option_cumulative = {
        "animationDuration": 100,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_display_columns,
            "source": cumulative_filtered.values.tolist()
        }],
        "title": {"text": "Andamento cumulato"},
        "tooltip": {"trigger": "axis", "triggerOn": "click"},
        "legend": {
            "data": selected_display_columns[1:],
            "selected": legend_selected,
            "left": "0%",
            "orient": "vertical",
            "textStyle": {"fontSize": 10}
        },
        "grid": {"left": "15%", "right": "5%", "bottom": "10%"},
        "xAxis": {"type": "category"},
        "yAxis": {},
        "series": [
            {
                "type": "line",
                "showSymbol": True,
                "name": col,
                "encode": {"x": "data", "y": col},
                "smooth": True
            }
            for col in selected_display_columns[1:]
        ],
        "media": [
            {
                "query": {"maxWidth": 768},
                "option": {
                    "legend": {"orient": "horizontal", "left": "center", "bottom": "0%"},
                    "grid": {"left": "5%", "right": "5%", "bottom": "15%"}
                }
            }
        ]
    }
    
    # Altezza dinamica o fissa (qui usiamo 600px)
    dynamic_height = 600

    # Mostra i grafici nel container
    st_echarts(options=option_daily, height=f"{dynamic_height}px", key="daily_echarts")
    st_echarts(options=option_cumulative, height=f"{dynamic_height}px", key="cumulative_echarts")



def display_tipologie_mittenti_tab(container, df):
    col1, col2 = container.columns(2)
    
    if "tipo_atto" in df.columns:
        tipologia_counts = df["tipo_atto"].value_counts().reset_index()
        tipologia_counts.columns = ["Tipo Atto", "Numero di Pubblicazioni"]
        palette = sns.color_palette("pastel", len(tipologia_counts)).as_hex()
        # Utilizzo di Plotly per questo grafico (rimane invariato)
        import plotly.express as px
        fig_tipologie = px.bar(
            tipologia_counts, x="Tipo Atto", y="Numero di Pubblicazioni",
            title="Tipologie", color="Tipo Atto", color_discrete_sequence=palette
        )
        fig_tipologie.update_layout(dragmode=False, showlegend=False)
        col1.plotly_chart(fig_tipologie, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        col1.warning("Dati sulle tipologie non disponibili.")
    
    if "mittente" in df.columns:
        mittente_counts = df["mittente"].value_counts().reset_index()
        mittente_counts.columns = ["Mittente", "Numero di Pubblicazioni"]
        mittente_counts["Mittente"] = mittente_counts["Mittente"].apply(lambda x: x[:15] + "…" if len(x) > 20 else x)
        palette = sns.color_palette("pastel", len(mittente_counts)).as_hex()
        import plotly.express as px
        fig_mittenti = px.bar(
            mittente_counts, x="Mittente", y="Numero di Pubblicazioni",
            title="Mittenti", color="Mittente", color_discrete_sequence=palette
        )
        fig_mittenti.update_layout(dragmode=False, showlegend=False)
        col2.plotly_chart(fig_mittenti, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        col2.warning("Dati sui mittenti non disponibili.")

def display_ritardi_tab(container, df):
    df_delays, df_missing = analyze_publication_delays(df)
    
    if "numero_pubblicazione" not in df_delays.columns:
        df_delays = df_delays.reset_index().rename(columns={"index": "numero_pubblicazione"})
    
    aggregated = df_delays.groupby("mittente").agg(
         ritardo_medio=('ritardo_pubblicazione', 'mean'),
         numero_pubblicazioni_totali=('ritardo_pubblicazione', 'count'),
         ritardo_massimo=('ritardo_pubblicazione', 'max')
    ).reset_index()
    
    max_idx = df_delays.groupby("mittente")["ritardo_pubblicazione"].idxmax()
    max_publications = df_delays.loc[max_idx, ["mittente", "numero_pubblicazione"]].rename(
         columns={"numero_pubblicazione": "pub_max_ritardo"}
    )
    
    performance = aggregated.merge(max_publications, on="mittente", how="left")
    performance["ritardo_medio"] = performance["ritardo_medio"].round(0).astype(int)
    performance = performance.sort_values("ritardo_medio", ascending=False)
    performance = performance.rename(columns={
         "mittente": "Mittente",
         "ritardo_medio": "Ritardo medio",
         "ritardo_massimo": "Ritardo massimo",
         "numero_pubblicazioni_totali": "Pubblicazioni totali",
         "pub_max_ritardo": "Pubblicazione max ritardo"
    })
    
    st.markdown("**Analisi dei ritardi per mittente**")
    container.dataframe(performance, use_container_width=True)
    
    if not df_missing.empty:
        st.markdown("**Pubblicazioni senza la data registro**")
        df_missing_copy = df_missing.copy()
        df_missing_copy = df_missing_copy.rename(columns={
            "numero_pubblicazione": "Numero",
            "mittente": "Mittente",
            "oggetto_atto": "Oggetto",
            "data_inizio_pubblicazione": "Data Pubblicazione"
        })
        df_missing_copy["Data Pubblicazione"] = pd.to_datetime(
            df_missing_copy["Data Pubblicazione"], errors="coerce"
        ).dt.strftime("%d-%m-%Y")
        container.dataframe(df_missing_copy, use_container_width=True)

# ---------------------- FUNZIONE PRINCIPALE ----------------------

def page_analisi(df):
    st.header("📊 ANALISI")
    
    # Creazione dei tab
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])
    
    with tab_temporale:
        display_temporal_tab(tab_temporale, df)
    
    with tab_tipologie:
        display_tipologie_mittenti_tab(tab_tipologie, df)
    
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)
