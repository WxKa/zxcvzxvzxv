import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import os
from dotenv import load_dotenv
import pycaret.regression as pcr
from langfuse.openai import OpenAI

# Załaduj zmienne środowiskowe
load_dotenv()

# Konfiguracja strony
st.set_page_config(
    page_title="Prognoza Półmaratonu",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
def better_styling_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin: 1rem 0;
    }
    .highlight-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff4444;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #44ff44;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

better_styling_css()

# Inicjalizacja klientów
@st.cache_resource
def init_clients():
    """Inicjalizacja klientów S3 i OpenAI"""
    try:
        s3_client = boto3.client('s3')
        openai_client = OpenAI()
        return s3_client, openai_client
    except Exception as e:
        st.error(f"Błąd inicjalizacji klientów: {e}")
        return None, None

# Funkcje pomocnicze
def seconds_to_time_format(seconds: float) -> str:
    """Konwertuje sekundy na format MM:SS lub HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def create_pace_conversion_table():
    """Tworzy tabelę konwersji tempa na prędkość"""
    paces = []
    speeds = []
    
    for minutes in range(3, 11):
        for seconds in range(0, 60, 15):
            pace_str = f"{minutes}:{seconds:02d}"
            total_seconds = minutes * 60 + seconds
            speed_kmh = 3600 / total_seconds
            
            paces.append(pace_str)
            speeds.append(f"{speed_kmh:.1f}")
    
    df = pd.DataFrame({
        'Tempo (min/km)': paces,
        'Prędkość (km/h)': speeds
    })
    
    return df

@st.cache_data
def load_data_from_s3(bucket: str, key: str) -> Optional[pd.DataFrame]:
    """Ładuje dane CSV z S3"""
    try:
        s3_client, _ = init_clients()
        if s3_client is None:
            return None
            
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(obj['Body'])
        return df
    except Exception as e:
        st.error(f"Błąd ładowania danych z S3: {e}")
        return None

@st.cache_resource
def load_model_from_s3():
    """Ładuje model z S3"""
    try:
        s3_client, _ = init_clients()
        if s3_client is None:
            return None
            
        # Pobierz model z S3 do tymczasowego pliku
        s3_client.download_file('wk1', 'zadanie_9/models/time_sec_model', 'temp_model.pkl')
        model = pcr.load_model('temp_model')
        return model
    except Exception as e:
        st.error(f"Błąd ładowania modelu: {e}")
        return None

def parse_runner_data(text: str) -> Dict[str, Any]:
    """Parsuje dane biegacza używając OpenAI"""
    try:
        _, openai_client = init_clients()
        if openai_client is None:
            return {"error": "Brak dostępu do OpenAI"}
        
        prompt = f"""
        Przeanalizuj następujący tekst i wyciągnij informacje o biegaczu:
        "{text}"
        
        Zwróć wynik w formacie JSON z następującymi polami:
        - age: wiek (liczba całkowita 18-105)
        - gender: płeć ("M" dla mężczyzny, "F" dla kobiety)
        - time_5km_seconds: czas na 5km w sekundach (float, zakres 900-7200)
        - error: opis błędu jeśli dane są niepoprawne
        
        Jeśli podano tempo zamiast czasu, przelicz na czas dla 5km.
        Przykłady formatów czasu: "25:30", "25 minut 30 sekund", "tempo 5:06"
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Walidacja
        if "error" in result:
            return result
            
        if not (18 <= result.get("age", 0) <= 105):
            return {"error": "Wiek musi być w zakresie 18-105 lat"}
            
        if result.get("gender") not in ["M", "F"]:
            return {"error": "Nie udało się rozpoznać płci"}
            
        if not (900 <= result.get("time_5km_seconds", 0) <= 7200):
            return {"error": "Czas na 5km musi być w zakresie 15-120 minut"}
            
        return result
        
    except Exception as e:
        return {"error": f"Błąd parsowania danych: {e}"}

