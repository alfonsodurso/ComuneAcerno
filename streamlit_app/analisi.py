def display_temporal_tab(container, df):
    """
    Visualizza due grafici (giornaliero e cumulato) che mostrano l'andamento
    totale e per ciascun mittente, consentendo di selezionare quali mittenti visualizzare,
    utilizzando echarts.
    """
    # Prepara i dataset aggregati per data e mittente
    daily_dataset, cumulative_dataset, senders = prepare_time_series_data_by_sender(df)
    
    # Widget per la selezione dei mittenti
    selected_senders = container.multiselect(
        "Seleziona i mittenti da visualizzare:",
        options=senders,
        default=senders  # default: tutti i mittenti
    )
    
    # Costruisce le dimensioni da utilizzare: si mostra sempre la colonna "TOTAL"
    dimensions = ["data", "TOTAL"] + selected_senders

    # Filtra i dataset per mantenere solo le colonne selezionate
    daily_filtered = daily_dataset[dimensions]
    cumulative_filtered = cumulative_dataset[dimensions]
    
    # Crea l'opzione per il grafico giornaliero
    option_daily = {
        "animationDuration": 10000,
        "dataset": [
            {
                "id": "dataset_raw",
                "dimensions": dimensions,
                "source": daily_filtered.values.tolist(),
            }
        ],
        "title": {"text": "Andamento giornaliero"},
        "tooltip": {"order": "valueDesc", "trigger": "axis"},
        "xAxis": {"type": "category", "nameLocation": "middle"},
        "yAxis": {"name": "Pubblicazioni Giorno"},
        "grid": {"right": 140},
        "series": [
            {
                "type": "line",
                "showSymbol": False,
                "name": col,
                "encode": {"x": "data", "y": col},
                "smooth": True,
            }
            for col in dimensions[1:]  # Escludiamo la colonna 'data'
        ],
    }
    
    # Crea l'opzione per il grafico cumulato
    option_cumulative = {
        "animationDuration": 10000,
        "dataset": [
            {
                "id": "dataset_raw",
                "dimensions": dimensions,
                "source": cumulative_filtered.values.tolist(),
            }
        ],
        "title": {"text": "Andamento cumulato"},
        "tooltip": {"order": "valueDesc", "trigger": "axis"},
        "xAxis": {"type": "category", "nameLocation": "middle"},
        "yAxis": {"name": "Pubblicazioni Cumulative"},
        "grid": {"right": 140},
        "series": [
            {
                "type": "line",
                "showSymbol": False,
                "name": col,
                "encode": {"x": "data", "y": col},
                "smooth": True,
            }
            for col in dimensions[1:]
        ],
    }
    
    st.subheader("Grafico giornaliero (totale e per mittente)")
    st_echarts(options=option_daily, height="600px", key="daily_echarts")
    
    st.subheader("Grafico cumulato (totale e per mittente)")
    st_echarts(options=option_cumulative, height="600px", key="cumulative_echarts")
