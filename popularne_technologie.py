from sqlalchemy import create_engine, text
import streamlit as st
import pandas as pd
import altair as alt

server = st.secrets["database"]["DB_SERVER"]
database = st.secrets["database"]["DB_DATABASE"]
username = st.secrets["database"]["DB_USERNAME"]
password = st.secrets["database"]["DB_PASSWORD"]
# Tworzenie łańcucha połączenia z bazą danych
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&charset=utf8"
# Tworzenie silnika połączenia
engine = create_engine(connection_string, use_setinputsizes=False) # https://github.com/sqlalchemy/sqlalchemy/issues/8681
 


def main():
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 95%;
            padding: 1rem;  
        }
        .stHeading {
            margin-bottom: 1rem;
            margin-left: 5%;
            margin-right: 5%;
        }
        .stMainBlockContainer {
            padding: 3rem;  
        }

        .stMain > .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
            margin-bottom: 1.5rem;
            margin-left: 5%;
            margin-right: 5%;
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;
        }

        .stMain > .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"]:hover
        {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        .st-key-plot > .stElementContainer:first-of-type 
        {
            margin: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    @st.cache_data
    def get_data():
        with engine.connect() as connection:
             df = pd.read_sql('''
                SELECT d.date_full, f.field_name, s.skill_name, l.level_name, el.experience_level_name, COUNT(jo.job_offer_id) as 'liczba_ofert'
                FROM Fields as f JOIN Job_Offers as jo on f.field_id=jo.field_id
                    JOIN Job_Offers_Skills as jos on jos.job_offer_id=jo.job_offer_id
                    JOIN Skills as s on s.skill_id=jos.skill_id
                    JOIN Levels as l on l.level_id=jos.level_id
                    JOIN Experience_Levels as el on el.experience_level_id=jo.experience_level_id
                    JOIN Dates as d on d.date_id = jo.date_id
                GROUP BY d.date_full, f.field_name, s.skill_name, l.level_name, el.experience_level_name
            ''', connection)
        df["date_full"] = pd.to_datetime(df["date_full"])
        return df
    @st.cache_data
    def get_data2():
        with engine.connect() as connection:
             df = pd.read_sql('''
                SELECT d.date_full, f.field_name, el.experience_level_name, COUNT(jo.job_offer_id) as 'liczba_ofert'
                FROM Fields as f JOIN Job_Offers as jo on f.field_id=jo.field_id
                    JOIN Experience_Levels as el on el.experience_level_id=jo.experience_level_id
                    JOIN Dates as d on d.date_id = jo.date_id
                GROUP BY d.date_full, f.field_name, el.experience_level_name
            ''', connection)
        df["date_full"] = pd.to_datetime(df["date_full"])
        return df
    @st.cache_data
    def get_data3():
        with engine.connect() as connection:
             df = pd.read_sql('''
                SELECT f.field_name, s.skill_name, COUNT(jo.job_offer_id) as 'liczba_ofert'
                FROM Fields as f JOIN Job_Offers as jo on f.field_id=jo.field_id
                    JOIN Job_Offers_Skills as jos on jos.job_offer_id=jo.job_offer_id
                    JOIN Skills as s on s.skill_id=jos.skill_id
                GROUP BY f.field_name, s.skill_name
            ''', connection)
        return df
    
    
    df = get_data()
    df2 = get_data2()
    df3 = get_data3()

    # Sidebar – wybór poziomu doświadczenia
    st.sidebar.title("Wybierz poziom doświadczenia")
    job_levels_options = ['Junior','Mid','Senior','C-level']

    if "selected_levels" not in st.session_state:
        st.session_state["selected_levels"] = ['Junior', 'Mid', 'Senior']

    selected_levels = []
    for level in job_levels_options:
        if st.sidebar.toggle(level, level in st.session_state["selected_levels"], key=f"exp_{level}"):
            selected_levels.append(level)

    st.session_state["selected_levels"] = selected_levels

    # Sidebar - wybór poziomu umiejętności
    st.sidebar.title("Wybierz poziom umiejętności")
    skill_levels_options = ['Nice To Have','Junior','Regular','Advanced','Master']

    if "selected_skill_levels" not in st.session_state:
        st.session_state["selected_skill_levels"] = ['Nice To Have', 'Junior', 'Regular', 'Advanced', 'Master']

    selected_skill_levels = []
    for level in skill_levels_options:
        if st.sidebar.toggle(level, level in st.session_state["selected_skill_levels"], key=f"skill_{level}"):
            selected_skill_levels.append(level)

    st.session_state["selected_skill_levels"] = selected_skill_levels




    # Wybór dziedzin obok wykresu za pomocą przycisków
    st.title("Najpopularniejsze technologie")
    st.header("Top 20 technologii w wybranych dziedzinach z podziałem na poziomy zaawansowania")


    fields_options = df["field_name"].unique().tolist()
    selected_fields = []

    with st.container():
        selected_fields = st.pills("Dziedziny", fields_options, selection_mode="multi")
        if not selected_fields:  # If nothing is selected, use all fields
            selected_fields = fields_options

    # Filtrowanie danych
    filtered_df = df[(df["experience_level_name"].isin(st.session_state["selected_levels"])) &
                     (df["level_name"].isin(st.session_state["selected_skill_levels"])) &
                     (df["field_name"].isin(selected_fields))]
    
    filtered_df2 = df2[(df2["experience_level_name"].isin(st.session_state["selected_levels"])) &
                     (df2["field_name"].isin(selected_fields))]
    
    offers = filtered_df2["liczba_ofert"].sum()

    # Grupowanie danych i wybór top 20 technologii ogólnie
    top_20_skills = (filtered_df.groupby("skill_name")
                     .agg({"liczba_ofert": "sum"})
                     .reset_index()
                     .sort_values("liczba_ofert", ascending=False)
                     .head(20)["skill_name"].tolist())

    # Filtrowanie danych dla top 20 technologii z podziałem na poziomy zaawansowania
    top_20_technologies = filtered_df[filtered_df["skill_name"].isin(top_20_skills)]

    df_skill_order = top_20_technologies.groupby(['skill_name']).agg(
        total_offers=('liczba_ofert', 'sum')
    ).reset_index().sort_values('total_offers', ascending=False)

    skill_order = df_skill_order['skill_name'].tolist()
    level_order= ['Nice To Have', 'Junior', 'Regular', 'Advanced', 'Master']

    # Grupowanie i sortowanie
    df_skill_order = top_20_technologies.groupby(['skill_name', 'level_name']).agg(
        total_offers=('liczba_ofert', 'sum')
    ).reset_index()
    
    # Create a categorical type for skill_name and level_name with the desired order
    df_skill_order['skill_name'] = pd.Categorical(df_skill_order['skill_name'], categories=skill_order, ordered=True)
    df_skill_order['level_name'] = pd.Categorical(df_skill_order['level_name'], categories=level_order, ordered=True)
    
    # Sort by both columns
    df_skill_order = df_skill_order.sort_values(['skill_name', 'level_name'])
    # Calculate cumulative positions for text labels
    df_skill_order['text_position'] = df_skill_order.groupby('skill_name')['total_offers'].cumsum() - (df_skill_order['total_offers'] / 2)
    #st.dataframe(df_skill_order)

    # Tworzenie wykresu z podziałem na poziomy zaawansowania
    bars = alt.Chart(df_skill_order, height=800).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X('sum(total_offers):Q', title='Liczba ofert').stack('zero'),
        y=alt.Y('skill_name:N', title='Technologia', sort=skill_order),
        color=alt.Color('level_name:N', title='Poziom zaawansowania', sort=level_order),
        order=alt.Order('color_level_name_sort_index:Q')
    )

    text = alt.Chart(df_skill_order).mark_text(align='center',baseline='middle', color='white').encode(
        x='text_position',
        y=alt.Y('skill_name:N', sort=skill_order),
        detail='level_name:N',
        text=alt.Text('sum(total_offers):Q', format='.0f')
    )
    
    chart = (bars + text).properties(
        title="Najczęstsze wymagania w wybranych ofertach:"
    ).configure(
        background='rgb(248, 249, 250)' 
    )
    with st.container(key='plot'):
        st.metric(f"Liczba ofert odpowiadających kryteriom:", f"{offers}")
        st.altair_chart(chart, use_container_width=True)

