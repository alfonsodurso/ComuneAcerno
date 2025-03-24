import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------

def prepare_time_series_data_by_sender(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    I mittenti nel df sono in uppercase.
    """
    # Converte la data di pubblicazione e filtra eventuali errori
    df_copy = df.copy()
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_inizio_pubblicazione"])
    df_copy["data"] = df_copy["data_inizio_pubblicazione"].dt.date

    # Crea una tabella pivot che raggruppa per data e mittente
    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()

    # Calcola il totale (TOTALE) per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)  # assicura che siano tipi Python (evita numpy.int64)

    # Mappatura per i mittenti principali (assumendo che nel df i nomi siano in uppercase)
    active_mapping = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    desired_order = ["AREA TECNICA 1", "AREA TECNICA 2", "AREA VIGILANZA", "AREA AMMINISTRATIVA", "COMUNE DI ACERNO"]

    existing_senders = set(pivot.columns) - {"TOTAL"}
    active = [sender for sender in desired_order if sender in existing_senders]
    inactive = list(existing_senders - set(active))

    pivot["ALTRI"] = pivot[inactive].sum(axis=1) if inactive else 0

    rename_dict = {"TOTAL": "TOTALE", "ALTRI": "Altri"}
    for sender in active:
        rename_dict[sender] = active_mapping[sender]

    final_order = ["data", "TOTALE"] + [active_mapping[s] for s in desired_order if s in active] + ["Altri"]

    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

# ------------------------Tipologie & Mittenti----------------------------

def prepare_typology_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara i dati per il grafico a ciambella delle tipologie di atto pubblicate."""
    typology_counts = df["tipo_atto"].value_counts().reset_index()
    typology_counts.columns = ["tipo_atto", "count"]
    return typology_counts

def prepare_mittente_data_with_altri(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara i dati per il grafico a ciambella dei mittenti, aggregando in "Altri"
    quelli non presenti nella mappatura dei mittenti principali.
    """
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
    
# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------

def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
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
            "smooth": True
        } for col in selected_cols[1:]],
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
    }

# ------------------------Tipologie & Mittenti----------------------------

def create_doughnut_chart(dataset: pd.DataFrame) -> dict:
    """Crea la configurazione del grafico a ciambella (doughnut)."""
    data = [{"value": row["count"], "name": row[0]} for _, row in dataset.iterrows()]
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
    
# ---------------------- VISUALIZZAZIONE ----------------------

def display_temporal_tab(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali con possibilità di filtrare i dati tramite una multiselect.
    """
    
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)
    # Escludiamo "data" per la multiselect (assicurandoci di mantenerla sempre)
    available_cols = daily_data.columns.tolist()[1:]
    selected_cols = st.multiselect("Seleziona i dati da visualizzare:", available_cols, default=available_cols)
    selected_cols.insert(0, "data")

    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data[selected_cols], selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data[selected_cols], selected_cols),
    }

    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
    }
    selected_label = st.radio("Seleziona il grafico", list(tab_labels.keys()), horizontal=True)
    selected_key = tab_labels[selected_label]

    with st.container():
        try:
            st_echarts(options=schede[selected_key], key=selected_key, height="500px")
        except Exception as e:
            st.error("Errore durante il caricamento del grafico.")
            st.exception(e)

# ------------------------Tipologie & Mittenti----------------------------

def display_typology_tab(container, df: pd.DataFrame):
    """Visualizza la tab Tipologie & Mittenti con due modalità:
       1. Tipologie: grafico a ciambella delle tipologie di atto (filtrato per mittente).
       2. Mittenti: grafico a ciambella dei mittenti (filtrato per tipologia di atto)."""

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

if __name__ == "__main__":
    page_analisi(df_example)
