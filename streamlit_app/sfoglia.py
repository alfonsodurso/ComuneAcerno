import streamlit as st
from common import filter_data

def page_sfoglia(df):
    st.header("📄 SFOGLIA")

    # **Inizializzazione session_state temporanei**
    for key, default in {
        "sfoglia_ricerca": "",
        "sfoglia_tipo_atto": "Tutti",
        "sfoglia_data_da": None,
        "sfoglia_data_a": None,
        "temp_sfoglia_ricerca": "",
        "temp_sfoglia_tipo_atto": "Tutti",
        "temp_sfoglia_data_da": None,
        "temp_sfoglia_data_a": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        st.session_state["temp_sfoglia_ricerca"] = col1.text_input("Ricerca", value=st.session_state["sfoglia_ricerca"], key="temp_sfoglia_ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        st.session_state["temp_sfoglia_tipo_atto"] = col2.selectbox("Tipologia di Atto", tipologie, key="temp_sfoglia_tipo_atto")

        col_date1, col_date2 = st.columns(2)
        st.session_state["temp_sfoglia_data_da"] = col_date1.date_input("Data inizio", st.session_state["sfoglia_data_da"], key="temp_sfoglia_data_da")
        st.session_state["temp_sfoglia_data_a"] = col_date2.date_input("Data fine", st.session_state["sfoglia_data_a"], key="temp_sfoglia_data_a")

    filtered = filter_data(df, st.session_state["sfoglia_ricerca"], st.session_state["sfoglia_tipo_atto"], st.session_state["sfoglia_data_da"], st.session_state["sfoglia_data_a"])
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return

    filtered.columns = [col.replace('_', ' ').title() for col in filtered.columns]

    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, len(filtered) - 1))

    current_pub = filtered.iloc[st.session_state.sfoglia_index]
    st.subheader(f"Pubblicazione {st.session_state.sfoglia_index + 1} di {len(filtered)}")

    for col in filtered.columns:
        if col not in ["Documento", "Allegati"]:
            st.write(f"**{col}:** {current_pub[col]}")

    col_doc, col_alla = st.columns(2)
    if "documento" in current_pub and current_pub["documento"]:
        col_doc.markdown(f"[📄 Documento Principale]( {current_pub['documento']} )", unsafe_allow_html=True)
    if "allegati" in current_pub and current_pub["allegati"]:
        col_alla.markdown(f"[📎 Allegati]( {current_pub['allegati']} )", unsafe_allow_html=True)

    col_nav1, col_nav2, _ = st.columns([1, 1, 3])
    with col_nav1:
        if st.button("◀️", use_container_width=True):
            st.session_state.sfoglia_index -= 1
    with col_nav2:
        if st.button("▶️", use_container_width=True):
            st.session_state.sfoglia_index += 1
