import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import numpy as np
from sqlalchemy import create_engine

# 🔹 Połączenie z bazą danych
server = st.secrets["database"]["DB_SERVER"]
database = st.secrets["database"]["DB_DATABASE"]
username = st.secrets["database"]["DB_USERNAME"]
password = st.secrets["database"]["DB_PASSWORD"]
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&charset=utf8"
engine = create_engine(connection_string, use_setinputsizes=False)

def main():
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
                SELECT jo.job_offer_id, f.field_name, jo.latitude, jo.longitude, d.date_full, c.city_name, co.company_name,
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
            x=0.7,  # Przesuwa legendę bliżej mapy (zmniejszaj wartość, jeśli nadal za daleko)
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
        coloraxis_colorbar=dict(
            x=0.7,  # Przesuwa legendę bliżej mapy (zmniejszaj wartość, jeśli nadal za daleko)
        )
    )

    df_cities = get_data_cities()
    cities_cords = pd.read_csv("cities/cities_z_koordynatami.csv")
    df_cities = df_cities.merge(cities_cords, left_on="city_name", right_on='city_name')
    fig_cities = px.scatter_map(df_cities, lat='latitude', lon='longitude', zoom=4, size='liczba_ofert',
                        color_continuous_scale=px.colors.cyclical.IceFire, size_max=40)

    st.title("Mapa ofert pracy w Polsce")

    col1, col2= st.columns(2)
    with col1: 
        selected_chart = st.radio("Wybierz poziom agregacji:", ["Województwa", "Powiaty"], horizontal=True)
        if selected_chart == "Województwa":
            st.plotly_chart(fig_woj, use_container_width=True)
        else:
            st.plotly_chart(fig_pow, use_container_width=True)
    with col2:
        st.plotly_chart(fig_cities, use_container_width=True)
    
    
    top5_df = get_data_top5()

    fields_options = top5_df["city_name"].unique().tolist()

    selected_city = st.selectbox("Wybierz miasto", fields_options)

    # Filtrowanie danych tylko dla wybranego miasta
    filtered_top5_df = top5_df[top5_df["city_name"] == selected_city]
    filtered_top5_df.loc[filtered_top5_df["salary"] == 0, "salary"] = np.nan
    filtered_top5_df["salary"] = filtered_top5_df["salary"].apply(
        lambda x: f"{x:.2f} PLN" if not pd.isna(x) else "Brak danych"
    )

    # Tworzenie mapy z Plotly
    fig = px.scatter_mapbox(
        filtered_top5_df,
        lat='latitude',
        lon='longitude',
        zoom=12,
        color='field_name',
        color_continuous_scale=px.colors.cyclical.IceFire,
        hover_data={  # Nowe dane do podglądu po najechaniu
        'field_name': True, 
        'salary': True,  
        'company_name': True,
        'longitude': False,
        'latitude': False  
    }
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        height=1000 
    )
    
    with st.container(key='plot'):
        st.plotly_chart(fig, use_container_width=True)