def calculate_position(predicted_time: float, historical_data: pd.DataFrame, 
                      same_gender_only: bool = False, gender: str = "M") -> int:
    """Oblicza pozycję na podstawie danych historycznych"""
    if same_gender_only:
        filtered_data = historical_data[historical_data['gender'] == gender]
    else:
        filtered_data = historical_data
    
    if 'time_seconds' in filtered_data.columns:
        times = filtered_data['time_seconds'].dropna()
    elif 'time_sec' in filtered_data.columns:
        times = filtered_data['time_sec'].dropna()
    else:
        # Spróbuj znaleźć kolumnę z czasem
        time_cols = [col for col in filtered_data.columns if 'time' in col.lower()]
        if time_cols:
            times = filtered_data[time_cols[0]].dropna()
        else:
            return 1
    
    better_times = (times < predicted_time).sum()
    return better_times + 1

# Inicjalizacja session state
if 'page' not in st.session_state:
    st.session_state.page = 'input'
if 'runner_data' not in st.session_state:
    st.session_state.runner_data = {}
if 'prediction' not in st.session_state:
    st.session_state.prediction = None
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'history_index' not in st.session_state:
    st.session_state.history_index = -1

# Sidebar navigation
st.sidebar.markdown("## 🏃‍♂️ Nawigacja")
if st.sidebar.button("Wprowadzanie danych", use_container_width=True):
    st.session_state.page = 'input'
if st.sidebar.button("Podsumowanie danych", use_container_width=True, 
                     disabled=not st.session_state.runner_data):
    st.session_state.page = 'summary'
if st.sidebar.button("Wyniki predykcji", use_container_width=True,
                     disabled=st.session_state.prediction is None):
    st.session_state.page = 'results'

