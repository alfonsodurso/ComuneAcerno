import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------- FUNZIONE DI PREPARAZIONE DATI ----------------------

def prepara_dati_temporali_per_mittente(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara i dati temporali aggregati per data e mittente.
    I mittenti nel df sono in uppercase.
    """
    df_copy = df.copy()
    df_copy["data_inizio_pubblicazione"] = pd.to_datetime(df_copy["data_inizio_pubblicazione"], errors="coerce")
    df_copy = df_copy.dropna(subset=["data_inizio_pubblicazione"])
    df_copy["data"] = df_copy["data_inizio_pubblicazione"].dt.date

    pivot = df_copy.pivot_table(index="data", columns="mittente", aggfunc="size", fill_value=0).sort_index()
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.applymap(int)  # converte in tipo int Python

    mapping_attivi = {
        "AREA TECNICA 1": "Area Tecnica 1",
        "AREA TECNICA 2": "Area Tecnica 2",
        "AREA VIGILANZA": "Area Vigilanza",
        "AREA AMMINISTRATIVA": "Area Amministrativa",
        "COMUNE DI ACERNO": "Comune di Acerno"
    }
    ordine_desiderato = ["AREA TECNICA 1", "AREA TECNICA 2", "AREA VIGILANZA", "AREA AMMINISTRATIVA", "COMUNE DI ACERNO"]

    mittenti_presenti = set(pivot.columns) - {"TOTAL"}
    attivi = [sender for sender in ordine_desiderato if sender in mittenti_presenti]
    inattivi = list(mittenti_presenti - set(attivi))

    pivot["ALTRI"] = pivot[inattivi].sum(axis=1) if inattivi else 0

    diz_rename = {"TOTAL": "TOTALE", "ALTRI": "Altri"}
    for sender in attivi:
        diz_rename[sender] = mapping_attivi[sender]

    ordine_finale = ["data", "TOTALE"] + [mapping_attivi[s] for s in ordine_desiderato if s in attivi] + ["Altri"]

    dati_giornalieri = pivot.reset_index().rename(columns=diz_rename)
    dati_giornalieri["data"] = dati_giornalieri["data"].apply(lambda d: d.strftime("%d-%m-%Y"))
    dati_giornalieri = dati_giornalieri[ordine_finale]

    dati_cumulativi = dati_giornalieri.copy()
    for col in ordine_finale:
        if col != "data":
            dati_cumulativi[col] = dati_cumulativi[col].cumsum()

    return dati_giornalieri, dati_cumulativi

def prepara_dati_tipo_atto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara i dati per il grafico a ciambella dei tipi di atto pubblicati.
    """
    conteggi = df["tipo_atto"].value_counts().reset_index()
    conteggi.columns = ["tipo_atto", "conteggio"]
    return conteggi

# ---------------------- CONFIGURAZIONE DEI GRAFICI ----------------------

def crea_configurazione_grafico(titolo: str, dataset: pd.DataFrame, colonne_selezionate: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    """
    source = dataset.values.tolist()
    source = [
        [cell.strftime("%d-%m-%Y") if hasattr(cell, "strftime") else cell for cell in riga]
        for riga in source
    ]
    return {
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": colonne_selezionate,
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
        } for col in colonne_selezionate[1:]],
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"},
    }

def crea_grafico_ciambella(dataset: pd.DataFrame) -> dict:
    """
    Crea la configurazione del grafico a ciambella.
    """
    dati = [{"value": row["conteggio"], "name": row["tipo_atto"]} for _, row in dataset.iterrows()]
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Tipi di Atto",
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
                "data": dati,
            }
        ],
    }

# ---------------------- VISUALIZZAZIONE ----------------------

def visualizza_tab_temporale(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali con possibilità di filtrare i dati tramite una multiselect.
    """
    dati_giornalieri, dati_cumulativi = prepara_dati_temporali_per_mittente(df)
    colonne_disponibili = dati_giornalieri.columns.tolist()[1:]
    colonne_selezionate = st.multiselect("Seleziona i dati da visualizzare:", colonne_disponibili, default=colonne_disponibili)
    colonne_selezionate.insert(0, "data")

    configurazioni = {
        "andamento_giornaliero": crea_configurazione_grafico("Andamento Giornaliero", dati_giornalieri[colonne_selezionate], colonne_selezionate),
        "andamento_cumulato": crea_configurazione_grafico("Andamento Cumulato", dati_cumulativi[colonne_selezionate], colonne_selezionate),
    }

    tab_label = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
    }
    scelta_label = st.radio("Seleziona il grafico", list(tab_label.keys()), horizontal=True)
    chiave_scelta = tab_label[scelta_label]

    with st.container():
        try:
            st_echarts(options=configurazioni[chiave_scelta], key=chiave_scelta)
        except Exception as e:
            st.error("Errore durante il caricamento del grafico.")
            st.exception(e)

def visualizza_tab_tipo_atto(container, df: pd.DataFrame):
    """
    Visualizza la tab 'Tipi di Atto & Mittenti' con il grafico a ciambella e il filtro per mittente.
    """
    opzione_visualizzazione = st.radio("Seleziona la visualizzazione:", ["Tipi di Atto"], horizontal=True)
    dati_tipo_atto = prepara_dati_tipo_atto(df)

    mittenti_disponibili = sorted(df["mittente"].unique().tolist())
    mittenti_selezionati = st.multiselect("Filtra per mittente:", mittenti_disponibili, default=mittenti_disponibili)

    df_filtrato = df[df["mittente"].isin(mittenti_selezionati)]

    if opzione_visualizzazione == "Tipi di Atto":
        dati_grafico = prepara_dati_tipo_atto(df_filtrato)
        config_grafico = crea_grafico_ciambella(dati_grafico)
        st_echarts(options=config_grafico, height="500px")

# ---------------------- FUNZIONE PRINCIPALE ----------------------

def pagina_analisi(df: pd.DataFrame):
    st.header("📊 ANALISI")
    tab_temporale, tab_tipo_atto, tab_ritardi = st.tabs([
        "📆 Andamento Temporale",
        "📋 Tipi di Atto & Mittenti",
        "⏳ Ritardi"
    ])
    with tab_temporale:
        visualizza_tab_temporale(tab_temporale, df)
    with tab_tipo_atto:
        visualizza_tab_tipo_atto(tab_tipo_atto, df)
    # Il tab "Ritardi" potrà essere implementato in futuro

if __name__ == "__main__":
    # Assicurarsi di avere un DataFrame "df" valido.
    pagina_analisi(df)
