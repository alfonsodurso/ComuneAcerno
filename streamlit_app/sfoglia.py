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

    # **Filtriamo i dati automaticamente**
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return

    # Manteniamo i nomi delle colonne originali per evitare problemi di accesso ai dati
    filtered_display = filtered.copy()
    filtered_display.columns = [col.replace('_', ' ').title() for col in filtered_display.columns]

    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, len(filtered) - 1))

    current_pub = filtered.iloc[st.session_state.sfoglia_index]
    st.subheader(f"Pubblicazione {st.session_state.sfoglia_index + 1} di {len(filtered)}")

    for col in filtered_display.columns:
        col_original = col.lower().replace(' ', '_')  # Recuperiamo il nome originale
        if col_original not in ["documento", "allegati"]:
            st.write(f"**{col}:** {current_pub[col_original]}")

    col_doc, col_alla = st.columns(2)
    documento = current_pub.get("documento")
    allegati = current_pub.get("allegati")

    if documento:
        col_doc.markdown(f"[\ud83d\udcdd Documento Principale]( {documento} )", unsafe_allow_html=True)
    if allegati:
        col_alla.markdown(f"[\ud83d\udcce Allegati]( {allegati} )", unsafe_allow_html=True)

    col_nav1, col_nav2, _ = st.columns([1, 1, 3])
    with col_nav1:
        if st.button("\u25c0\ufe0f", use_container_width=True):
            st.session_state.sfoglia_index -= 1
    with col_nav2:
        if st.button("\u25b6\ufe0f", use_container_width=True):
            st.session_state.sfoglia_index += 1
