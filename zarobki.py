from sqlalchemy import create_engine, text
from dotenv import load_dotenv

import streamlit as st
import pandas as pd
import altair as alt

def main():
    
    # Dodaj niestandardowy CSS dla zwiększenia szerokości kontenera
    st.markdown(
        """
        <style>
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


        @keyframes fadeInReveal {
            from {
                opacity: 0;
                clip-path: inset(80% 0% 0% 0%); 
            }
            to {
                opacity: 1;
                clip-path: inset(0% 0% 0% 0%); 
            }
        }
        .chart-wrapper {
            #animation: fadeInReveal 0.7s cubic-bezier(0.25, 1, 0.5, 1) forwards;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }

        .stColumn{
            animation: fadeIn 0.7s ease-out forwards;
            margin: 1rem;
            max-width: 47%;
            min-width: 47%;
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-opacity: 40%;
            border-radius: 10px;    
            background-color: rgb(248, 249, 250);
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            
            will-change: transform;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;

        }
        .stColumn:hover {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Tytuł dashboardu
    st.title("Zarobki w IT")

    st.header(f"Zarobki w podziale na dziedziny")

    # Poprawione dane
    data = {
        'Dziedzina': ['Python']*3 + ['Java']*3 + ['Analytics']*3 + ['Games']*3,
        'Poziom': ['junior', 'mid', 'senior']*4,
        'B2B': [7000, 12000, 20000, 8000, 13000, 21000, 9000, 14000, 22000, 9000, 14000, 22000],
        'zlecenie': [6000, 10000, 18000, 7000, 11000, 19000, 8000, 12000, 20000, 9000, 14000, 22000],
        'umowa_o_prace': [5500, 9500, 17000, 6500, 10500, 18000, 7500, 11500, 19000, 9000, 14000, 22000],
        'umowa_o_dzielo': [5000, 9000, 16000, 6000, 10000, 17000, 7000, 11000, 18000, 9000, 14000, 22000],
        'staz': [3000, None, None, 3200, None, None, 3500, None, None, 3500, None, None]
    }

    # Przekształcenie do DataFrame
    df = pd.DataFrame(data)

    # Ustawienia panelu bocznego
    st.sidebar.header("Filtry")
    selected_fields = st.sidebar.multiselect("Dziedziny", df['Dziedzina'].unique(), default=['Python','Analytics','Java'])
    selected_contracts = st.sidebar.multiselect("Typy umów", ['B2B', 'zlecenie', 'umowa_o_prace', 'umowa_o_dzielo','staz'], default=['B2B', 'umowa_o_prace'])
    start_date = st.sidebar.date_input("Data początkowa", pd.to_datetime("2023-01-01"))
    end_date = st.sidebar.date_input("Data końcowa", pd.to_datetime("2023-12-31"))
    selected_dates = (start_date, end_date)

    # Filtrowanie danych
    filtered_data = df[df['Dziedzina'].isin(selected_fields)]

    # Dynamiczne dostosowanie liczby kolumn
    max_columns = len(df['Dziedzina'].unique())  # Maksymalna liczba kolumn
    num_columns = min(max_columns, len(selected_fields))  # Liczba kolumn zależy od liczby wykresów
    columns = st.columns(num_columns)  # Tworzymy kolumny


    # Tworzenie wykresów dla każdej dziedziny
    for i, field in enumerate(selected_fields):
        # Filtruj dane dla konkretnej dziedziny
        field_data = filtered_data[filtered_data['Dziedzina'] == field].melt(
            id_vars=['Poziom'], 
            value_vars=selected_contracts, 
            var_name='Typ umowy', 
            value_name='Wartość'
        )
        
        # Tworzenie wykresu słupkowego grupowanego
        chart = alt.Chart(field_data).mark_bar().encode(
            x=alt.X('Poziom:N', title="Poziom doświadczenia", sort=['junior', 'mid', 'senior']),
            y=alt.Y('Wartość:Q', title="Zarobki (PLN)"),
            color=alt.Color('Typ umowy:N', legend=alt.Legend(title="Typ umowy")),
            xOffset=alt.XOffset('Typ umowy:N')  # Grupowanie słupków obok siebie
        )

        labels = chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,  # Adjust text position above bars
            fontSize=12,
            fontWeight="bold"
        ).encode(
            text=alt.Text('Wartość:Q', format='.0f')  # Format as integer
        )

        # 🔹 Połączenie wykresu słupkowego i etykiet
        chart_labels  = (chart  + labels).properties(
            title=f"Zarobki w dziedzinie {field}"
        ).configure(
            background='rgb(248, 249, 250)'  # Tło wykresu
        ).configure_title(
            fontSize=20
        ).configure_axisX(
            labelAngle=0,
            labelPadding=10
        )
        chart = chart.configure_title(
            fontSize=20
        )

        # Wyświetlanie wykresu w odpowiedniej kolumnie
        with columns[i % num_columns]:
            st.altair_chart(chart_labels, use_container_width=True,theme="streamlit")



    # Dodaj nowy wykres pod wszystkimi istniejącymi
    st.markdown("---")  # Dodaj linię oddzielającą

    selected_level = 'junior'

    st.header(f"Średnie zarobki w różnych dziedzinach dla poziomu doświadczenia")

    # Wybór poziomu doświadczenia dla nowego wykresu
    selected_level = st.selectbox("Wybierz poziom doświadczenia", ['junior', 'mid', 'senior'], key='level_selector')

    # Przygotowanie danych dla nowego wykresu
    level_data = df[df['Poziom'] == selected_level].melt(
        id_vars=['Dziedzina'], 
        value_vars=selected_contracts, 
        var_name='Typ umowy', 
        value_name='Wartość'
    )

    # Obliczenie średnich zarobków dla każdej dziedziny
    average_earnings = level_data.groupby('Dziedzina')['Wartość'].mean().reset_index()
    average_earnings = average_earnings.sort_values(by='Wartość', ascending=False)

    # Tworzenie wykresu słupkowego
    average_chart = alt.Chart(average_earnings).mark_bar(size=40).encode(
        x=alt.X('Dziedzina:N', title="Dziedzina", sort=None),  # Sortowanie według wartości
        y=alt.Y('Wartość:Q', title="Średnie zarobki (PLN)"),
        color=alt.Color('Dziedzina:N', legend=None)  # Bez legendy, ponieważ każdy słupek reprezentuje inną dziedzinę
    ).configure(
        background='rgb(248, 249, 250)',  # Tło wykresu
    ).configure_axisX(
        labelAngle=0,
        labelPadding=10
    )

    average_chart = average_chart.configure_title(
        fontSize=20
    )

    st.altair_chart(average_chart, use_container_width=True, theme="streamlit")
