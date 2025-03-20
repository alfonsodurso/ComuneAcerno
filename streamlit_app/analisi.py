import streamlit as st
import pandas as pd
import numpy as np
import streamlit_echarts as ste

# Simuliamo un DataFrame con dati di esempio
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

# Select multipla per filtrare i dati
opzioni = list(df.columns[1:])  # Escludiamo la colonna 'data'
aree_selezionate = st.multiselect("Seleziona le aree", opzioni, default=opzioni)

# Se nessuna area è selezionata, non mostrare nulla
if not aree_selezionate:
    st.warning("Seleziona almeno un'area per visualizzare il grafico.")
else:
    # Creiamo il dataset filtrato
    selected_cols = ["data"] + aree_selezionate

    def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
        """
        Crea la configurazione per un grafico lineare ECharts con più selezioni.
        """
        # Converte i Timestamp in stringhe per evitare errori di serializzazione
        dataset["data"] = dataset["data"].dt.strftime("%d-%m-%Y")

        # Convertiamo i dati in una lista di liste
        source = dataset[selected_cols].values.tolist()

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
            "emphasis": {"focus": "series"},
            "legend": {"data": selected_cols[1:], "right": "0%", "top": "middle"},
            "media": [{
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
        }
        return config

    # Generiamo il grafico con le aree selezionate
    chart_config = crea_config_chart("Andamento delle Aree", df, selected_cols)
    ste.st_echarts(options=chart_config, key="-".join(aree_selezionate))
