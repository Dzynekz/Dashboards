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
    
    df = get_data()

    # Sidebar – wybór poziomu doświadczenia
    st.sidebar.title("Wybierz poziom doświadczenia")
    job_levels_options = df["experience_level_name"].unique().tolist()

    if "selected_levels" not in st.session_state:
        st.session_state["selected_levels"] = ["Junior", "Senior"]

    selected_levels = []
    for level in job_levels_options:
        if st.sidebar.toggle(level, level in st.session_state["selected_levels"], key=f"exp_{level}"):
            selected_levels.append(level)

    st.session_state["selected_levels"] = selected_levels

    # Sidebar - wybór poziomu umiejętności
    st.sidebar.title("Wybierz poziom umiejętności")
    skill_levels_options = df["level_name"].unique().tolist()

    if "selected_skill_levels" not in st.session_state:
        st.session_state["selected_skill_levels"] = ['Nice To Have', 'Regular', 'Advanced', 'Master']

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

    selected_fields = st.pills("Dziedziny", fields_options, selection_mode="multi")
    if not selected_fields:  # If nothing is selected, use all fields
        selected_fields = fields_options

   

    # Filtrowanie danych
    filtered_df = df[(df["experience_level_name"].isin(st.session_state["selected_levels"])) &
                     (df["level_name"].isin(st.session_state["selected_skill_levels"])) &
                     (df["field_name"].isin(selected_fields))]

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
    st.dataframe(df_skill_order)

    # Tworzenie wykresu z podziałem na poziomy zaawansowania
    bars = alt.Chart(df_skill_order).mark_bar().encode(
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

    st.altair_chart(bars + text, use_container_width=True)
