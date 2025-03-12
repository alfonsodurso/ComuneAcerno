import streamlit as st
from common import filter_data

def page_sfoglia(df):
    st.header("📄 SFOGLIA")

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipo_atto = col2.selectbox("Tipologia di Atto", tipologie)

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None)
        data_a = col_date2.date_input("Data fine", None)

    # Applichiamo il filtro ai dati
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return

    # Creiamo una copia per visualizzare le colonne in formato "Title"
    filtered_display = filtered.copy()
    filtered_display.columns = [col.replace('_', ' ').title() for col in filtered_display.columns]

    # Inizializziamo l'indice di navigazione se non esiste
    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    
    # Gestiamo la navigazione
    total_items = len(filtered)
    col_nav1, col_nav2, col_nav3, col_nav4, _ = st.columns([1, 1, 1, 1, 3])
    
    with col_nav1:
        if st.button("⏪", use_container_width=True):
            st.session_state.sfoglia_index = 0
    with col_nav2:
        if st.button("◀️", use_container_width=True):
            st.session_state.sfoglia_index = max(0, st.session_state.sfoglia_index - 1)
    with col_nav3:
        if st.button("▶️", use_container_width=True):
            st.session_state.sfoglia_index = min(total_items - 1, st.session_state.sfoglia_index + 1)
    with col_nav4:
        if st.button("⏩", use_container_width=True):
            st.session_state.sfoglia_index = total_items - 1
            
    # Validazione finale dell'indice
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, total_items - 1))
    
    if total_items > 0:
        current_pub = filtered.iloc[st.session_state.sfoglia_index]
        st.subheader(f"Pubblicazione {st.session_state.sfoglia_index + 1} di {total_items}")

        # Mostriamo tutte le colonne tranne "documento" e "allegati"
        for col in filtered_display.columns:
            col_original = col.lower().replace(' ', '_')
            if col_original not in ["documento", "allegati"]:
                value = current_pub.get(col_original, "N/A")
                st.write(f"**{col}:** {value}")

        # Documento Principale
        documento = current_pub.get("documento", "")
        if documento and pd.notna(documento) and str(documento) != "N/A":
            st.markdown(f"**Documento Principale:** [Apri]({documento})")

        # Allegati
        allegati = current_pub.get("allegati", "")
        if allegati and pd.notna(allegati) and str(allegati) != "N/A":
            try:
                if isinstance(allegati, list):
                    allegati_links = allegati
                elif isinstance(allegati, str):
                    allegati_links = [link.strip() for link in allegati.split(",") if link.strip()]
                else:
                    allegati_links = [str(allegati)]
                
                if allegati_links:
                    links_md = " ".join(f"[Allegato {i+1}]({link})" for i, link in enumerate(allegati_links))
                    st.markdown(f"**Allegati:** {links_md}")
            except Exception as e:
                st.error(f"Errore nel processare gli allegati: {e}")
