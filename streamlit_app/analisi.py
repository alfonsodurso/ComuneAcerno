import streamlit as st

# Simuliamo un DataFrame con colonne di esempio
import pandas as pd
import numpy as np

# Creazione di dati di esempio
np.random.seed(42)
date_rng = pd.date_range(start="2024-01-01", periods=30, freq="D")
df = pd.DataFrame({
    "data": date_rng,
    "Area Tecnica 1": np.random.randint(10, 50, size=len(date_rng)),
    "Area Tecnica 2": np.random.randint(5, 40, size=len(date_rng)),
    "Area Vigilanza": np.random.randint(8, 45, size=len(date_rng)),
    "Area Amministrativa": np.random.randint(12, 55, size=len(date_rng)),
    "Comune di Acerno": np.random.randint(7, 50, size=len(date_rng)),
    "Altri": np.random.randint(5, 20, size=len(date_rng)),
    "TOTALE": lambda x: x.sum(axis=1),
})

# Select per scegliere l'area da visualizzare
opzioni = ["Tutte le Aree"] + list(df.columns[1:])
area_selezionata = st.selectbox("Seleziona l'area", opzioni)

# Filtriamo il dataset in base alla selezione
if area_selezionata == "Tutte le Aree":
    selected_cols = df.columns.tolist()  # Mostra tutto
else:
    selected_cols = ["data", area_selezionata]  # Solo la colonna selezionata

# Funzione per creare il grafico senza legenda su mobile
def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
    """
    Crea la configurazione per un grafico lineare ECharts.
    Se l'utente sceglie una singola area, la legenda è nascosta per ottimizzare la UX su mobile.
    """
    # Converte il dataset in lista di liste
    source = dataset[selected_cols].copy()
    source["data"] = source["data"].dt.strftime("%d-%m-%Y")  # Convertiamo i Timestamp
    source = source.values.tolist()

    # Config base
    config = {
        "animationDuration": 500,
        "dataset": [{
            "id": "dataset_raw",
            "dimensions": selected_cols,
            "source": source
        }],
        "title": {"text": title},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category"},
        "yAxis": {},
        "grid": {"right": "5%", "bottom": "10%"},
        "series": [{
            "type": "line",
            "name": col,
            "encode": {"x": "data", "y": col},
            "smooth": True
        } for col in selected_cols[1:]],
        "labelLayout": {"moveOverlap": "shiftX"},
        "emphasis": {"focus": "series"}
    }

    # Se sono visualizzati tutti i dati, la legenda è abilitata su desktop
    if area_selezionata == "Tutte le Aree":
        config["legend"] = {
            "data": selected_cols[1:],
            "orient": "vertical",
            "right": "0%",
            "top": "middle"
        }
        # Adattamento mobile: legenda in basso e orizzontale
        config["media"] = [{
            "query": {"maxWidth": 768},
            "option": {
                "legend": {
                    "left": "center",
                    "bottom": "0%",
                    "orient": "horizontal"
                },
                "grid": {"bottom": "15%"}
            }
        }]
    
    return config

# Mostra il grafico
import streamlit_echarts as ste
chart_config = crea_config_chart("Andamento delle Aree", df, selected_cols)
ste.st_echarts(options=chart_config, key=area_selezionata)
