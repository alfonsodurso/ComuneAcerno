import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------

# Costante per la mappatura dei mittenti
ACTIVE_MAPPING = {
    "AREA TECNICA 1": "Area Tecnica 1",
    "AREA TECNICA 2": "Area Tecnica 2",
    "AREA VIGILANZA": "Area Vigilanza",
    "AREA AMMINISTRATIVA": "Area Amministrativa",
    "COMUNE DI ACERNO": "Comune di Acerno"
}

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

    # Filtriamo i dati per includere solo i mittenti definiti
    df_copy = df_copy[df_copy["mittente"].isin(ACTIVE_MAPPING.keys())]

    # Crea una tabella pivot che raggruppa per data e mittente
    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()

    # Calcola il totale (TOTALE) per ogni data
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)  # assicura che siano tipi Python (evita numpy.int64)

    rename_dict = {"TOTAL": "TOTALE"}
    for sender in ACTIVE_MAPPING:
        rename_dict[sender] = ACTIVE_MAPPING[sender]

    # Ordina i dati come specificato
    final_order = ["data"] + [ACTIVE_MAPPING[s] for s in ACTIVE_MAPPING] + ["TOTALE"]

    daily_dataset = pivot.reset_index().rename(columns=rename_dict)
    daily_dataset["data"] = daily_dataset["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    daily_dataset = daily_dataset[final_order]

    cumulative_dataset = daily_dataset.copy()
    for col in final_order:
        if col != "data":
            cumulative_dataset[col] = cumulative_dataset[col].cumsum()

    return daily_dataset, cumulative_dataset

# ------------------------Tipologie & Mittenti----------------------------

def prepare_mittenti_count(df: pd.DataFrame, selected_senders: list, mapping: dict = ACTIVE_MAPPING) -> pd.DataFrame:
    """
    Prepara un DataFrame contenente il conteggio delle pubblicazioni per ogni mittente.
    I mittenti sono mappati tramite il dizionario 'mapping'. Vengono considerati solo 
    i mittenti il cui nome mappato è presente in selected_senders.
    """
    df_copy = df.copy()
    df_copy["sender_mapped"] = df_copy["mittente"].apply(lambda s: mapping.get(s, "Altri"))
    filtered_df = df_copy[df_copy["sender_mapped"].isin(selected_senders)]
    counts = filtered_df["sender_mapped"].value_counts().reset_index()
    counts.columns = ["label", "value"]
    return counts

def prepare_tipologie_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara un DataFrame contenente il conteggio delle pubblicazioni per ciascuna tipologia.
    """
    counts = df["tipo_atto"].value_counts().reset_index()
    counts.columns = ["label", "value"]
    return counts

# ------------------------Ritardi----------------------------

def prepare_ritardi_metrics(df: pd.DataFrame, mapping: dict = ACTIVE_MAPPING) -> pd.DataFrame:
    """
    Prepara una tabella con per ogni mittente:
      - Ritardo medio (in giorni)
      - Ritardo massimo (in giorni)
      - Totale delle pubblicazioni
      - Numero di pubblicazioni che hanno raggiunto il ritardo massimo
    La tabella viene ordinata in ordine decrescente in base al ritardo medio.
    """
    df_copy = df.copy()
    df_copy["data_registro_generale"] = pd.to_datetime(df_copy["data_registro_generale"], errors="coerce")
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"])
    
    # Calcola il ritardo in giorni
    df_copy["ritardo"] = (df_copy["data_inizio_pubblicazione"] - df_copy["data_registro_generale"]).dt.days
    
    # Applica il mapping e filtra solo i mittenti definiti
    df_copy["sender_mapped"] = df_copy["mittente"].apply(lambda s: mapping.get(s, "Altri"))
    df_copy = df_copy[df_copy["mittente"].isin(mapping.keys())]
    
    # Raggruppa per mittente e calcola i valori
    agg = df_copy.groupby("sender_mapped")["ritardo"].agg(["mean", "max", "count"]).reset_index()
    agg = agg.rename(columns={
        "mean": "ritardo_medio", 
        "max": "ritardo_massimo", 
        "count": "totale_pubblicazioni"
    })
    
    # Calcolo: numero di pubblicazioni con ritardo massimo
    def count_max_delay(sub_df):
        max_delay = sub_df["ritardo"].max()
        return (sub_df["ritardo"] == max_delay).sum()
    
    max_counts = df_copy.groupby("sender_mapped").apply(count_max_delay).reset_index(name="pubblicazioni_max_ritardo")
    result = pd.merge(agg, max_counts, on="sender_mapped")
    result["ritardo_medio"] = result["ritardo_medio"].round(2)
    
    # Ordina per ritardo medio decrescente
    result = result.sort_values(by="ritardo_medio", ascending=False)
    
    return result

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

def create_doughnut_chart(data_df: pd.DataFrame) -> dict:
    """
    Crea la configurazione per un grafico a torta (doughnut) utilizzando i dati forniti.
    La funzione gestisce differenti formati di input, verificando la presenza di colonne
    specifiche.
    """
    if "tipo_atto" in data_df.columns and "count" in data_df.columns:
        data = [{"name": row["tipo_atto"], "value": row["count"]} for _, row in data_df.iterrows()]
    elif "label" in data_df.columns and "value" in data_df.columns:
        data = [{"name": row["label"], "value": row["value"]} for _, row in data_df.iterrows()]
    else:
        data = [{"name": row[0], "value": row[1]} for _, row in data_df.iterrows()]
    
    chart_config = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "0%", "left": "center"},
        "series": [{
            "type": "pie",
            "radius": ["40%", "70%"],
            "avoidLabelOverlap": False,
            "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "position": "center", "formatter": "Pubblicazioni"},
            "emphasis": {"label": {"show": True, "fontSize": "12"}},
            "labelLine": {"show": False},
            "data": data
        }]
    }
    return chart_config
    
# ------------------------Ritardi----------------------------

def create_scatter_chart_ritardi(data: pd.DataFrame) -> dict:
    """
    Crea la configurazione per uno scatter plot in cui ogni punto rappresenta un mittente,
    con asse X: ritardo medio e asse Y: ritardo massimo.
    """
    scatter_data = []
    for sender, row in data.iterrows():
        scatter_data.append({
            "name": sender,
            "value": [row["ritardo_medio"], row["ritardo_massimo"]],
            "symbolSize": max(10, min(50, row["totale_pubblicazioni"] * 2))
        })
    
    return {
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}<br/>Ritardo Medio: {c0}<br/>Ritardo Massimo: {c1}"
        },
        "xAxis": {
            "name": "Ritardo medio",
            "type": "value"
        },
        "yAxis": {
            "name": "Ritardo massimo",
            "type": "value"
        },
        "series": [{
            "data": scatter_data,
            "type": "scatter"
        }]
    }

def create_combo_chart_ritardi(data: pd.DataFrame) -> dict:
    """
    Crea la configurazione per un grafico combinato con barre (ritardo medio) e linea (ritardo massimo).
    """
    mittenti = list(data.index)
    ritardi_medi = data["ritardo_medio"].tolist()
    ritardi_massimi = data["ritardo_massimo"].tolist()
    
    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Ritardo medio", "Ritardo massimo"]},
        "xAxis": {"type": "category", "data": mittenti},
        "yAxis": {"type": "value", "name": "Giorni"},
        "series": [
            {
                "name": "Ritardo medio",
                "type": "bar",
                "data": ritardi_medi,
            },
            {
                "name": "Ritardo massimo",
                "type": "line",
                "data": ritardi_massimi,
                "itemStyle": {"color": "#91CC75"},
                "smooth": True
            }
        ]
    }
    
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

def display_tipologie_tab(container, df: pd.DataFrame):
    """
    Visualizza la tab "Tipologie & Mittenti" con una scelta tramite radio button:
      - "Mittenti": visualizza il numero di pubblicazioni per mittente (filtrabili tramite session_state)
      - "Tipologie": visualizza il numero di pubblicazioni per tipologia
    """
    with st.container():
        view_option = st.radio(
            "Visualizza per:",
            ["Mittenti", "Tipologie"],
            horizontal=True,
            index=0,
            key="tipologie_radio"
        )
    
    if view_option == "Mittenti":
        selected_senders = st.session_state.get("selected_senders", list(ACTIVE_MAPPING.values()))
        chart_data = prepare_mittenti_count(df, selected_senders)
    else:  # "Tipologie"
        chart_data = prepare_tipologie_count(df)
    
    chart_config = create_doughnut_chart(chart_data)
    st_echarts(options=chart_config, height="400px", key="echarts_tipologie")

# -----------------------------------------------------------------

def display_ritardi_tab(container, df: pd.DataFrame):
    """
    Visualizza la tab "Ritardi" mostrando:
      - La tabella ordinata dei ritardi per mittente.
      - Il grafico a dispersione (scatter plot).
      - Il grafico combinato (combo chart).
    Con un radiobutton per selezionare "Tabella" o "Grafici".
    """
    with container:
        
        # Radiobutton per scegliere la visualizzazione
        view_option = st.radio(
            "Visualizza:",
            ["Tabella", "Grafici"],
            horizontal=True,
            key="ritardi_view"
        )
        
        # Prepara i dati
        metrics_df = prepare_ritardi_metrics(df)
        """
        # Per rinominare correttamente, resettiamo l'indice e rinominiamo la colonna
        metrics_df = metrics_df.rename(columns={
            "sender_mapped": "Mittente",
            "ritardo_medio": "Ritardo medio",
            "ritardo_massimo": "Ritardo massimo",
            "totale_pubblicazioni": "Pubblicazioni",
            "pubblicazioni_max_ritardo": "Pubb. max ritardo"
        })"""
            
        if view_option == "Tabella":
            st.dataframe(metrics_df.style.hide())
        else:  # "Grafici"
            st_echarts(options=scatter_chart_config, height="400px", key="ritardi_scatter_chart")
            st_echarts(options=combo_chart_config, height="400px", key="ritardi_combo_chart")

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
        display_tipologie_tab(tab_tipologie, df)
    with tab_ritardi:
        display_ritardi_tab(tab_ritardi, df)


