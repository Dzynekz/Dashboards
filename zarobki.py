from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import altair as alt

# Połączenie z bazą danych
server = st.secrets["database"]["DB_SERVER"]
database = st.secrets["database"]["DB_DATABASE"]
username = st.secrets["database"]["DB_USERNAME"]
password = st.secrets["database"]["DB_PASSWORD"]
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&charset=utf8"
engine = create_engine(connection_string, use_setinputsizes=False)

def main():
    
    # Dodaj niestandardowy CSS dla zwiększenia szerokości kontenera
    st.markdown(
        """
        <style>
        body {
            font-family: 'Arial', sans-serif !important;
        }
        .main .block-container {
            max-width: 95%;  # Zwiększ szerokość kontenera do 95% ekranu
            padding: 1rem;   # Dodaj trochę odstępu wokół kontenera
        }
        .stHeading {
            margin: 1rem;
        }
        .stMainBlockContainer {
            padding: 3rem;
        }
        .stMain .stVerticalBlock:nth-child(1) > .stElementContainer:nth-child(3) > .stHeading {
            margin-left: 5%;
            margin-right: 5%;
        }
        .stVerticalBlock > .stHorizontalBlock:nth-child(4) {
            display: flex;
            flex-direction: row-reverse;
            margin-left: 5%;
            margin-right: 5%;
        }
        .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(1) .stHorizontalBlock {
            display: flex;
            flex-direction: column;
        } 
        .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock{
            display: flex;
            flex-direction: column-reverse;
        } 

        .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn .stHorizontalBlock > .stColumn {
            width: 100%;
        }
        .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock > .stColumn:nth-child(1) .stVerticalBlock {
            display:flex;
            flex-direction: row;
        }

        .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock > .stColumn:nth-child(1) .stVerticalBlock > .stElementContainer {
            width: 100%;
        }
        .stMetric {
            width: 100%;
        }
        .stMetric,
         .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn {
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;
        }

        .stMetric:hover,
         .stVerticalBlock > .stHorizontalBlock:nth-child(4) > .stColumn:hover
        {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    @st.cache_data
    def get_job_offers():
        query = '''
            SELECT j.job_offer_id, f.field_name, el.experience_level_name, om.operating_mode_name, s.salary_from, s.salary_to,
                    s.salary_currency, e.employment_type_name, c.city_name, STRING_AGG(sk.skill_name, ', ') AS skills
            FROM Job_Offers j
                JOIN Fields f ON j.field_id = f.field_id
                JOIN Experience_Levels el ON j.experience_level_id = el.experience_level_id
                JOIN Operating_Modes om ON j.operating_mode_id = om.operating_mode_id
                JOIN Job_Offers_Salaries jos ON j.job_offer_id = jos.job_offer_id
                JOIN Salaries s ON jos.salary_id = s.salary_id
                JOIN Employment_Types e ON jos.employment_type_id=e.employment_type_id
                JOIN Cities c ON j.city_id=c.city_id
                LEFT JOIN Job_Offers_Skills josk ON j.job_offer_id = josk.job_offer_id
                LEFT JOIN Skills sk ON josk.skill_id = sk.skill_id
            WHERE e.employment_type_id IN (1,2,7,6,5,4,3,20,18,25) 
                AND (salary_from is NULL OR (salary_from < 200000 AND salary_to < 200000))
            GROUP BY j.job_offer_id, f.field_name, el.experience_level_name, om.operating_mode_name, 
                    s.salary_from, s.salary_to, s.salary_currency, e.employment_type_name, c.city_name
        '''
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        
        # Definiowanie kursów walut
        currency_exchange_rates = {
            "USD": 4.2,  # Kurs wymiany USD -> PLN
            "EUR": 4.5   # Kurs wymiany EUR -> PLN
        }

        # Przeliczenie salary_from i salary_to na PLN
        df["salary_from"] = df.apply(lambda row: row["salary_from"] * currency_exchange_rates[row["salary_currency"]] 
                                    if row["salary_currency"] in currency_exchange_rates else row["salary_from"], axis=1)
        
        df["salary_to"] = df.apply(lambda row: row["salary_to"] * currency_exchange_rates[row["salary_currency"]] 
                                if row["salary_currency"] in currency_exchange_rates else row["salary_to"], axis=1)
        
        # Zamiana waluty na PLN
        df["salary_currency"] = "PLN"

        # Usunięcie wierszy, w których wynagrodzenie przekracza 200 000 PLN
        df = df[(df["salary_from"] < 200000) & (df["salary_to"] < 200000)]
        
        return df

    @st.cache_data
    def get_salaries_info():
        query = '''
            SELECT COUNT(*) AS total_offers,
                SUM(CASE WHEN s.salary_from IS NOT NULL OR s.salary_to IS NOT NULL THEN 1 ELSE 0 END) AS offers_with_salary,
                SUM(CASE WHEN s.salary_from IS NULL AND s.salary_to IS NULL THEN 1 ELSE 0 END) AS offers_without_salary
            FROM Job_Offers_Salaries jos
            LEFT JOIN Salaries s ON jos.salary_id = s.salary_id;
        '''
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df

    @st.cache_data
    def get_salaries_info2():
        query = '''         
            SELECT 
                COUNT(*) AS total_offers,
                SUM(CASE WHEN liczba_typow_zatrudnienia = 1 THEN 1 ELSE 0 END) AS one_employment_type,
                SUM(CASE WHEN liczba_typow_zatrudnienia >= 2 THEN 1 ELSE 0 END) AS two_employments_types
            FROM (
                SELECT job_offer_id, COUNT(DISTINCT employment_type_id) AS liczba_typow_zatrudnienia
                FROM Job_Offers_Salaries
                GROUP BY job_offer_id
            ) AS subquery;
        '''
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df
    
    def get_skills():
        query = '''
            SELECT skill_name FROM Skills
        '''
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df["skill_name"].tolist()

     # **Normalizacja typów umowy**
    
    employment_mapping = {
        "B2B": "B2B",
        "b2b": "B2B",
        "Net/month - B2B": "B2B",
        "Net per month - B2B": "B2B",
        "Employment Type B2B": "B2B",
        "permanent": "UoP",
        "Permanent": "UoP",
        "Gross/month - Permanent": "UoP",
        "Employment Type Permanent": "UoP",
        "mandate_contract": "Umowa Zlecenie"
    }
    
    # Pobranie ofert pracy
    job_offers = get_job_offers()
    job_offers["employment_type_name"] = job_offers["employment_type_name"].replace(employment_mapping)


    salaries_info = get_salaries_info()
    # Wyciągnięcie wartości z dataframe
    total_offers = salaries_info.iloc[0]["total_offers"]
    offers_with_salary = salaries_info.iloc[0]["offers_with_salary"]

    # Obliczenie procentu ofert z wynagrodzeniem
    salary_percentage = (offers_with_salary / total_offers) * 100 if total_offers > 0 else 0

    employment_types = get_salaries_info2()
    total_offers_empl = employment_types.iloc[0]["total_offers"]
    offers_with_2empl = employment_types.iloc[0]["two_employments_types"]
    employment_percentage = (offers_with_2empl / total_offers_empl) * 100 if total_offers_empl > 0 else 0


    # Dodanie informacji do sidebaru
    st.sidebar.subheader("📊 Statystyki ofert")
    st.sidebar.write(f"- {salary_percentage:.2f}% ofert zawiera informacje o wynagrodzeniu")
    st.sidebar.write(f"- {employment_percentage:.2f}% ofert zawiera przynajmniej dwa typy zatrudnienia do wyboru")

    

   
    # Tytuł dashboardu
    st.title("Dashboard Zarobków IT: Filtruj i Analizuj Oferty")

    # **Filtry**

    col1, col2 = st.columns([1,4], gap="medium")

    with col1:
        col11, col12, col13, col14, col15, col16 = st.columns(6)

        with col11:
            st.write("### Filtry:")
        with col12:
            # Wybór dziedziny
            field_options = ["Wybierz dziedzinę..."] + sorted(job_offers["field_name"].unique().tolist())
            selected_field = st.selectbox("📌 Wybierz dziedzinę:", field_options)

        with col13:
            # Wybór trybu pracy
            mode_options = ["Wybierz tryb pracy..."] + sorted(job_offers["operating_mode_name"].unique().tolist())
            selected_mode = st.selectbox("🏢 Wybierz tryb pracy:", mode_options)

        with col14:
            # Wybór poziomu doświadczenia
            experience_options = ["Wybierz poziom doświadczenia..."] + sorted(job_offers["experience_level_name"].unique().tolist())
            selected_experience = st.selectbox("🎓 Wybierz poziom doświadczenia:", experience_options)

        with col15:
            # Wybór poziomu doświadczenia
            cities_options = ["Wybierz miasto..."] + sorted(["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Poznań", "Katowice", "Łódź", "Gdynia", "Gliwice", "Szczecin"])
            selected_cities = st.selectbox("🏙️ Wybierz miasto:", cities_options)
    
        with col16:
            def reset_skill_choose():
                st.session_state.skill_selection = 'Wybierz umiejętność...'

            skills_list = get_skills()
            skills_list.insert(0, "Wybierz umiejętność...")  # Placeholder
            

            # **Inicjalizacja session_state dla umiejętności**
            if "selected_skills" not in st.session_state:
                st.session_state.selected_skills = []

            # **Limit wyboru umiejętności**
            MAX_SKILLS = 5

            # **Wybór umiejętności tylko jeśli limit nie został przekroczony**
            if len(st.session_state.selected_skills) < MAX_SKILLS:
                selected_skill = st.selectbox("🛠 Wybierz umiejętności (max 5):", skills_list, key='skill_selection')

                # **Dodanie umiejętności do listy, jeśli nie jest placeholderem i nie została już wybrana**
                if selected_skill and selected_skill != "Wybierz umiejętność..." and selected_skill not in st.session_state.selected_skills:
                    st.session_state.selected_skills.append(selected_skill)
                    st.rerun()  # Odświeżenie UI po dodaniu nowej umiejętności

            def reset_skill_choose():
                st.session_state.skill_selection = 'Wybierz umiejętność...'

            # **Stylizacja wybranych umiejętności**
            st.write("#### Wybrane umiejętności:")

            # **Obsługa usuwania umiejętności**
            skill_to_remove = None

            for skill in st.session_state.selected_skills:
                if st.button(f"❌ {skill}", key=f"remove_{skill}", on_click=reset_skill_choose):
                    skill_to_remove = skill  # Zapisujemy umiejętność do usunięcia

            # **Usunięcie umiejętności po pętli**
            if skill_to_remove:
                st.session_state.selected_skills.remove(skill_to_remove)
                st.rerun()  # Odświeżenie UI po usunięciu umiejętności

    # **Filtrowanie danych według wybranych filtrów**
    filtered_offers = job_offers.copy()

    if selected_field != "Wybierz dziedzinę...":
        filtered_offers = filtered_offers[filtered_offers["field_name"] == selected_field]
    if selected_mode != "Wybierz tryb pracy...":
        filtered_offers = filtered_offers[filtered_offers["operating_mode_name"] == selected_mode]
    if selected_experience != "Wybierz poziom doświadczenia...":
        filtered_offers = filtered_offers[filtered_offers["experience_level_name"] == selected_experience]
    if selected_cities != "Wybierz miasto...":
        filtered_offers = filtered_offers[filtered_offers["city_name"] == selected_cities]
    # **Filtrowanie po umiejętnościach**
    if st.session_state.selected_skills:
        for skill in st.session_state.selected_skills:
            filtered_offers = filtered_offers[filtered_offers["skills"].apply(lambda x: skill in x)]

    # **Obliczenie średnich zarobków dla każdego typu umowy**
    salary_means = (
        filtered_offers.groupby("employment_type_name")
        .agg({"salary_from": "mean", "salary_to": "mean"})
        .rename(columns={"salary_from": "Min Salary", "salary_to": "Max Salary"})
    ).reset_index()


    with col2: # Całe kolumn 2 jako blok nie sam wykres
        col21, col22, col23 = st.columns(3)

        if salary_means.empty:
            st.write("❌ Brak ofert spełniających wybrane kryteria.")
            
            # Pusty wykres Altair
            empty_chart = alt.Chart(pd.DataFrame({"employment_type_name": [], "Salary": []})).mark_bar()
            st.altair_chart(empty_chart, use_container_width=True)
            
        else:

            # **Obliczenie liczby ofert dla każdego typu umowy**
            employment_counts = filtered_offers["employment_type_name"].value_counts().reset_index()
            employment_counts.columns = ["Typ umowy", "Liczba ofert"]

            employment_counts = employment_counts.sort_values(by="Typ umowy")

            with col21:
                # **Wyświetlenie liczby ofert dla każdego typu umowy**
                for index, row in employment_counts.iterrows():
                    st.metric(label=row["Typ umowy"], value=row["Liczba ofert"])
            
            filtered_offers["salary_avg"] = (filtered_offers["salary_from"] + filtered_offers["salary_to"]) / 2
            # Przekształcenie danych: każda oferta staje się dwoma rekordami (salary_from, salary_to)
            long_salaries = filtered_offers.melt(id_vars=["employment_type_name"],
                                                value_vars=["salary_from", "salary_to"],
                                                var_name="Salary Type",
                                                value_name="Salary")

            # Dodanie wartości średniej jako osobnego punktu
            average_salaries = filtered_offers[["employment_type_name", "salary_avg"]].rename(columns={"salary_avg": "Salary"})
            average_salaries["Salary Type"] = "Średnia"

            # Połączenie przekształconych danych
            final_data = pd.concat([long_salaries, average_salaries])

            with col22:
                st.write("### Oferty pasujące do wymagań:")

            with col23:
                # Wykres pudełkowy
                box_plot = alt.Chart(final_data).mark_boxplot(size=150, extent="min-max").encode(
                    x=alt.X("employment_type_name:N", title="Typ umowy"),
                    y=alt.Y("Salary:Q", title="Zarobki"),
                    color=alt.Color("employment_type_name:N", legend=None),
                    tooltip=["employment_type_name", "Salary"]
                ).properties(
                    height=700
                )

                box_plot = box_plot.configure(
                    background='rgb(248, 249, 250)'
                ).properties(
                    title="Rozkład zarobków dla B2B, UoP i umowy zlecenia"
                ).configure_title(
                    fontSize=20
                )

                st.altair_chart(box_plot, use_container_width=True)





