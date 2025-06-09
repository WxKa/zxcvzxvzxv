import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Import dodatkowych modułów
from langfuse.openai import OpenAI
import pycaret.regression as pcr

# Konfiguracja strony
st.set_page_config(
    page_title="Prognoza czasu w półmaratonie",
    page_icon="🏃‍♂️",
    layout="wide"
)

# CSS styling
def apply_custom_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #f0f8ff;
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
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# Inicjalizacja session state
def init_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'input'
    if 'runner_data' not in st.session_state:
        st.session_state.runner_data = {}
    if 'prediction' not in st.session_state:
        st.session_state.prediction = None
    if 'data_history' not in st.session_state:
        st.session_state.data_history = []
    if 'history_index' not in st.session_state:
        st.session_state.history_index = -1

init_session_state()

# Klient S3
@st.cache_resource
def get_s3_client():
    return boto3.client('s3')

# Klient OpenAI
@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Funkcje pomocnicze
def time_to_seconds(time_str: str) -> int:
    """Konwertuje czas w formacie MM:SS lub HH:MM:SS na sekundy"""
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        raise ValueError("Nieprawidłowy format czasu")

def seconds_to_time(seconds: int) -> str:
    """Konwertuje sekundy na format HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def pace_to_seconds_5km(pace_str: str) -> int:
    """Konwertuje tempo (min'sek''/km) na czas na 5km w sekundach"""
    # Parsowanie tempa w różnych formatach
    pace_str = pace_str.replace("'", ":").replace('"', '').replace("''", '')
    parts = pace_str.split(':')
    if len(parts) == 2:
        pace_seconds = int(parts[0]) * 60 + int(parts[1])
        return pace_seconds * 5  # tempo na km * 5km
    else:
        raise ValueError("Nieprawidłowy format tempa")

# Ładowanie modelu
@st.cache_data
def load_prediction_model():
    try:
        s3 = get_s3_client()
        model = pcr.load_model('time_sec_model',
                              platform='aws',
                              authentication={'bucket': 'wk1',
                                            'path': 'zadanie_9/models/'})
        return model
    except Exception as e:
        st.error(f"Błąd ładowania modelu: {e}")
        return None

# Ładowanie danych historycznych
@st.cache_data
def load_historical_data(year: int):
    try:
        s3 = get_s3_client()
        csv_path = f'zadanie_9/current/halfmarathon_wroclaw_{year}__final_cleaned_full.csv'

        response = s3.get_object(Bucket='wk1', Key=csv_path)
        df = pd.read_csv(response['Body'], sep=';')
        return df
    except Exception as e:
        st.error(f"Błąd ładowania danych historycznych dla roku {year}: {e}")
        return None

# Parsowanie danych z pomocą OpenAI
def parse_runner_data(text: str) -> Dict:
    client = get_openai_client()

    prompt = f"""
    Przeanalizuj następujący tekst i wyciągnij informacje o biegaczu:
    "{text}"

    Zwróć odpowiedź w formacie JSON z następującymi polami:
    - age: wiek (liczba całkowita 18-105)
    - gender: płeć ("M" dla mężczyzna/"F" dla kobieta)
    - time_5km_sec: czas na 5km w sekundach (900-7200 sek, czyli 15-120 min)
    - errors: lista błędów jeśli jakieś dane są nieprawidłowe

    Jeśli podano tempo zamiast czasu, przelicz tempo na czas na 5km.
    Przykłady formatów:
    - Czas: "25:30", "25 minut 30 sekund"
    - Tempo: "5'06''", "5:06 na km"

    Jeśli nie możesz wyciągnąć jakiejś informacji lub jest nieprawidłowa, dodaj błąd do listy errors.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"errors": [f"Błąd parsowania: {e}"]}

# Tabela konwersji tempo-prędkość
def create_pace_speed_table():
    paces = []
    for min_per_km in range(3, 8):
        for sec in [0, 15, 30, 45]:
            if min_per_km == 7 and sec > 30:
                break
            pace_seconds = min_per_km * 60 + sec
            speed_kmh = 3600 / pace_seconds
            paces.append({
                'Tempo (min/km)': f"{min_per_km}:{sec:02d}",
                'Prędkość (km/h)': f"{speed_kmh:.1f}"
            })

    return pd.DataFrame(paces)

# STRONA 1: Wprowadzanie danych
def page_input():
    st.markdown('<div class="main-header">🏃‍♂️ Prognoza czasu w półmaratonie</div>',
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Wprowadź dane", "Tabela konwersji tempo-prędkość"])

    with tab1:
        st.markdown('<div class="section-header">Wprowadź swoje dane</div>',
                    unsafe_allow_html=True)

        # Historia danych
        if st.session_state.data_history:
            st.subheader("Historia danych")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("← Poprzedni"):
                    if st.session_state.history_index > 0:
                        st.session_state.history_index -= 1

            with col2:
                if st.button("Następny →"):
                    if st.session_state.history_index < len(st.session_state.data_history) - 1:
                        st.session_state.history_index += 1

            with col3:
                if st.button("Wyczyść bieżący"):
                    st.session_state.history_index = -1

            with col4:
                if st.button("Usuń z historii"):
                    if 0 <= st.session_state.history_index < len(st.session_state.data_history):
                        st.session_state.data_history.pop(st.session_state.history_index)
                        st.session_state.history_index = -1
                        st.rerun()

            # Wyświetl aktualnie wybrany wpis
            if 0 <= st.session_state.history_index < len(st.session_state.data_history):
                current_entry = st.session_state.data_history[st.session_state.history_index]
                st.info(f"Wpis {st.session_state.history_index + 1}/{len(st.session_state.data_history)}: {current_entry}")

        # Pole tekstowe dla danych
        default_text = ""
        if 0 <= st.session_state.history_index < len(st.session_state.data_history):
            default_text = st.session_state.data_history[st.session_state.history_index]

        user_input = st.text_area(
            "Opisz swoje dane (wiek, płeć, czas na 5km lub tempo):",
            value=default_text,
            placeholder="Przykład: Mam 30 lat, jestem mężczyzną, mój czas na 5km to 22:15",
            height=100
        )

        if st.button("Dalej", type="primary"):
            if user_input.strip():
                # Dodaj do historii jeśli to nowy wpis
                if user_input not in st.session_state.data_history:
                    st.session_state.data_history.append(user_input)

                # Parsuj dane
                with st.spinner("Przetwarzam dane..."):
                    parsed_data = parse_runner_data(user_input)

                if "errors" in parsed_data and parsed_data["errors"]:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error("Błędy w danych:")
                    for error in parsed_data["errors"]:
                        st.write(f"• {error}")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Walidacja
                    errors = []

                    if not (18 <= parsed_data.get("age", 0) <= 105):
                        errors.append("Wiek musi być między 18 a 105 lat")

                    if parsed_data.get("gender") not in ["M", "F"]:
                        errors.append("Płeć musi być określona jako mężczyzna (M) lub kobieta (F)")

                    if not (900 <= parsed_data.get("time_5km_sec", 0) <= 7200):
                        errors.append("Czas na 5km musi być między 15 a 120 minut")

                    if errors:
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.error("Błędy walidacji:")
                        for error in errors:
                            st.write(f"• {error}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.runner_data = parsed_data
                        st.session_state.current_page = 'summary'
                        st.rerun()
            else:
                st.warning("Proszę wprowadzić dane.")

    with tab2:
        st.subheader("Tabela konwersji tempo na prędkość")
        pace_table = create_pace_speed_table()
        st.dataframe(pace_table, use_container_width=True)

# STRONA 2: Podsumowanie i predykcja
def page_summary():
    st.markdown('<div class="main-header">📊 Podsumowanie danych</div>',
                unsafe_allow_html=True)

    if not st.session_state.runner_data:
        st.error("Brak danych biegacza. Wróć do strony wprowadzania danych.")
        if st.button("Powrót do wprowadzania danych"):
            st.session_state.current_page = 'input'
            st.rerun()
        return

    data = st.session_state.runner_data

    # Wyświetl podsumowanie
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader("Twoje dane:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Wiek", f"{data['age']} lat")

    with col2:
        gender_text = "Mężczyzna" if data['gender'] == 'M' else "Kobieta"
        st.metric("Płeć", gender_text)

    with col3:
        time_5km = seconds_to_time(data['time_5km_sec'])
        st.metric("Czas na 5km", time_5km)

    st.markdown('</div>', unsafe_allow_html=True)

    # Przyciski
    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Powrót do wprowadzania danych"):
            st.session_state.current_page = 'input'
            st.rerun()

    with col2:
        if st.button("Oszacuj czas w półmaratonie", type="primary"):
            with st.spinner("Ładuję model i generuję prognozę..."):
                model = load_prediction_model()

                if model is None:
                    st.error("Nie udało się załadować modelu predykcji.")
                    return

                try:
                    # Przygotuj dane dla modelu
                    input_data = pd.DataFrame([{
                        'gender': data['gender'],
                        'age': data['age'],
                        '5_km_sec': float(data['time_5km_sec'])
                    }])

                    # Wykonaj predykcję
                    prediction = pcr.predict_model(model, data=input_data)
                    predicted_seconds = int(prediction['prediction_label'].iloc[0])

                    st.session_state.prediction = predicted_seconds
                    st.session_state.current_page = 'results'
                    st.rerun()

                except Exception as e:
                    st.error(f"Błąd podczas predykcji: {e}")

# STRONA 3: Wyniki i wizualizacja
def page_results():
    st.markdown('<div class="main-header">🏆 Wyniki predykcji</div>',
                unsafe_allow_html=True)

    if st.session_state.prediction is None:
        st.error("Brak prognozy. Wróć do poprzedniej strony.")
        if st.button("Powrót"):
            st.session_state.current_page = 'summary'
            st.rerun()
        return

    # Wyświetl przewidywany czas
    predicted_time = seconds_to_time(st.session_state.prediction)

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader("Twój przewidywany czas w półmaratonie:")
    st.markdown(f'<div style="font-size: 3rem; font-weight: bold; text-align: center; color: #1f77b4;">{predicted_time}</div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Zakładki z wizualizacjami
    tab1, tab2 = st.tabs(["Półmaraton Wrocław 2023", "Półmaraton Wrocław 2024"])

    for tab, year in zip([tab1, tab2], [2023, 2024]):
        with tab:
            create_visualization(year)

    # Przycisk powrotu
    if st.button("← Powrót do strony głównej"):
        st.session_state.current_page = 'input'
        st.session_state.prediction = None
        st.rerun()

def create_visualization(year: int):
    df = load_historical_data(year)

    if df is None:
        st.error(f"Nie udało się załadować danych dla roku {year}")
        return

    # Wybór grupy porównawczej
    show_all = st.radio(
        f"Porównaj z (rok {year}):",
        ["Wszystkimi biegaczami", "Biegaczami tej samej płci"],
        key=f"radio_{year}"
    )

    # Filtruj dane jeśli potrzeba
    if show_all == "Biegaczami tej samej płci":
        user_gender = st.session_state.runner_data['gender']
        df_filtered = df[df['gender'] == user_gender].copy()
        title_suffix = f" (płeć: {'mężczyźni' if user_gender == 'M' else 'kobiety'})"
    else:
        df_filtered = df.copy()
        title_suffix = " (wszyscy biegacze)"

    # Konwersja czasu na sekundy jeśli potrzeba
    if 'time_seconds' not in df_filtered.columns:
        # Assumujemy że jest kolumna z czasem w formacie tekstowym
        time_columns = [col for col in df_filtered.columns if 'time' in col.lower() or 'czas' in col.lower()]
        if time_columns:
            try:
                df_filtered['time_seconds'] = df_filtered[time_columns[0]].apply(
                    lambda x: time_to_seconds(str(x)) if pd.notna(x) else None
                )
            except:
                st.error("Problem z konwersją czasów w danych historycznych")
                return

    # Sprawdź czy mamy potrzebne kolumny
    required_cols = ['age', 'time_seconds']
    missing_cols = [col for col in required_cols if col not in df_filtered.columns]
    if missing_cols:
        st.error(f"Brakuje kolumn w danych: {missing_cols}")
        return

    # Usuń wiersze z brakującymi danymi
    df_filtered = df_filtered.dropna(subset=['age', 'time_seconds'])

    if len(df_filtered) == 0:
        st.warning("Brak danych do wyświetlenia")
        return

    # Stwórz wykres
    fig, ax = plt.subplots(figsize=(12, 8))

    # Wykres rozrzutu dla danych historycznych
    scatter = ax.scatter(df_filtered['age'], df_filtered['time_seconds'] / 3600,
                        alpha=0.6, s=30, color='lightblue', label='Uczestnicy historyczni')

    # Dodaj punkt dla aktualnego biegacza
    user_age = st.session_state.runner_data['age']
    user_time_hours = st.session_state.prediction / 3600

    ax.scatter(user_age, user_time_hours,
              color='red', s=200, marker='*',
              label='Twoja prognoza', zorder=5, edgecolor='darkred', linewidth=2)

    # Formatowanie wykresu
    ax.set_xlabel('Wiek', fontsize=12)
    ax.set_ylabel('Czas (godziny)', fontsize=12)
    ax.set_title(f'Półmaraton Wrocław {year}{title_suffix}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Ustaw limity osi Y dla lepszej czytelności
    y_min = max(1.0, df_filtered['time_seconds'].min() / 3600 - 0.1)
    y_max = min(4.0, df_filtered['time_seconds'].max() / 3600 + 0.1)
    ax.set_ylim(y_min, y_max)

    st.pyplot(fig)
    plt.close()

    # Oblicz szacowane miejsce
    better_runners = len(df_filtered[df_filtered['time_seconds'] < st.session_state.prediction])
    total_runners = len(df_filtered)
    estimated_place = better_runners + 1

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"Szacowane miejsce w roku {year}:")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Miejsce", f"{estimated_place}")
    with col2:
        st.metric("Na", f"{total_runners}")
    with col3:
        percentile = (1 - better_runners / total_runners) * 100
        st.metric("Percentyl", f"{percentile:.1f}%")

    st.markdown('</div>', unsafe_allow_html=True)

# Nawigacja główna
def main():
    if st.session_state.current_page == 'input':
        page_input()
    elif st.session_state.current_page == 'summary':
        page_summary()
    elif st.session_state.current_page == 'results':
        page_results()

if __name__ == "__main__":
    main()
