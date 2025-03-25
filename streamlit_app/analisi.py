import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data_by_sender(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    Considera solo i mittenti definiti nel mapping.
    """
    # Converte la data di pubblicazione e filtra eventuali errori
    df_copy = df.copy()
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_inizio_pubblicazione"])
    df_copy["data"] = df_copy["data_inizio_pubblicazione"].dt.date

    # Definiamo i mittenti attivi da considerare
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }

    # Filtriamo i dati per includere solo i mittenti definiti
    df_copy = df_copy[df_copy["mittente"].isin(active_mapping.keys())]

    # Crea una tabella pivot che raggruppa per data e mittente
    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()

    # Calcola il totale (TOTALE) per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)  # assicura che siano tipi Python (evita numpy.int64)

    rename_dict = {"TOTAL": "TOTALE"}
    for sender in active_mapping:
        rename_dict[sender] = active_mapping[sender]

    # Ordina i dati come specificato
    final_order = ["data"] + [active_mapping[s] for s in active_mapping] + ["TOTALE"]

    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

"""
# ------------------------Tipologie & Mittenti----------------------------

def prepare_typology_data(df: pd.DataFrame) -> pd.DataFrame:

    typology_counts = df["tipo_atto"].value_counts().reset_index()
    typology_counts.columns = ["tipo_atto", "count"]
    return typology_counts

def prepare_mittente_data_with_altri(df: pd.DataFrame) -> pd.DataFrame:

    # Definizione della mappatura dei mittenti principali
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    desired_order = list(active_mapping.keys())
    counts = df["mittente"].value_counts().to_dict()

    # Dati per i mittenti "attivi"
    data_list = []
    for sender in desired_order:
        cnt = counts.get(sender, 0)
        if cnt > 0:
            data_list.append((active_mapping[sender], cnt))
    # Somma dei mittenti non mappati
    others_count = sum(cnt for sender, cnt in counts.items() if sender not in desired_order)
    if others_count > 0:
        data_list.append(("Altri", others_count))
    # Converte in DataFrame con colonne 'label' e 'value'
    return pd.DataFrame(data_list, columns=["label", "value"])

# ------------------------------------------------------------------------

def analyze_publication_delays(df):

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

    performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    performance.columns = ["Mittente", "Ritardo medio"]
    performance = performance.sort_values(by="Ritardo medio", ascending=False)
    return performance
"""
# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------

def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    Ora senza la multiselect, filtro tramite la legenda.
    """
    source = dataset.values.tolist()
    source = [[cell.strftime("%d-%m-%Y") if hasattr(cell, "strftime") else cell for cell in row] for row in source]
    
    return {
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_cols,
            "source": source
        }],
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category"},
        "yAxis": {},
        "series": [{
            "type": "line",
            "name": col,
            "encode": {"x": "data", "y": col},
            "smooth": True,
            "legendHoverLink": True  # Permette di filtrare tramite la legenda
        } for col in selected_cols[1:]],  # Non includiamo "data" nei grafici
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
    }


"""
# ------------------------Tipologie & Mittenti----------------------------

def create_doughnut_chart(dataset: pd.DataFrame) -> dict:

    if "tipo_atto" in dataset.columns and "count" in dataset.columns:
        data = [{"name": row["tipo_atto"], "value": row["count"]} for _, row in dataset.iterrows()]
    elif "label" in dataset.columns and "value" in dataset.columns:
        data = [{"name": row["label"], "value": row["value"]} for _, row in dataset.iterrows()]
    else:
        data = [{"name": row[0], "value": row[1]} for _, row in dataset.iterrows()]
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Distribuzione",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": "20", "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": data,
            }
        ],
    }

# -------------------------------------------------------------

def display_ritardi_tab(container, df):

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
"""    
# ---------------------- VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali. La multiselect è rimossa e il filtro dei dati è tramite la legenda.
    """
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)

    # Grafico solo per Totale (senza mittenti)
    total_daily_chart = crea_config_chart("Andamento Totale Giornaliero", daily_data[["data", "TOTALE"]], ["data", "TOTALE"])
    total_cumulative_chart = crea_config_chart("Andamento Totale Cumulato", cumulative_data[["data", "TOTALE"]], ["data", "TOTALE"])

    # Grafico diversificato per mittente (senza il Totale)
    available_cols = daily_data.columns.tolist()[1:-1]  # Escludiamo "data" e "TOTALE"
    selected_cols = ["data"] + available_cols  # Aggiungiamo "data" come prima colonna per entrambi i grafici

    # Creazione dei grafici per mittenti
    sender_daily_chart = crea_config_chart("Andamento Mittenti Giornaliero", daily_data[selected_cols], selected_cols)
    sender_cumulative_chart = crea_config_chart("Andamento Mittenti Cumulato", cumulative_data[selected_cols], selected_cols)

    # Selezione del radiobutton per il grafico
    selected_label = st.radio("Seleziona l'andamento", ["Andamento giornaliero", "Andamento cumulato"], horizontal=True)

    with st.container():
        if selected_label == "Andamento giornaliero":
            # Mostriamo i grafici per l'andamento giornaliero
            st.subheader("Andamento Giornaliero per Mittenti")
            st_echarts(options=sender_daily_chart, key="sender_daily_chart", height="500px")
            st.subheader("Andamento Giornaliero Totale")
            st_echarts(options=total_daily_chart, key="total_daily_chart", height="500px")
        elif selected_label == "Andamento cumulato":
            # Mostriamo i grafici per l'andamento cumulato
            st.subheader("Andamento Cumulato per Mittenti")
            st_echarts(options=sender_cumulative_chart, key="sender_cumulative_chart", height="500px")
            st.subheader("Andamento Cumulato Totale")
            st_echarts(options=total_cumulative_chart, key="total_cumulative_chart", height="500px")

"""

