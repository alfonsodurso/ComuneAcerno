import streamlit as st
from common import filter_data

def reset_sfoglia_filters():
    """Resetta i filtri della sezione SFOGLIA"""
    st.session_state["sfoglia_ricerca"] = ""
    st.session_state["sfoglia_tipo_atto"] = "Tutti"
    st.session_state["sfoglia_data_da"] = None
    st.session_state["sfoglia_data_a"] = None
    st.rerun()  # ✅ Forza il refresh della pagina per aggiornare i filtri

def page_sfoglia(df):
    st.header("📄 SFOGLIA")

    # **Inizializzazione session_state**
    for key, default in {
        "sfoglia_ricerca": "",
        "sfoglia_tipo_atto": "Tutti",
        "sfoglia_data_da": None,
        "sfoglia_data_a": None
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca", value=st.session_state["sfoglia_ricerca"], key="sfoglia_ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipo_atto = col2.selectbox("Tipologia di Atto", tipologie, key="sfoglia_tipo_atto")

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", st.session_state["sfoglia_data_da"], key="sfoglia_data_da")
        data_a = col_date2.date_input("Data fine", st.session_state["sfoglia_data_a"], key="sfoglia_data_a")

        col3, col4 = st.columns(2)
        if col3.button("✅ Applica Filtro"):
            st.session_state["sfoglia_ricerca"] = ricerca
            st.session_state["sfoglia_tipo_atto"] = tipo_atto
            st.session_state["sfoglia_data_da"] = data_da
            st.session_state["sfoglia_data_a"] = data_a
            st.rerun()  # ✅ Applica i filtri e aggiorna la pagina

        if col4.button("❌ Cancella Filtri", on_click=reset_sfoglia_filters):  # ✅ Usa un callback per evitare errori
            pass

    filtered = filter_data(df, ricerca, tipo_att
