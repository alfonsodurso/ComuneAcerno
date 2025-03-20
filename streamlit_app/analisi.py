import streamlit as st
import pandas as pd
import numpy as np
import streamlit_echarts as ste

# Creazione di dati di esempio (assicurarsi che TOTALE sia calcolato)
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
})
df["TOTALE"] = df.drop("data", axis=1).sum(axis=1)

# Utilizza st.multiselect per consentire la selezione multipla delle aree
opzioni = list(df.columns[1:])  # Escludiamo la colonna 'data'
aree_selezionate = st.multiselect("Seleziona le aree", opzioni, default=opzioni)

# Se nessuna area è selezionata, mostra un messaggio di avviso
if not aree_selezionate:
    st.warning("Seleziona almeno un'area per visualizzare il grafico.")
else:
    # Crea il dataset filtrato: includi la colonna "data" e le aree selezionate
    selected_cols = ["data"] + aree_selezionate

    def crea_config_chart(title: str, dataset: pd.DataFrame, selected_cols: list) -> dict:
        """
        Crea la configurazione per un grafico lineare ECharts in base alle aree selezionate.
        Se viene selezionata più di un'area (o "Tutte le Aree"), mostra la legenda.
        """
        # Converte la colonna "data" in stringhe (per evitare problemi con Timestamp)
        ds = dataset.copy()
        ds["data"] = ds["data"].dt.strftime("%d-%m-%Y")
        # Convertiamo il dataset in una lista di liste
        source = ds[selected_cols].values.tolist()

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
        # Se sono selezionate più di una area, abilita la legenda
        if len(aree_selezionate) > 1:
            config["legend"] = {
                "data": selected_cols[1:],
                "orient": "vertical",
                "right": "0%",
                "top": "middle"
            }
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

    chart_config = crea_config_chart("Andamento delle Aree", df, selected_cols)
    # Usa come chiave la concatenazione dei nomi selezionati (senza caratteri problematici)
    ste.st_echarts(options=chart_config, key="-".join(aree_selezionate))
