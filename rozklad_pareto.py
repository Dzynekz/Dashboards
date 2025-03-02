from sqlalchemy import create_engine, text
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from scipy.stats import pareto, skew, kurtosis
import streamlit.components.v1 as components

# Połączenie z bazą danych
server = st.secrets["database"]["DB_SERVER"]
database = st.secrets["database"]["DB_DATABASE"]
username = st.secrets["database"]["DB_USERNAME"]
password = st.secrets["database"]["DB_PASSWORD"]
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&charset=utf8"
engine = create_engine(connection_string, use_setinputsizes=False)

def main():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 95%;
            padding: 1rem;  
        }
        .stHeading {
            margin-bottom: 1rem;
        }
        .stMainBlockContainer {
            padding: 3rem;
        }
        .stVerticalBlock:nth-child(1) .stHorizontalBlock {     
            display: flex;
            flex-direction: column;
        }
        .stVerticalBlock:nth-child(1) .stHorizontalBlock:nth-child(1) {     
            display: flex;
            flex-direction: column-reverse;
        }

        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(1),
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock .stColumn,
        .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(2),
        .stMetric {
            padding: 1.5rem;
            border: solid 1px rgba(248, 249, 250, 0.5);
            border-radius: 10px;    
            margin-bottom: 1.5rem;   
            background-color: rgb(248, 249, 250);       
            box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;
            transition: box-shadow 0.5s ease-in-out, transform 0.3s ease-in-out;
        }
        .stHorizontalBlock:nth-child(5) .stColumn:nth-child(1) .stVerticalBlock {
            display:flex;
            flex-direction: row;
        }
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock {
            display:flex;
            flex-direction: row;
            flex-wrap: wrap;
        }
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(1),
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(1) .stHorizontalBlock > .stColumn,
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2),
        .stHorizontalBlock:nth-child(5) > .stColumn,
        .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(2) .stHorizontalBlock > .stColumn
         {
            width: 100%;
        }

        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock > .stColumn:nth-child(1) {
            min-width:700px;
        }

        .stHorizontalBlock:nth-child(4),
         .stHorizontalBlock:nth-child(5),
          .stMain .stVerticalBlock:nth-child(1) > .stElementContainer:nth-child(3) > .stHeading {
            margin-left: 5%;
            margin-right: 5%;
        }

        .stExpander {
            width: 100%;
        }

        .stMetric:hover,
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(1):hover,
        .stHorizontalBlock:nth-child(5) > .stColumn:nth-child(2):hover,
        .stHorizontalBlock:nth-child(4) > .stColumn:nth-child(2) .stHorizontalBlock .stColumn:hover
        {
            box-shadow: #0096c7 0px 3px 8px; 
            transform: translateY(-5px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    @st.cache_data
    def get_data():
        query = '''
            SELECT c.city_id, c.city_name, COUNT(j.job_offer_id) as liczba_ofert
            FROM Job_Offers as j 
            JOIN Cities as c ON j.city_id = c.city_id
            WHERE c.is_polish = 1
            GROUP BY c.city_id, c.city_name
        '''
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df
    
    df = get_data()
    df = df[df['liczba_ofert'] > 0]
    
    st.title("Rozkład Pareto liczby ofert pracy w polskich miastach")

    col1, col2 = st.columns(2)
    with col1:
        
        col11, col12, col13, col14= st.columns(4)
        # Wykres Pareto (interaktywny próg)
        with col11:
            with st.expander("ℹ️ Co oznacza ten wykres?"):
                st.markdown("""
                ##### Wykres Pareto (dynamiczny próg + model 80/20)
                Wykres przedstawia zależność między liczbą ofert pracy a procentem miast, które te oferty generują. Dodatkowo dodano **teoretyczny model Pareto 80/20** dla porównania.

                - **Oś X (Procent miast)** – miasta są uporządkowane od największej do najmniejszej liczby ofert.
                - **Oś Y (Skumulowany procent ofert pracy)** – pokazuje, jaki procent wszystkich ofert pracy przypada na określoną liczbę miast.
                - **Czerwona kropka** – dynamiczny próg Pareto. Ilustruje punkt, w którym określony procent miast (np. 20%) generuje wybrany procent ofert (np. 80%).
                - **Pomarańczowa przerywana linia** – teoretyczny rozkład Pareto 80/20. Pokazuje idealne dopasowanie do zasady Pareto, gdzie 20% miast generuje 80% ofert.

                ##### Interpretacja:
                - Jeśli **rzeczywista krzywa (niebieska linia)** przebiega **blisko pomarańczowej przerywanej linii**, oznacza to, że rozkład liczby ofert pracy dobrze pasuje do prawa Pareto.
                - Jeśli krzywa rzeczywista **przebiega powyżej**, oznacza to, że koncentracja ofert w największych miastach jest jeszcze większa niż w modelu 80/20.
                - Jeśli krzywa rzeczywista **przebiega poniżej**, oznacza to, że rozkład ofert jest bardziej równomierny i mniej skoncentrowany.

                Wykres pozwala ocenić, czy rynek pracy jest zdominowany przez kilka miast, czy oferty są bardziej równomiernie rozproszone oraz jak blisko rzeczywisty rozkład jest względem zasady Pareto.
                """)

        with col12:
            df_sorted = df.sort_values(by='liczba_ofert', ascending=False)
            df_sorted['cum_oferty'] = df_sorted['liczba_ofert'].cumsum()
            df_sorted['cum_oferty_pct'] = df_sorted['cum_oferty'] / df_sorted['liczba_ofert'].sum()
            df_sorted['cum_miasta_pct'] = (np.arange(len(df_sorted)) + 1) / len(df_sorted)

            threshold_pct = st.slider("Wybierz procent ofert pracy", min_value=0.4, max_value=1.0, value=0.8, step=0.01)

        with col13:  
            pareto_threshold = df_sorted[df_sorted['cum_oferty_pct'] >= threshold_pct].iloc[0]
            st.markdown(f"<h5>Interpretacja: Około {pareto_threshold['cum_miasta_pct'] * 100:.2f}%  miast ({int(pareto_threshold['cum_miasta_pct'] * len(df))}) generuje {threshold_pct * 100:.0f}% wszystkich ofert pracy.</h5>", unsafe_allow_html=True)

        with col14:
            pareto_chart = alt.Chart(df_sorted).mark_line(color='#0096c7', point=True).encode(
                x=alt.X('cum_miasta_pct:Q', title='Procent miast (od największej liczby ofert)'),
                y=alt.Y('cum_oferty_pct:Q', title='Skumulowany procent ofert pracy')
            ) + alt.Chart(pd.DataFrame({'x': [pareto_threshold['cum_miasta_pct']], 'y': [pareto_threshold['cum_oferty_pct']]})).mark_point(color='red', size=100).encode(
                x='x:Q', y='y:Q'
            ).properties(
                title="Wykres Pareto (dynamiczny próg + model 80/20)"
            )
            pareto_chart = pareto_chart.configure(
                background='rgb(248, 249, 250)'  # Tło wykresu
            ).configure_title(
                fontSize=20
            )

            pareto_theory = pd.DataFrame({
                'cum_miasta_pct': np.linspace(0, 1, 100),
                'cum_oferty_pct': np.where(np.linspace(0, 1, 100) <= 0.2, 
                                        np.linspace(0, 1, 100) * (0.8 / 0.2), 
                                        0.8 + (np.linspace(0, 1, 100) - 0.2) * (0.2 / 0.8))
            })
            pareto_line = alt.Chart(pareto_theory).mark_line(color='orange', strokeDash=[5,5]).encode(
                x='cum_miasta_pct:Q', 
                y='cum_oferty_pct:Q'
            )
            st.altair_chart(pareto_chart + pareto_line)
            
        
    # Grupowanie danych
    city_counts = df.groupby("city_name")["liczba_ofert"].sum().reset_index()
    # Wybór top 10 miast pod względem liczby ofert
    top_10_cities = city_counts.nlargest(10, "liczba_ofert")

    # Tworzenie wykresu słupkowego
    chart_top10 = alt.Chart(top_10_cities).mark_bar(color='#0096c7').encode(
        x=alt.X('city_name:N', title='Miasto', sort='-y', axis=alt.Axis(labelAngle=0)),  # Sortowanie według liczby ofert
        y=alt.Y('liczba_ofert:Q', title='Liczba ofert pracy'),
        tooltip=['city_name', 'liczba_ofert']
    ).configure(
        background='rgb(248, 249, 250)'  # Tło wykresu
    ).properties(
        height=400,
        title="Top 10 miast pod względem liczby ofert pracy"
    ).configure_title(
        fontSize=20
    )


    # 📌 Tworzenie wykresu kołowego (Pie Chart)
    top_10 = df.nlargest(10, "liczba_ofert")

    # Suma ofert dla pozostałych miast
    inne_suma = df[~df["city_name"].isin(top_10["city_name"])]["liczba_ofert"].sum()

    # Tworzenie nowego DF z 10 miastami i dodatkową kategorią "Inne"
    df_top10_inne = pd.concat([
        top_10,
        pd.DataFrame([{"city_name": "Inne", "liczba_ofert": inne_suma}])
    ], ignore_index=True)

    
    chart = alt.Chart(df_top10_inne).mark_arc().encode(
        theta=alt.Theta("liczba_ofert:Q"),
        color=alt.Color("city_name:N", title="Miasto",
                    scale=alt.Scale(scheme="category20")), 
        order=alt.Order("liczba_ofert:Q", sort="descending"),
        tooltip=["city_name", "liczba_ofert"]
    ).configure(
        background='rgb(248, 249, 250)'  # Tło wykresu
    ).properties(
        title="TOP 10 miast + 'Inne' (oferty pracy)"
    ).configure_title(
        fontSize=20
    )


    # Wyświetlenie wykresu
    with col2:
        col21, col22 = st.columns(2)
        with col21:
            st.altair_chart(chart_top10, use_container_width=True)
        with col22:
            st.altair_chart(chart, use_container_width=True)
       
    # Obliczenie dodatkowych metryk
    mean = np.mean(df['liczba_ofert'])
    variance = np.var(df['liczba_ofert'])
    skewness = skew(df['liczba_ofert'])
    kurt = kurtosis(df['liczba_ofert'])
    
    col1, col2 = st.columns(2)
    with col1:      
        st.metric(label="Średnia", value=f"{mean:.2f}", 
          help='Średnia arytmetyczna liczby ofert pracy na miasto. Wskazuje, ile ofert przypada średnio na jedno miasto.')

        st.metric(label="Wariancja", value=f"{variance:.2f}", 
            help='Miara rozproszenia liczby ofert pracy między miastami. Wyższa wariancja oznacza większe zróżnicowanie w liczbie ofert.')

        st.metric(label="Współczynnik skośności", value=f"{skewness:.2f}", 
            help='Określa asymetrię rozkładu liczby ofert pracy. Wartość dodatnia oznacza, że większość miast ma mniej ofert, ale jest kilka z bardzo dużą liczbą ofert. Wartość ujemna oznacza odwrotną sytuację.')

        st.metric(label="Kurtoza", value=f"{kurt:.2f}", 
            help='Miara "szczytowatości" rozkładu liczby ofert pracy. Wartość wyższa od 3 sugeruje, że rozkład ma więcej wartości ekstremalnych (grubymi ogonami). Wartość mniejsza od 3 oznacza, że rozkład jest bardziej płaski.')


    with col2:    
        col21, col22, col23, col24 = st.columns(4)

        with col21:
            with st.expander("ℹ️ Co oznacza ten wykres?"):
                st.markdown("""
                ##### Wykres Q-Q (log-log) – analiza dopasowania do rozkładu Pareto
                Wykres pozwala ocenić, na ile rozkład liczby ofert pracy przypomina teoretyczny rozkład Pareto. Wykorzystuje **skalę logarytmiczną**, aby lepiej zobrazować dopasowanie rozkładu do modelu.

                - **Oś X (Teoretyczne wartości, log)** – wartości oczekiwane zgodnie z rozkładem Pareto.
                - **Oś Y (Empiryczne wartości, log)** – rzeczywiste wartości liczby ofert pracy w miastach.
                - **Niebieskie punkty** – empiryczne wartości skumulowanych percentyli liczby ofert pracy.
                - **Czerwona linia** – idealne dopasowanie do rozkładu Pareto. Im bardziej punkty pokrywają się z linią, tym lepsze dopasowanie.
                
                ##### Dlaczego skala logarytmiczna?
                Rozkład Pareto charakteryzuje się **silnie prawostronnym ogonem** – oznacza to, że większość miast ma mało ofert, ale jest kilka z bardzo dużą liczbą. Na zwykłym wykresie te duże wartości dominowałyby resztę danych i trudniej byłoby ocenić zgodność z modelem Pareto. **Logarytmiczna skala** pozwala lepiej zobaczyć strukturę danych i dopasowanie do teoretycznego rozkładu.

                ##### Parametry rozkładu Pareto:
                - **(x\u2098) (Wartość minimalna)** – określa najmniejszą wartość, od której zaczyna się rozkład Pareto. Im wyższa wartość (x\u2098), tym większa minimalna liczba ofert w miastach, które są brane pod uwagę.  
                - **(α) (Parametr kształtu)** – kontroluje, jak mocno rozkład jest "rozciągnięty".  
                    - **Niska wartość (α) (np. 0.5 - 1.0)** – oznacza, że niewielka liczba miast dominuje pod względem liczby ofert (silne nierówności).  
                    - **Wysoka wartość (α) (np. >2.0)** – oznacza bardziej równomierny rozkład ofert pracy między miastami.
        
                ##### Interpretacja wykresu:
                - Jeśli **punkty leżą wzdłuż czerwonej linii**, oznacza to, że liczba ofert pracy w miastach dobrze pasuje do rozkładu Pareto.
                - Jeśli **punkty odchylają się w górę**, oznacza to, że w największych miastach jest jeszcze więcej ofert, niż przewidywałby model Pareto.
                - Jeśli **punkty odchylają się w dół**, oznacza to, że rozkład ofert jest bardziej równomierny i odbiega od klasycznego prawa Pareto.

                Zmiana parametrów (x\u2098) i (α) pozwala modelować różne scenariusze i sprawdzić, jak dobrze dane rzeczywiste pasują do teorii Pareto.
                """)


        with col22:
            xm = st.slider("Wartość minimalna (x\u2098)", min_value=1, max_value=int(df['liczba_ofert'].max()), value=int(df['liczba_ofert'].min()))       
        with col23:
            alpha = st.slider("Parametr kształtu (α)", min_value=0.1, max_value=3.0, value=0.7, step=0.1)
        with col24:
            # Wykres Q-Q (log-log)
            emp_quantiles = np.sort(df['liczba_ofert'])
            theo_quantiles = pareto.ppf(np.linspace(0.01, 0.99, len(emp_quantiles)), alpha, loc=0, scale=xm)
            
            qq_df = pd.DataFrame({'Teoretyczne': theo_quantiles, 'Empiryczne': emp_quantiles})
            qq_chart = alt.Chart(qq_df).mark_point(color='#0096c7').encode(
                x=alt.X('Teoretyczne:Q', scale=alt.Scale(type='log'), title='Teoretyczne (log)'),
                y=alt.Y('Empiryczne:Q', scale=alt.Scale(type='log'), title='Empiryczne (log)')
            ) + alt.Chart(qq_df).mark_line(color='red').encode(
                x='Teoretyczne:Q', y='Teoretyczne:Q'
            )

            qq_chart = qq_chart.configure(
                background='rgb(248, 249, 250)'  # Tło wykresu
            ).properties(
                title="Wykres Q-Q (log-log)"
            ).configure_title(
                fontSize=20
            )
            st.altair_chart(qq_chart.properties(width=700, height=400))

    
    