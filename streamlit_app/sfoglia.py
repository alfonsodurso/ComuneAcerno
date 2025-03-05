import streamlit as st
from common import filter_data

def page_sfoglia(df):
    st.header("📄 SFOGLIA")

    # **Gestione dei filtri con session_state**
    if "sfoglia_ricerca" not in st.session_state:
        st.session_state["sfoglia_ricerca"] = ""
    if "sfoglia_tipo_atto" not in st.session_state:
        st.session_state["sfoglia_tipo_atto"] = "Tutti"
    if "sfoglia_data_da" not in st.session_state:
        st.session_state["sfoglia_data_da"] = None
    if "sfoglia_data_a" not in st.session_state:
        st.session_state["sfoglia_data_a"] = None

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
            st.rerun()

        if col4.button("❌ Cancella Filtri"):
            st.session_state["sfoglia_ricerca"] = ""
            st.session_state["sfoglia_tipo_atto"] = "Tutti"
            st.session_state["sfoglia_data_da"] = None
            st.session_state["sfoglia_data_a"] = None
            st.rerun()

    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return
        
    filtered = filtered.sort_values(by=filtered.columns[0], ascending=False)
    filtered.columns = [col.replace('_', ' ').title() for col in filtered.columns]

    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, len(filtered) - 1))

    current_pub = filtered.iloc[st.session_state.sfoglia_index]
    st.subheader(f"Pubblicazione {st.session_state.sfoglia_index + 1} di {len(filtered)}")

    # **Mostra i dettagli della pubblicazione**
    for col in filtered.columns:
        st.write(f"**{col}:** {current_pub[col]}")


    # **Bottoni Avanti / Indietro sulla stessa riga, anche su mobile**
    col_nav1, col_nav2, _ = st.columns([1, 1, 3])  # Due colonne strette per i bottoni, una larga per spazio
    with col_nav1:
        if st.button("◀️", use_container_width=True):
            st.session_state.sfoglia_index -= 1
    with col_nav2:
        if st.button("▶️", use_container_width=True):
            st.session_state.sfoglia_index += 1