# STRONA 1: Wprowadzanie danych
if st.session_state.page == 'input':
    st.markdown('<h1 class="main-header">🏃‍♂️ Prognoza Półmaratonu</h1>', 
                unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Wprowadź dane", "Tabela konwersji tempa"])
    
    with tab1:
        st.markdown('<h2 class="section-header">Wprowadź swoje dane</h2>', 
                    unsafe_allow_html=True)
        
        # Historia danych
        if st.session_state.data_history:
            st.markdown("### Historia wprowadzonych danych")
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
            
            with col1:
                if st.button("⬅️ Poprzedni") and st.session_state.history_index > 0:
                    st.session_state.history_index -= 1
                    
            with col2:
                if st.button("➡️ Następny") and st.session_state.history_index < len(st.session_state.data_history) - 1:
                    st.session_state.history_index += 1
                    
            with col3:
                if st.button("🗑️ Usuń bieżący"):
                    if 0 <= st.session_state.history_index < len(st.session_state.data_history):
                        st.session_state.data_history.pop(st.session_state.history_index)
                        if st.session_state.history_index >= len(st.session_state.data_history):
                            st.session_state.history_index = len(st.session_state.data_history) - 1
                            
            with col4:
                if st.button("🧹 Wyczyść"):
                    st.session_state.history_index = -1
                    
            with col5:
                if st.session_state.data_history and 0 <= st.session_state.history_index < len(st.session_state.data_history):
                    current_entry = st.session_state.data_history[st.session_state.history_index]
                    st.info(f"Wpis {st.session_state.history_index + 1}/{len(st.session_state.data_history)}: {current_entry[:100]}...")
        
        # Pole wprowadzania danych
        default_text = ""
        if (st.session_state.data_history and 
            0 <= st.session_state.history_index < len(st.session_state.data_history)):
            default_text = st.session_state.data_history[st.session_state.history_index]
            
        user_input = st.text_area(
            "Opisz swoje dane (wiek, płeć, czas lub tempo na 5km):",
            value=default_text,
            height=100,
            placeholder="Np: Mam 30 lat, jestem mężczyzną, mój czas na 5km to 25:30"
        )
        
        if st.button("Dalej", type="primary", use_container_width=True):
            if user_input.strip():
                # Dodaj do historii jeśli to nowy wpis
                if user_input not in st.session_state.data_history:
                    st.session_state.data_history.append(user_input)
                    st.session_state.history_index = len(st.session_state.data_history) - 1
                
                # Parsuj dane
                with st.spinner("Przetwarzam dane..."):
                    parsed_data = parse_runner_data(user_input)
                
                if "error" in parsed_data:
                    st.markdown(f'<div class="error-box">❌ {parsed_data["error"]}</div>', 
                               unsafe_allow_html=True)
                else:
                    st.session_state.runner_data = parsed_data
                    st.markdown('<div class="success-box">✅ Dane zostały pomyślnie przetworzone!</div>', 
                               unsafe_allow_html=True)
                    st.session_state.page = 'summary'
                    st.rerun()
            else:
                st.warning("Proszę wprowadzić dane o sobie.")
    
    with tab2:
        st.markdown('<h2 class="section-header">Tabela konwersji tempa na prędkość</h2>', 
                    unsafe_allow_html=True)
        
        pace_table = create_pace_conversion_table()
        
        # Wyświetl tabelę w kolumnach dla lepszej czytelności
        col1, col2, col3 = st.columns(3)
        
        rows_per_col = len(pace_table) // 3
        
        with col1:
            st.dataframe(pace_table.iloc[:rows_per_col], hide_index=True)
        with col2:
            st.dataframe(pace_table.iloc[rows_per_col:2*rows_per_col], hide_index=True)
        with col3:
            st.dataframe(pace_table.iloc[2*rows_per_col:], hide_index=True)

# STRONA 2: Podsumowanie danych
elif st.session_state.page == 'summary':
    st.markdown('<h1 class="main-header">📊 Podsumowanie Danych</h1>', 
                unsafe_allow_html=True)
    
    if st.session_state.runner_data:
        data = st.session_state.runner_data
        
        # Wyświetl podsumowanie
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Wiek", f"{data['age']} lat")
            
        with col2:
            gender_text = "Mężczyzna" if data['gender'] == 'M' else "Kobieta"
            st.metric("Płeć", gender_text)
            
        with col3:
            time_5km = seconds_to_time_format(data['time_5km_seconds'])
            st.metric("Czas na 5km", time_5km)
        
        st.markdown("---")
        
        # Przycisk predykcji
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Wróć do wprowadzania", use_container_width=True):
                st.session_state.page = 'input'
                st.rerun()
                
        with col2:
            if st.button("🔮 Oszacuj czas w półmaratonie", type="primary", use_container_width=True):
                with st.spinner("Ładuję model i wykonuję predykcję..."):
                    model = load_model_from_s3()
                    
                    if model is not None:
                        try:
                            # Przygotuj dane dla modelu
                            input_data = pd.DataFrame({
                                'gender': [data['gender']],
                                'age': [data['age']],
                                '5_km_sec': [data['time_5km_seconds']]
                            })
                            
                            # Wykonaj predykcję
                            prediction = pcr.predict_model(model, data=input_data)
                            predicted_time = prediction['prediction_label'].iloc[0]
                            
                            st.session_state.prediction = predicted_time
                            st.session_state.page = 'results'
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Błąd predykcji: {e}")
                    else:
                        st.error("Nie udało się załadować modelu.")
    else:
        st.warning("Brak danych do wyświetlenia. Wróć do wprowadzania danych.")
        if st.button("⬅️ Wróć do wprowadzania danych"):
            st.session_state.page = 'input'
            st.rerun()

# STRONA 3: Wyniki predykcji
elif st.session_state.page == 'results':
    st.markdown('<h1 class="main-header">🏆 Wyniki Predykcji</h1>', 
                unsafe_allow_html=True)
    
    if st.session_state.prediction is not None and st.session_state.runner_data:
        # Wyświetl przewidywany czas
        predicted_time_str = seconds_to_time_format(st.session_state.prediction)
        st.markdown(f'<div class="highlight-box"><h2 style="text-align: center; color: #1f77b4;">🎯 Przewidywany czas półmaratonu: {predicted_time_str}</h2></div>', 
                   unsafe_allow_html=True)
        
        # Zakładki dla różnych lat
        tab1, tab2 = st.tabs(["Półmaraton Wrocław 2023", "Półmaraton Wrocław 2024"])
        
        for tab, year in [(tab1, 2023), (tab2, 2024)]:
            with tab:
                # Załaduj dane historyczne
                historical_data = load_data_from_s3('wk1', 
                    f'zadanie_9/current/halfmarathon_wroclaw_{year}__final_cleaned_full.csv')
                
                if historical_data is not None:
                    # Wybór filtrowania
                    same_gender = st.checkbox(f"Pokaż tylko biegaczy tej samej płci ({year})", 
                                            key=f"gender_filter_{year}")
                    
                    # Przygotuj dane do wykresu
                    if same_gender:
                        plot_data = historical_data[historical_data['gender'] == st.session_state.runner_data['gender']]
                        title_suffix = f" - {'Mężczyźni' if st.session_state.runner_data['gender'] == 'M' else 'Kobiety'}"
                    else:
                        plot_data = historical_data
                        title_suffix = " - Wszyscy biegacze"
                    
                    # Znajdź kolumnę z czasem
                    time_col = None
                    age_col = None
                    
                    for col in plot_data.columns:
                        if 'time' in col.lower() and 'sec' in col.lower():
                            time_col = col
                        elif col.lower() in ['age', 'wiek']:
                            age_col = col
                    
                    if time_col and age_col:
                        # Utwórz wykres
                        fig, ax = plt.subplots(figsize=(12, 8))
                        
                        # Wykres rozrzutu dla danych historycznych
                        if same_gender:
                            color = 'blue' if st.session_state.runner_data['gender'] == 'M' else 'red'
                            alpha = 0.6
                        else:
                            # Różne kolory dla różnych płci
                            men_data = plot_data[plot_data['gender'] == 'M']
                            women_data = plot_data[plot_data['gender'] == 'F']
                            
                            if not men_data.empty:
                                ax.scatter(men_data[age_col], men_data[time_col]/60, 
                                         alpha=0.4, c='blue', label='Mężczyźni', s=20)
                            if not women_data.empty:
                                ax.scatter(women_data[age_col], women_data[time_col]/60, 
                                         alpha=0.4, c='red', label='Kobiety', s=20)
                            color = 'blue' if st.session_state.runner_data['gender'] == 'M' else 'red'
                            alpha = 0.4
                        
                        if same_gender:
                            ax.scatter(plot_data[age_col], plot_data[time_col]/60, 
                                     alpha=alpha, c=color, s=20)
                        
                        # Dodaj punkt dla aktualnego biegacza
                        ax.scatter(st.session_state.runner_data['age'], 
                                 st.session_state.prediction/60,
                                 c='gold', s=200, marker='*', 
                                 edgecolors='black', linewidth=2,
                                 label='Twoja predykcja', zorder=5)
                        
                        ax.set_xlabel('Wiek', fontsize=12)
                        ax.set_ylabel('Czas (minuty)', fontsize=12)
                        ax.set_title(f'Czasy półmaratonu vs wiek - Wrocław {year}{title_suffix}', 
                                   fontsize=14)
                        ax.grid(True, alpha=0.3)
                        ax.legend()
                        
                        st.pyplot(fig)
                        
                        # Oblicz pozycję
                        position = calculate_position(
                            st.session_state.prediction, 
                            plot_data, 
                            same_gender, 
                            st.session_state.runner_data['gender']
                        )
                        
                        total_runners = len(plot_data)
                        percentile = (1 - position/total_runners) * 100
                        
                        st.markdown(f"""
                        <div class="highlight-box">
                        <h3>📈 Szacowana pozycja w {year} roku:</h3>
                        <ul>
                        <li><strong>Miejsce:</strong> {position} z {total_runners}</li>
                        <li><strong>Percentyl:</strong> {percentile:.1f}% (lepszy niż {percentile:.1f}% uczestników)</li>
                        </ul>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.error(f"Nie znaleziono odpowiednich kolumn w danych z {year} roku.")
                else:
                    st.error(f"Nie udało się załadować danych historycznych z {year} roku.")
        
        # Przycisk powrotu
        st.markdown("---")
        if st.button("⬅️ Wróć do wprowadzania danych", use_container_width=True):
            st.session_state.page = 'input'
            st.rerun()
            
    else:
        st.warning("Brak wyników predykcji. Wykonaj najpierw predykcję.")
        if st.button("⬅️ Wróć do podsumowania danych"):
            st.session_state.page = 'summary' if st.session_state.runner_data else 'input'
            st.rerun()

# Footer
st.markdown("---")
st.markdown("*Aplikacja do prognozowania czasu w półmaratonie na podstawie danych z Półmaratonu Wrocławskiego*")