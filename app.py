from sqlalchemy import create_engine, text
from dotenv import load_dotenv

import streamlit as st
import liczba_ofert
import zarobki
import popularne_technologie

st.set_page_config(layout="wide")

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
selected_page = st.sidebar.radio("Wybierz stronę:", ["Liczba Ofert", "Zarobki", "Popularne Technologie"])
st.sidebar.markdown("---") 

# Display the selected page
if selected_page == "Liczba Ofert":
    liczba_ofert.main()
elif selected_page == "Zarobki":
    zarobki.main()
elif selected_page == "Popularne Technologie":
    popularne_technologie.main()