# ------------------------Tipologie & Mittenti----------------------------

def display_typology_tab(container, df: pd.DataFrame):

    # Radio button per selezionare la visualizzazione
    view_option = st.radio("Visualizza per:", 
                           ["Tipologie", "Mittenti"], horizontal=True)

    if view_option == "Tipologie":
        # Mappatura dei mittenti (i df hanno i mittenti in uppercase)
        active_mapping = {
            "AREA TECNICA 1": "Area Tecnica 1",
            "AREA TECNICA 2": "Area Tecnica 2",
            "AREA VIGILANZA": "Area Vigilanza",
            "AREA AMMINISTRATIVA": "Area Amministrativa",
            "COMUNE DI ACERNO": "Comune di Acerno"
        }
        # Ottieni i mittenti presenti nel dataframe (escludendo "TOTALE")
        existing_senders = set(df["mittente"].unique()) - {"TOTALE"}
        # Mittenti "attivi" in base alla mappatura
        active = [s for s in active_mapping if s in existing_senders]
        # Gli altri mittenti (non mappati)
        inactive = list(existing_senders - set(active))
        # Lista finale per la multiselect: i mittenti mappati + "Altri" se presenti
        available_senders = [active_mapping[s] for s in active] + (["Altri"] if inactive else [])

        # Inizializza lo stato se non esiste
        if "selected_senders" not in st.session_state:
            st.session_state.selected_senders = available_senders

        # Multiselect per i mittenti
        selected_senders = st.multiselect(
            "Filtra per mittente:", 
            available_senders, 
            key="selected_senders"
        )
        if not selected_senders:
            selected_senders = available_senders

        # Mappatura inversa: da nomi visualizzati ai nomi originali
        selected_senders_mapped = [s for s, mapped in active_mapping.items() if mapped in selected_senders]
        if "Altri" in selected_senders:
            selected_senders_mapped += inactive

        # Filtraggio del dataframe
        filtered_df = df[df["mittente"].isin(selected_senders_mapped)]
        if not filtered_df.empty:
            chart_data = prepare_typology_data(filtered_df)
            chart_config = create_doughnut_chart(chart_data)
            st_echarts(options=chart_config, height="500px")
        else:
            st.warning("⚠️ Nessun dato disponibile per i mittenti selezionati.")

    elif view_option == "Mittenti":
        # In questo caso il filtro è sulle tipologie di atto
        available_tipologie = sorted(df["tipo_atto"].unique())
        if "selected_tipologie" not in st.session_state:
            st.session_state.selected_tipologie = available_tipologie
        selected_tipologie = st.multiselect(
            "Filtra per tipologia di atto:", 
            available_tipologie, 
            key="selected_tipologie"
        )
        if not selected_tipologie:
            selected_tipologie = available_tipologie
        # Filtra il dataframe in base alle tipologie selezionate
        filtered_df = df[df["tipo_atto"].isin(selected_tipologie)]
        if not filtered_df.empty:
            # Prepara i dati aggregati per i mittenti
            chart_data = prepare_mittente_data_with_altri(filtered_df)
            chart_config = create_doughnut_chart(chart_data)
            st_echarts(options=chart_config, height="500px")
        else:
            st.warning("⚠️ Nessun dato disponibile per le tipologie selezionate.")

# -----------------------------------------------------------------

def display_ritardi_tab(container, df):

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
"""
        
# ---------------------- FUNZIONE PRINCIPALE ----------------------

def page_analisi(df: pd.DataFrame):
    st.header("📊 ANALISI")
    tab_temporale, tab_tipologie, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipologie & Mittenti",
        "⏳ Ritardi"
    ])
    with tab_temporale:
        display_temporal_tab(tab_temporale, df)
    """
    with tab_tipologie:
        display_typology_tab(tab_tipologie, df)
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)
    """


