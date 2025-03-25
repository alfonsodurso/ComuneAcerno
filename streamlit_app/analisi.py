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

# ------------------------Tipologie & Mittenti----------------------------

def prepare_mittenti_count(df: pd.DataFrame, selected_senders: list) -> pd.DataFrame:
    """
    Prepara il DataFrame contenente il conteggio delle pubblicazioni per ogni mittente.
    I mittenti sono mappati tramite la variabile active_mapping.
    Vengono considerati solo i mittenti il cui nome mappato è presente in selected_senders.
    """
    # Mappatura dei mittenti principali
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    
    # Copia per non modificare l'originale
    df_copy = df.copy()
    
    # Mappiamo i mittenti; quelli non presenti nella mappatura saranno etichettati come "Altri"
    df_copy["sender_mapped"] = df_copy["mittente"].apply(lambda s: active_mapping.get(s, "Altri"))
    
    # Filtriamo solo i mittenti che sono stati selezionati (se non presenti in session_state, usiamo tutti)
    filtered_df = df_copy[df_copy["sender_mapped"].isin(selected_senders)]
    
    # Calcoliamo il conteggio per ciascun mittente
    counts = filtered_df["sender_mapped"].value_counts().reset_index()
    counts.columns = ["label", "value"]
    
    return counts

def prepare_tipologie_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara il DataFrame contenente il conteggio delle pubblicazioni per ciascuna tipologia.
    """
    counts = df["tipo_atto"].value_counts().reset_index()
    counts.columns = ["label", "value"]
    return counts


"""
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

    series = [{
        "type": "line",
        "name": col,
        "encode": {"x": "data", "y": col},
        "smooth": True,
        "legendHoverLink": True  # Permette di filtrare tramite la legenda
    } for col in selected_cols[1:]]  # Non includiamo "data" nei grafici

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
        "series": series,
        "legend": {
            "data": selected_cols[1:],  # La legenda mostra i mittenti e il Totale
            "selected": {col: True for col in selected_cols[1:]},  # Tutti i mittenti sono selezionati di default
            "orient": "horizontal",
            "top": "top"
        },
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
    }

# ------------------------Tipologie & Mittenti----------------------------

def display_tipologie_tab(container, df: pd.DataFrame):
    """
    Visualizza la tab "Tipologie" con due radiobutton:
     - "Mittenti": mostra il numero di pubblicazioni per mittente
     - "Tipologie": mostra il numero di pubblicazioni per tipologia
    Non viene usato alcun multiselect; il filtro sui mittenti avviene tramite la variabile di sessione 
    (se presente, proveniente dalla prima tab "Analisi temporale") e, in ogni caso, la visualizzazione 
    può essere affinata tramite la legenda del grafico.
    """
    view_option = st.radio("Visualizza per:", ["Mittenti", "Tipologie"], horizontal=True)
    
    if view_option == "Mittenti":
        # Definiamo la mappatura attiva per i mittenti
        active_mapping = {
            "AREA TECNICA 1": "Area Tecnica 1",
            "AREA TECNICA 2": "Area Tecnica 2",
            "AREA VIGILANZA": "Area Vigilanza",
            "AREA AMMINISTRATIVA": "Area Amministrativa",
            "COMUNE DI ACERNO": "Comune di Acerno"
        }
        # Se esiste una selezione nella prima tab, la usiamo; altrimenti usiamo tutti i mittenti attivi
        default_senders = list(active_mapping.values())
        selected_senders = st.session_state.get("selected_senders", default_senders)
        
        # Prepara i dati aggregati per mittente
        chart_data = prepare_mittenti_count(df, selected_senders)
        st.markdown("**Numero di pubblicazioni per mittente**")
    
    elif view_option == "Tipologie":
        # Prepara i dati aggregati per tipologia
        chart_data = prepare_tipologie_count(df)
        st.markdown("**Numero di pubblicazioni per tipologia**")
    
    # Crea la configurazione del grafico a torta (doughnut) e lo visualizza
    chart_config = create_doughnut_chart(chart_data)
    st_echarts(options=chart_config, height="400px")
    
"""
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
            st_echarts(options=sender_daily_chart, key="sender_daily_chart", height="400px")
            st_echarts(options=total_daily_chart, key="total_daily_chart", height="400px")
        elif selected_label == "Andamento cumulato":
            # Mostriamo i grafici per l'andamento cumulato
            st_echarts(options=sender_cumulative_chart, key="sender_cumulative_chart", height="400px")
            st_echarts(options=total_cumulative_chart, key="total_cumulative_chart", height="400px")

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
"""
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
    with tab_tipologie:
        display_typology_tab(tab_tipologie, df)
    """
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)
    """


