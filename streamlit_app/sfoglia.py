import streamlit as st
import pandas as pd
import ast  # Per convertire stringhe JSON in liste Python

from common import filter_data

def page_sfoglia(df):
    st.header("📖 SFOGLIA PUBBLICAZIONI")

    with st.expander("🔍 Filtri di Ricerca"):
        col1, col2 = st.columns(2)
        ricerca = col1.text_input("Ricerca")
        tipologie = ["Tutti"] + sorted(df["tipo_atto"].dropna().unique().tolist()) if "tipo_atto" in df.columns else ["Tutti"]
        tipo_atto = col2.selectbox("Tipologia di Atto", tipologie)

        col_date1, col_date2 = st.columns(2)
        data_da = col_date1.date_input("Data inizio", None)
        data_a = col_date2.date_input("Data fine", None)

    # **Filtriamo i dati**
    filtered = filter_data(df, ricerca, tipo_atto, data_da, data_a)
    filtered = filtered.sort_values("numero_pubblicazione", ascending=False)

    if filtered.empty:
        st.info("Nessuna pubblicazione trovata.")
        return

    # Creiamo uno stato per la navigazione
    if "index_sfoglia" not in st.session_state:
        st.session_state.index_sfoglia = 0

    # Assicuriamoci che l'indice non superi i limiti
    st.session_state.index_sfoglia = max(0, min(st.session_state.index_sfoglia, len(filtered) - 1))

    # Recuperiamo la pubblicazione corrente
    current_index = st.session_state.index_sfoglia
    current_pub = filtered.iloc[current_index]

    # Visualizzazione della pubblicazione
    st.write(f"**Pubblicazione {current_index + 1} di {len(filtered)}**\n")
    st.write(f"**Numero Pubblicazione:** {current_pub.get('numero_pubblicazione', 'N/A')}")
    st.write(f"**Mittente:** {current_pub.get('mittente', 'N/A')}")
    st.write(f"**Tipo Atto:** {current_pub.get('tipo_atto', 'N/A')}")
    st.write(f"**Registro Generale:** {current_pub.get('registro_generale', 'N/A')}")
    st.write(f"**Data Registro Generale:** {current_pub.get('data_registro_generale', 'N/A')}")
    st.write(f"**Oggetto Atto:** {current_pub.get('oggetto_atto', 'N/A')}")
    st.write(f"**Data Inizio Pubblicazione:** {current_pub.get('data_inizio_pubblicazione', 'N/A')}")
    st.write(f"**Data Fine Pubblicazione:** {current_pub.get('data_fine_pubblicazione', 'N/A')}")

    # Documento Principale
    documento = current_pub.get("documento")
    if pd.notna(documento) and documento:
        st.write(f"📄 **Documento Principale:** [🔗 Link]({documento})")

    # **Mostra gli allegati, se presenti**
    allegati = current_pub.get("allegati")

    if allegati and pd.notna(allegati):
        try:
            if isinstance(allegati, str):  # Se è una stringa (JSON salvato come testo)
                allegati_list = ast.literal_eval(allegati)
            else:
                allegati_list = allegati  # Se è già una lista
        except (ValueError, SyntaxError):
            allegati_list = []

        if isinstance(allegati_list, list) and allegati_list:
            st.write("📎 **Allegati:**")
            for i, allegato in enumerate(allegati_list, start=1):
                st.write(f"🔗 [Allegato {i}]({allegato})")

    # **Navigazione tra le pubblicazioni**
    col_nav1, col_nav2 = st.columns([1, 1])
    
    if col_nav1.button("⬅️ Indietro"):
        if st.session_state.index_sfoglia > 0:
            st.session_state.index_sfoglia -= 1
            st.experimental_rerun()

    if col_nav2.button("➡️ Avanti"):
        if st.session_state.index_sfoglia < len(filtered) - 1:
            st.session_state.index_sfoglia += 1
            st.experimental_rerun()
