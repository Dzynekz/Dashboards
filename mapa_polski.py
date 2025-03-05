import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import numpy as np
import webbrowser
from sqlalchemy import create_engine
from streamlit.components.v1 import html

# 🔹 Połączenie z bazą danych
server = st.secrets["database"]["DB_SERVER"]
database = st.secrets["database"]["DB_DATABASE"]
username = st.secrets["database"]["DB_USERNAME"]
password = st.secrets["database"]["DB_PASSWORD"]
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&charset=utf8"
engine = create_engine(connection_string, use_setinputsizes=False)

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
        [data-testid="stPageLink-NavLink"] {
            border: 2px solid rgba(49, 51, 63, 0.2);
            border-radius: 10px;    
            background-color: rgb(255, 255, 255);
            transition: border-color 0.3s ease, transform 0.3s ease-in-out; 
        }
        [data-testid="stPageLink-NavLink"]:hover {
            border-color: #0096c7;
            background-color: rgb(255, 255, 255);
            color: #0096c7;
            transform: translateY(-5px);
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5),
         .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) {
            margin-left: 5%;
            margin-right: 5%;
            margin-bottom: 1rem;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(1) {
            min-width:650px;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(2) {
            min-width:450px;
        }

        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7),
         .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(1) .stHorizontalBlock {
            display:flex;
            flex-direction: column;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(1) .stHorizontalBlock > .stColumn {
            width: 100%;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn,
         .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(2) .stHorizontalBlock > .stColumn {
            width: 100%;
            heigth: 90%;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(1) {
            width: 10rem;
        }

        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(2) .stHorizontalBlock {
            display: flex;
            flex-direction: column;
            justify-contet: flex-start;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(2) .stHorizontalBlock > div:nth-child(1) {
            order: 2;
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(2) .stHorizontalBlock > div:nth-child(2) {
            order: 3; 
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) > .stColumn:nth-child(2) .stHorizontalBlock > div:nth-child(3) {
            order: 1; 
        }

        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn,
         .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7) {
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;    
        }
        .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(5) > .stColumn:hover,
         .stMainBlockContainer > div[data-testid="stVerticalBlockBorderWrapper"] .stVerticalBlock:nth-child(1) > .stHorizontalBlock:nth-child(7):hover {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    @st.cache_data
    def get_data_woj():
        """ Pobiera dane o liczbie ofert pracy z SQL """
        with engine.connect() as connection:
            df = pd.read_sql('''
                SELECT p.province_name, COUNT(j.job_offer_id) AS liczba_ofert
                FROM Districts AS di JOIN Provinces AS p ON di.province_id = p.province_id
				LEFT JOIN Cities AS c ON di.district_id = c.district_id
				LEFT JOIN Job_Offers AS j ON c.city_id = j.city_id
				LEFT JOIN Experience_Levels AS e ON j.experience_level_id = e.experience_level_id
				LEFT JOIN Dates AS d ON j.date_id = d.date_id
                GROUP BY p.province_name
            ''', connection)
        return df
    
    @st.cache_data
    def get_data_pow():
        """ Pobiera dane o liczbie ofert pracy z SQL """
        with engine.connect() as connection:
            df = pd.read_sql('''
                SELECT di.district_id_gus, COALESCE(COUNT(j.job_offer_id), 0) AS liczba_ofert
                FROM Districts AS di JOIN Provinces AS p ON di.province_id = p.province_id
				LEFT JOIN Cities AS c ON di.district_id = c.district_id
				LEFT JOIN Job_Offers AS j ON c.city_id = j.city_id
				LEFT JOIN Experience_Levels AS e ON j.experience_level_id = e.experience_level_id
				LEFT JOIN Dates AS d ON j.date_id = d.date_id
                GROUP BY di.district_id_gus;
            ''', connection)
        return df

    @st.cache_data
    def get_data_cities():
        """ Pobiera dane o liczbie ofert pracy z SQL """
        with engine.connect() as connection:
            df = pd.read_sql('''
                SELECT c.city_name, COUNT(jo.job_offer_id) as liczba_ofert
                FROM Job_Offers as jo JOIN Cities as c on jo.city_id=c.city_id
                WHERE c.is_polish = 1
                GROUP BY c.city_name
            ''', connection)
        return df

    @st.cache_data
    def get_data_top5():
        with engine.connect() as connection:
            df = pd.read_sql('''
                SELECT jo.job_offer_id, jo.job_title, jo.job_offer_name, f.field_name, jo.latitude, jo.longitude, d.date_full, c.city_name, co.company_name,
                        ((COALESCE(s.salary_from, 0) + COALESCE(s.salary_to, 0)) / 2) as salary
                FROM Job_Offers as jo JOIN Cities as c on jo.city_id=c.city_id
                JOIN Dates as d on jo.date_id=d.date_id
                JOIN Fields as f on jo.field_id=f.field_id
                JOIN Job_Offers_Salaries as jos on jos.job_offer_id=jo.job_offer_id
                JOIN Salaries as s on jos.salary_id=s.salary_id
                JOIN Companies as co on jo.company_id=co.company_id
                WHERE (city_name = 'Warszawa' OR city_name = 'Wrocław' OR city_name = 'Kraków' OR city_name = 'Gdańsk' OR city_name = 'Poznań') 
                        AND (jo.latitude is not NULL) AND (jo.latitude is not NULL)
            ''', connection)
        return df
    

    df_woj = get_data_woj()

    df_pow = get_data_pow()
    def format_values(val):
        val1, val2 = val.split("_")  # Rozdzielamy wartości
        val1 = str(val1) if int(val1) >= 10 else '0' + str(val1)
        val2 = str(val2) if int(val2) >= 10 else '0' + str(val2)
        return val1 + val2  # Łączymy obie wartości
    df_pow['formatted'] = df_pow['district_id_gus'].apply(format_values)

    # Odczytanie pliku JSON
    geojson_path_woj = "wojewodztwa/woj.json"
    with open(geojson_path_woj, "r", encoding="utf-8") as f:
        geojson_data_woj = json.load(f)
    geo_df_woj = gpd.GeoDataFrame.from_features(geojson_data_woj["features"])
    gdf_woj = geo_df_woj.merge(df_woj, left_on="NAME_1", right_on="province_name").set_index("NAME_1")

    # Tworzenie mapy choropleth
    fig_woj = px.choropleth(gdf_woj,
                        geojson=gdf_woj.geometry,
                        locations=gdf_woj.index,
                        color="liczba_ofert",
                        projection="mercator")
    fig_woj.update_geos(fitbounds="locations", visible=False)
    fig_woj.update_layout(
        coloraxis_colorbar=dict(
            x=0.85,  # Przesuwa legendę bliżej mapy (zmniejszaj wartość, jeśli nadal za daleko)
        )
    )
    fig_woj.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),  # Usuwa wszystkie marginesy
        paper_bgcolor='rgb(248, 249, 250)',  # Zmienia kolor całego tła
        geo=dict(
            bgcolor='rgb(248, 249, 250)'  # Zmienia kolor samego obszaru mapy
        )
    )



    # Odczytanie pliku JSON
    geojson_path_pow = "powiaty/pow.json"
    with open(geojson_path_pow, "r", encoding="utf-8") as f:
        geojson_data_pow = json.load(f)
    geo_df_pow = gpd.GeoDataFrame.from_features(geojson_data_pow["features"])
    gdf_pow = geo_df_pow.merge(df_pow, left_on="CC_2", right_on="formatted").set_index("NAME_2")

    # Tworzenie mapy choropleth
    fig_pow = px.choropleth(gdf_pow,
                        geojson=gdf_pow.geometry,
                        locations=gdf_pow.index,
                        color="liczba_ofert",
                        projection="mercator")
    fig_pow.update_geos(fitbounds="locations", visible=False)
    fig_pow.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),  # Usuwa wszystkie marginesy
        paper_bgcolor='rgb(248, 249, 250)',  # Zmienia kolor całego tła
        geo=dict(
            bgcolor='rgb(248, 249, 250)'  # Zmienia kolor samego obszaru mapy
        )
    )

    df_cities = get_data_cities()
    cities_cords = pd.read_csv("cities/cities_z_koordynatami.csv")
    df_cities = df_cities.merge(cities_cords, left_on="city_name", right_on='city_name')
    fig_cities = px.scatter_map(df_cities, lat='latitude', lon='longitude', zoom=4, size='liczba_ofert',
                        color_continuous_scale=px.colors.cyclical.IceFire, size_max=40,
                        title="Rozmieszczenie liczby ofert w miastach",
                        height=500)  # Dodano wysokość wykresu
    fig_cities.update_layout(
        margin=dict(l=0, r=0, t=25, b=0),  # Usuwa wszystkie marginesy
        paper_bgcolor="rgba(0,0,0,0)",  # Usuwa tło wokół mapy
        plot_bgcolor="rgba(0,0,0,0)",  # Usuwa tło samej mapy
    )

    st.title("Dane na mapie")

    st.header(f"Rozmieszczenie ofert w Polsce")

    col1, col2= st.columns(2, gap="medium")
    with col1: 
        col12, col22 = st.columns(2)
        with col12:
            selected_chart = st.radio("Wybierz poziom agregacji:", ["Województwa", "Powiaty"], horizontal=True)
        with col22:
            if selected_chart == "Województwa":
                st.plotly_chart(fig_woj, use_container_width=True)
            else:
                st.plotly_chart(fig_pow, use_container_width=True)
    with col2:
        st.plotly_chart(fig_cities, use_container_width=True)
    
    
    st.header(f"Szczegółowa mapa ofert w najpopularniejszych miastach")

    top5_df = get_data_top5()

    # Wyświetlenie wykresu
    col1, col2 = st.columns(2)
    with col1:
        # Wybór miasta
        cities_options = top5_df["city_name"].unique().tolist()

        # Inicjalizacja session state dla miasta, jeśli nie istnieje
        if "selected_city" not in st.session_state:
            st.session_state["selected_city"] = "Warszawa"

        # Widget selectbox z kluczem do automatycznej aktualizacji session_state
        st.selectbox(
            "Wybierz miasto", 
            cities_options, 
            index=cities_options.index(st.session_state["selected_city"]), 
            key="selected_city"
        )
    
    with col2:
        col21, col22, col23 = st.columns(3)

        with col21:
            # Zamiana wartości 0 na NaN
            top5_df.loc[top5_df["salary"] == 0, "salary"] = np.nan

            # Konwersja wynagrodzenia na liczbę (dla filtrów)
            top5_df["salary_numeric"] = pd.to_numeric(top5_df["salary"], errors='coerce')

            # Suwak z **stałym zakresem** od 0 do 100 000 PLN
            salary_range = st.slider(
                "Zakres wynagrodzenia (PLN)", 
                0, 100000, (0, 100000)
            )

            # Filtrowanie po wybranym mieście i zakresie wynagrodzenia
            filtered_top5_df = top5_df[
                (top5_df["city_name"] == st.session_state["selected_city"]) & 
                (top5_df["salary_numeric"].between(salary_range[0], salary_range[1], inclusive="both"))
            ]

            # Ponowne formatowanie wynagrodzenia
            filtered_top5_df["salary"] = filtered_top5_df["salary_numeric"].apply(
                lambda x: f"{x:.2f} PLN" if not pd.isna(x) else "Brak danych"
            )
        with col22:
            selected_offer = st.selectbox("Wybierz ofertę za pomocą ID: ", filtered_top5_df["job_offer_name"].tolist())
            offer_url = f"https://justjoin.it/job-offer/{selected_offer}"
            st.page_link(offer_url, label="Przejdź do oferty pracy")
            
        
        with col23:
            # Tworzenie wykresu
            fig_cities = px.scatter_mapbox(
                filtered_top5_df,
                lat='latitude',
                lon='longitude',
                zoom=12,
                color='field_name',
                color_continuous_scale=px.colors.cyclical.IceFire,
                labels={'field_name': 'Dziedzina:'},
                custom_data=['job_title', 'company_name', 'salary', 'field_name', 'job_offer_name']
            )

            fig_cities.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>" + 
                            "<b>Wynagrodzenie:</b> %{customdata[2]}<br>" + 
                            "<b>Firma:</b> %{customdata[1]}<br>" +
                            "<b>ID:</b> %{customdata[4]}"
            )

            fig_cities.update_layout(
                mapbox_style="carto-positron", #carto-positron #open-street-map
                height=600
            )
            fig_cities.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),  # Usuwa wszystkie marginesy
                paper_bgcolor='rgb(248, 249, 250)',  # Zmienia kolor całego tła
                geo=dict(
                    bgcolor='rgb(248, 249, 250)'  # Zmienia kolor samego obszaru mapy
                )
            )
            st.plotly_chart(fig_cities, use_container_width=True)
            