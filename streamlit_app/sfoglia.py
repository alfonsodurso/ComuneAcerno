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

    # Filtriamo i dati automaticamente
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return

    # Creiamo una copia per visualizzare le colonne con titoli leggibili
    filtered_display = filtered.copy()
    filtered_display.columns = [col.replace('_', ' ').title() for col in filtered_display.columns]

    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, len(filtered) - 1))

    current_pub = filtered.iloc[st.session_state.sfoglia_index]
    st.subheader(f"Pubblicazione {st.session_state.sfoglia_index + 1} di {len(filtered)}")

    # Mostriamo tutte le colonne tranne "documento" e "allegati"
    for col in filtered_display.columns:
        col_original = col.lower().replace(' ', '_')
        if col_original not in ["documento", "allegati"]:
            st.write(f"**{col}:** {current_pub[col_original]}")

    # Documento Principale: Mostriamo un solo link con il testo "Apri Documento"
    documento = current_pub.get("documento")
    if documento and documento != "N/A":
        doc_link = documento[0] if isinstance(documento, list) else documento
        st.markdown(f"**Documento Principale:** [Apri Documento]({doc_link})", unsafe_allow_html=True)

    # Allegati: Mostriamo ogni link con il testo "Apri Allegato X"
    allegati = current_pub.get("allegati")
    if allegati and allegati != "N/A":
        allegati_links = allegati if isinstance(allegati, list) else [link.strip() for link in allegati.split(",") if link.strip()]
        if allegati_links:
            att_links_md = " ".join([f"[Apri Allegato {i+1}]({link})" for i, link in enumerate(allegati_links)])
            st.markdown(f"**Allegati:** {att_links_md}", unsafe_allow_html=True)

    # Navigazione tra le pubblicazioni
    col_nav1, col_nav2, _ = st.columns([1, 1, 3])
    with col_nav1:
        if st.button("◀️", use_container_width=True):
            st.session_state.sfoglia_index -= 1
    with col_nav2:
        if st.button("▶️", use_container_width=True):
            st.session_state.sfoglia_index += 1

    col_nav3, col_nav4, _ = st.columns([1, 1, 3])
    with col_nav3:
        if st.button("⏪", use_container_width=True):
            st.session_state.sfoglia_index = 0
    with col_nav4:
        if st.button("⏩", use_container_width=True):
            st.session_state.sfoglia_index = len(filtered) - 1
