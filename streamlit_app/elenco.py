import streamlit as st
from common import filter_data

def page_sfoglia(df):
    st.header("SFOGLIA")
    st.markdown("Consulta le pubblicazioni una alla volta, dalla più recente alla meno recente.")

    col1, col2 = st.columns(2)
    ricerca = col1.text_input("🔍 Ricerca")
    tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
    tipologia_selezionata = col2.selectbox("Filtra per Tipologia di Atto", tipologie)

    col_date1, col_date2 = st.columns(2)
    data_da = col_date1.date_input("Data inizio", None, key="sfoglia_data_da")
    data_a = col_date2.date_input("Data fine", None, key="sfoglia_data_a")

    filtered = filter_data(df, ricerca, tipologia_selezionata, data_da, data_a)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata con questi filtri.")
        return

    filtered.columns = [col.replace('_', ' ').title() for col in filtered.columns]

    if "sfoglia_index" not in st.session_state:
        st.session_state.sfoglia_index = 0
    st.session_state.sfoglia_index = max(0, min(st.session_state.sfoglia_index, len(filtered) - 1))

    current_pub = filtered.iloc[st.session_state.sfoglia_index]
    st.markdown(f"### Pubblicazione {st.session_state.sfoglia_index + 1} di {len(filtered)}")
    
    with st.container():
        st.markdown("<div style='background-color: #f9f9f9; border: 1px solid #ddd; padding: 1em; border-radius: 0.5em;'>", unsafe_allow_html=True)
        for col in filtered.columns:
            st.markdown(f"**{col}:** {current_pub[col]}")
        st.markdown("</div>", unsafe_allow_html=True)

    col_nav1, col_nav2 = st.columns(2)
    if col_nav1.button("◀️ Precedente"):
        st.session_state.sfoglia_index -= 1
    if col_nav2.button("Successiva ▶️"):
        st.session_state.sfoglia_index += 1
