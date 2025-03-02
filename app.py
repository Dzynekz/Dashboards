from sqlalchemy import create_engine, text
from dotenv import load_dotenv

import streamlit as st
st.set_page_config(layout="wide")
import liczba_ofert, zarobki, popularne_technologie, rozklad_pareto, mapa_polski



st.markdown(
    """
    <style>
        /* Stylizacja sidebar */
        section[data-testid="stSidebar"] {
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            padding: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar navigation
st.sidebar.title("Dashboard Menu")
selected_page = st.sidebar.radio("Wybierz stronę:", ["Liczba Ofert", "Zarobki", "Technologie", "Mapa Polski", 'Rozkład Pareto'])
st.sidebar.markdown("---") 

# Display the selected page
if selected_page == "Liczba Ofert":
    liczba_ofert.main()
elif selected_page == "Zarobki":
    zarobki.main()
elif selected_page == "Technologie":
    popularne_technologie.main()
elif selected_page == "Mapa Polski":
    mapa_polski.main()
elif selected_page == "Rozkład Pareto":
    rozklad_pareto.main()