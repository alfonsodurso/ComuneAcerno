def display_temporal_tab(container, df: pd.DataFrame):
    """
    Visualizza i grafici temporali in un layout a schede (card layout) con lazy loading, animazioni e dimensioni responsive.
    """
    daily_data, cumulative_data = prepare_time_series_data_by_sender(df)
    
    # Prepara i dati per il calendario partendo dal dataset giornaliero
    df_calendar = daily_data.copy()
    df_calendar["data"] = pd.to_datetime(df_calendar["data"], format="%d-%m-%Y")
    total_per_day = df_calendar.groupby(df_calendar["data"].dt.date)["TOTALE"].sum().reset_index()
    total_per_day.columns = ["date", "total"]
    calendar_data = [[str(row["date"]), row["total"]] for _, row in total_per_day.iterrows()]

    # L'ordine delle colonne, come definito nella funzione di preparazione, è:
    # data, TOTALE, Area Tecnica 1, Area Tecnica 2, Area Vigilanza, Area Amministrativa, Comune di Acerno, Altri
    selected_cols = daily_data.columns.tolist()

    # Configurazioni per i grafici
    schede = {
        "andamento_giornaliero": crea_config_chart("Andamento giornaliero", daily_data, selected_cols),
        "andamento_cumulato": crea_config_chart("Andamento cumulato", cumulative_data, selected_cols),
        "heatmap_calendario": crea_config_calendar(calendar_data),
    }

    # Mappa etichette utente -> chiavi interne (semplici, senza caratteri speciali)
    tab_labels = {
        "Andamento Giornaliero": "andamento_giornaliero",
        "Andamento Cumulato": "andamento_cumulato",
        "Heatmap Calendario": "heatmap_calendario",
    }
    
    selected_label = st.radio("Seleziona il grafico", list(tab_labels.keys()), horizontal=True)
    selected_key = tab_labels[selected_label]

    # CSS per animazioni di transizione (opzionale) e per rendere il grafico responsive
    st.markdown("""
        <style>
            .echarts-container { 
                transition: opacity 0.5s ease-in-out; 
                opacity: 1;
            }
            .echarts-responsive {
                width: 100% !important;
                height: 70vh !important;  /* l'altezza è impostata al 70% dell'altezza della viewport */
            }
        </style>
        """, unsafe_allow_html=True)

    # Avvolge il componente in un container responsive
    with st.container():
        try:
            st.markdown('<div class="echarts-container echarts-responsive">', unsafe_allow_html=True)
            st_echarts(options=schede[selected_key], key=selected_key)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error("Errore durante il caricamento del grafico.")
            st.exception(e)
