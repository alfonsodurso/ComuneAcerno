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
    Visualizza due grafici (giornaliero e cumulato) con andamento totale e per mittente,
    raggruppando i mittenti inattivi sotto "Altri". La configurazione è ottimizzata
    anche per smartphone.
    """
    daily_data, cumulative_data, senders = prepare_time_series_data_by_sender(df)
    
    active_senders = {s.title() for s in {
        "Area tecnica 1", "Area tecnica 2", "Area vigilanza", "Area amministrativa", "Comune di acerno"
    }}
    
    display_map = {col: "TOTALE" if col == "TOTAL" else col.title() for col in daily_data.columns}
    display_map["data"] = "data"
    
    active_original = {s for s in senders if display_map.get(s, s) in active_senders}
    inactive_original = set(senders) - active_original
    
    for dataset in [daily_data, cumulative_data]:
        dataset["Altri"] = dataset[list(inactive_original)].sum(axis=1)
    
    rename_columns = {col: display_map[col] for col in daily_data.columns if col not in {"data", "Altri"}}
    daily_display, cumulative_display = [df.rename(columns=rename_columns) for df in [daily_data, cumulative_data]]
    
    selected_cols = ["data", "TOTALE"] + sorted(display_map[s] for s in active_original) + ["Altri"]
    daily_filtered, cumulative_filtered = [df[selected_cols] for df in [daily_display, cumulative_display]]
    
    legend_selected = {col: col in active_senders or col == "TOTALE" for col in selected_cols[1:]}
    
    def create_chart(title, dataset):
        return {
            "animationDuration": 200,
            "dataset": [{
                "id": "dataset_raw",
                "dimensions": selected_cols,
                "source": dataset.values.tolist()
            }],
            "title": {"text": title},
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": selected_cols[1:],
                "selected": legend_selected,
                "orient": "horizontal",
                "bottom": "5px"
            },
            "xAxis": {"type": "category"},
            "yAxis": {},
            "grid": {
                "bottom": "55px"
            },
            "series": [
                {
                    "type": "line",
                    "name": col,
                    "encode": {"x": "data", "y": col},
                    "smooth": True
                }
                for col in selected_cols[1:]
            ]
        }
    
    st_echarts(options=create_chart("Andamento giornaliero", daily_filtered), key="daily_echarts")
    st_echarts(options=create_chart("Andamento cumulato", cumulative_filtered), key="cumulative_echarts")


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
