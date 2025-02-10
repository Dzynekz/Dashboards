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
            margin: 1rem;
        }
        .stMainBlockContainer {
            padding: 3rem;
        }
        .stColumn {
            margin-bottom: 1rem;
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;
        }
        .stColumn:hover {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        .offer-box {
            margin: 0.5rem;
            padding: 1rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;
        }
        .offer-box:hover {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    @st.cache_data
    def get_data():
        with engine.connect() as connection:
            df = pd.read_sql('''
                SELECT d.date_full, d.day_name, d.month_name, e.experience_level_name as experience_level, COUNT(j.job_offer_id) AS liczba_ofert
                FROM Job_Offers as j JOIN Dates as d ON j.date_id=d.date_id JOIN Experience_Levels as e ON j.experience_level_id=e.experience_level_id
                GROUP BY d.date_full, d.day_name, d.month_name, e.experience_level_name
                ORDER BY d.date_full ASC;
            ''', connection)
        df["date_full"] = pd.to_datetime(df["date_full"])
        return df
    
    df = get_data()

    # Sidebar – wybór poziomu doświadczenia
    st.sidebar.title("Wybierz poziom doświadczenia")
    job_levels_options = df["experience_level"].unique().tolist()

    if "selected_levels" not in st.session_state:
        st.session_state["selected_levels"] = ["Junior", "Senior"]

    selected_levels = []
    for level in job_levels_options:
        if st.sidebar.toggle(level, level in st.session_state["selected_levels"]):
            selected_levels.append(level)

    st.session_state["selected_levels"] = selected_levels

    # Filtrowanie danych na podstawie wybranego poziomu doświadczenia
    filtered_df = df[df["experience_level"].isin(st.session_state["selected_levels"])]

    # Dynamiczne metryki
    today = pd.Timestamp.today()
    offers_last_week = filtered_df[filtered_df["date_full"] >= (today - pd.Timedelta(days=1)) - pd.Timedelta(days=7)]["liczba_ofert"].sum()
    offers_last_month = filtered_df[filtered_df["date_full"] >= (today - pd.Timedelta(days=1)) - pd.Timedelta(days=30)]["liczba_ofert"].sum()
    total_offers = filtered_df["liczba_ofert"].sum()

    
    st.title("Liczba ofert")

    selected_experience_levels = ", ".join(st.session_state.get("selected_levels"))

    st.header(f"Liczba ofert na przestrzeni ostatniego czasu")

    # Wyświetlenie metryk
    #col1, col2, col3, col4 = st.columns([0.235, 0.365, 0.26, 0.14], gap="medium")
    #col1, col2, col3 = st.columns([1.5, 3, 2], gap="large")
    col1, col2, col3 = st.columns([0.235, 0.365, 0.4], gap="medium")
    with col1:
        st.metric(f"#### Liczba ofert z ostatniego tygodnia ({selected_experience_levels})", f"{offers_last_week:,}")
    with col2:
        st.metric(f"### Liczba ofert z ostatniego miesiąca ({selected_experience_levels})", f"{offers_last_month:,}")
    with col3:
        st.metric(f"##### Liczba ofert w systemie ({selected_experience_levels})", f"{total_offers:,}")

    
    

    last_7_days = today - pd.Timedelta(days=8)

    week_data = filtered_df[filtered_df["date_full"] >= last_7_days]
    week_data = week_data.groupby(["date_full", "day_name"])["liczba_ofert"].sum().reset_index()
    week_data = week_data.sort_values("date_full")
    print(week_data)
    
    ############################################
    # 🔹 Wykres słupkowy
    bars = alt.Chart(week_data).mark_bar(size=30, color='#0096c7').encode(
        x=alt.X("date_full:T", title="Data", axis=alt.Axis(labelAngle=-45), sort=None),
        y=alt.Y("liczba_ofert:Q", title="Liczba ofert")
    )

    # 🔹 Etykiety nad słupkami
    labels = alt.Chart(week_data).mark_text(
        align="center",
        baseline="bottom",
        dy=-5,  # 🔹 Przesunięcie tekstu nad słupkiem
        fontSize=12,
        fontWeight="bold"
    ).encode(
        x=alt.X("date_full:T"),
        y=alt.Y("liczba_ofert:Q"),
        text=alt.Text("liczba_ofert:Q", format=",d")  # 🔹 Formatowanie liczb (tysiące z przecinkiem)
    )

    # 🔹 Połączenie wykresu słupkowego i etykiet
    weekly_chart = (bars + labels).properties(
        title="Liczba ofert w ostatnich 7 dniach"
    ).configure(
        background='rgb(248, 249, 250)'  # Tło wykresu
    ).configure_title(
        fontSize=20
    )

   
    # Filtrowanie danych do ostatnich 30 dni
    last_30_days = today - pd.Timedelta(days=30)
    month_data = filtered_df[filtered_df["date_full"] >= last_30_days]

    # Grupowanie danych dla skumulowanego wykresu
    stacked_data = month_data.groupby(["date_full", "experience_level"])["liczba_ofert"].sum().reset_index()

    # Warstwa podświetlenia weekendów

    # Wykres słupkowy (stacked bar chart)
    stacked_chart = alt.Chart(stacked_data).mark_bar(size=15).encode(
        x=alt.X("date_full:T", title="Data", axis=alt.Axis(labelAngle=-45)),  # Oś X - data
        y=alt.Y("liczba_ofert:Q", title="Liczba ofert"),  # Oś Y - łączna liczba ofert
        color=alt.Color("experience_level:N", legend=alt.Legend(title="Poziom doświadczenia")),  # Podział na poziomy doświadczenia
        tooltip=["date_full:T", "experience_level:N", "liczba_ofert:Q"]  # Tooltip
    ).properties(
        title="Liczba ofert z ostatniego miesiąca"
    ).configure(
        background='rgb(248, 249, 250)'  # Tło wykresu
    )
    stacked_chart = stacked_chart.configure_title(
        fontSize=20
    )


    experience_data = filtered_df.groupby("experience_level")["liczba_ofert"].sum().reset_index()
    experience_data_nf = df.groupby("experience_level")["liczba_ofert"].sum().reset_index()

    # Podstawowy wykres kołowy
    base = alt.Chart(experience_data).encode(
        theta=alt.Theta("liczba_ofert:Q").stack(True),  # Stosowanie wartości
        color=alt.Color("experience_level:N", legend=None)
    )

    # Warstwa pie chart
    pie = base.mark_arc(outerRadius=120, innerRadius=50)

    # Warstwa etykiet (umieszczonych na zewnątrz)
    text = base.mark_text(radius=140, size=14, fontWeight="bold").encode(
        text=alt.Text("experience_level:N")
    )

    # Połączenie wykresu i tekstu
    pie_chart_with_labels = (pie + text).properties(
        title="Rozkład ofert według poziomu doświadczenia"
    ).configure(
        background='rgb(248, 249, 250)'
    ).configure_title(
        fontSize=20
    )


    col1, col2, col3, col4 = st.columns([0.235, 0.365, 0.26, 0.14], gap="medium")
    with st.container():
        with col1:
            st.altair_chart(weekly_chart, use_container_width=True)
        with col2: 
            st.altair_chart(stacked_chart, use_container_width=True) 
        with col3: 
            st.altair_chart(pie_chart_with_labels, use_container_width=True)
        with col4: 
            st.write("##### Liczba ofert - poziomy")
            for index, row in experience_data_nf.iterrows():
                with st.container():
                    st.markdown(f'<div class="offer-box"><b>{row["experience_level"]}</b>: {row["liczba_ofert"]:,} ofert</div>', unsafe_allow_html=True)
                    



    st.markdown("---")  # Dodaj linię oddzielającą
    st.header("Liczba ofert na przestrzeni lat")
    
    # 🔹 Tworzenie kolumny "year_month" (np. "2023-01")
    filtered_df = filtered_df.copy()  # Tworzy bezpieczną kopię, eliminując warning
    filtered_df.loc[:, "year_month"] = filtered_df["date_full"].dt.to_period("M").astype(str)

    # 🔹 Grupowanie danych miesięcznie zamiast rocznie
    monthly_data = filtered_df.groupby(["year_month", "experience_level"])["liczba_ofert"].sum().reset_index()

    # 🔹 Ustalenie niestandardowej palety kolorów
    color_palette = ["#0096c7", "#0077b6", "#48cae4", "#00b4d8", "#90e0ef", "#ADE8F4"]
    experience_levels = monthly_data["experience_level"].unique()
    color_mapping = dict(zip(experience_levels, color_palette[:len(experience_levels)]))

    # 🔹 Tworzenie wykresu z ukrytą legendą
    time_chart = alt.Chart(monthly_data).mark_line(point=True).encode(
        x=alt.X("year_month:T", title="Miesiąc", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("liczba_ofert:Q", title="Liczba ofert"),
        color=alt.Color("experience_level:N", scale=alt.Scale(domain=list(color_mapping.keys()), range=list(color_mapping.values())), legend=None)  # 🔹 Brak legendy
    ).properties(
        title="Liczba ofert na przestrzeni miesięcy"
    ).configure(
        background='rgb(248, 249, 250)'
    ).configure_title(
        fontSize=20
    )

    # 🔹 Układ kolumn (wykres + legenda)
    col1, col2 = st.columns([0.86, 0.14], gap="medium")

    with col1:
        st.altair_chart(time_chart, use_container_width=True)

    with col2:
        st.write("### Legenda")
        
        # Wyświetlenie legendy jako kolorowych znaczników
        for level, color in color_mapping.items():
            st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">'
                        f'<div style="width: 15px; height: 15px; background-color: {color}; border-radius: 50%;"></div>'
                        f'<span style="font-size: 16px;">{level}</span>'
                        f'</div>', unsafe_allow_html=True)
