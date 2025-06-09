# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pycaret.regression import predict_model

from s3_utils import get_s3_client, load_csv_from_s3, get_prediction_model
from llm_parser import parse_runner_data_with_llm
from utils import seconds_to_hms, seconds_to_ms, create_pace_conversion_table

# --- Konfiguracja strony i inicjalizacja stanu ---
st.set_page_config(page_title="Prognoza Półmaratonu", layout="wide")

def initialize_state():
    """Inicjalizuje stan sesji przy pierwszym uruchomieniu."""
    if 'page' not in st.session_state:
        st.session_state.page = 'input'
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'history_index' not in st.session_state:
        st.session_state.history_index = -1
    if 'runner_data' not in st.session_state:
        st.session_state.runner_data = None
    if 'predicted_time_sec' not in st.session_state:
        st.session_state.predicted_time_sec = None
    if 'current_input' not in st.session_state:
        st.session_state.current_input = "Np. kobieta, 35 lat, tempo na 5km 5'30''"

initialize_state()

# --- Definicje stron (widoków) ---

def render_input_page():
    """Strona 1: Wprowadzanie danych."""
    st.title("🏃 Prognoza Czasu w Półmaratonie")
    st.header("Krok 1: Wprowadź dane")

    tab1, tab2 = st.tabs(["Wprowadzanie Danych", "Pomoc: Tabela Konwersji Tempa"])
    with tab2:
        st.dataframe(create_pace_conversion_table(), use_container_width=True, hide_index=True)

    with tab1:
        st.subheader("Historia wpisów")
        if not st.session_state.history:
            st.info("Brak wpisów w historii. Twój pierwszy wpis zostanie tu zapisany.")

        cols = st.columns([1, 1, 1, 1, 4])
        if cols[0].button("⬅️ Poprzedni", disabled=st.session_state.history_index <= 0):
            st.session_state.history_index -= 1
            st.session_state.current_input = st.session_state.history[st.session_state.history_index]
            st.rerun()
        if cols[1].button("➡️ Następny", disabled=st.session_state.history_index >= len(st.session_state.history) - 1):
            st.session_state.history_index += 1
            st.session_state.current_input = st.session_state.history[st.session_state.history_index]
            st.rerun()
        if cols[2].button("🗑️ Usuń wpis", disabled=st.session_state.history_index == -1):
            st.session_state.history.pop(st.session_state.history_index)
            st.session_state.history_index = min(st.session_state.history_index, len(st.session_state.history) - 1)
            st.session_state.current_input = st.session_state.history[st.session_state.history_index] if st.session_state.history else ""
            st.rerun()
        if cols[3].button("🧹 Wyczyść pole"):
            st.session_state.current_input = ""
            st.rerun()

        st.subheader("Opisz siebie i swoje wyniki")
        user_input = st.text_area(
            "Podaj swój wiek, płeć oraz czas na 5km lub tempo biegu.",
            value=st.session_state.current_input,
            height=100,
            key="runner_input_area",
        )
        st.session_state.current_input = user_input

        if st.button("Przetwórz dane i przejdź dalej ➡️", type="primary"):
            if not user_input or user_input.startswith("Np."):
                st.warning("Proszę wprowadzić dane.")
                return

            with st.spinner("Analiza danych przy użyciu AI..."):
                try:
                    parsed_data = parse_runner_data_with_llm(user_input)
                    st.session_state.runner_data = parsed_data
                    if user_input not in st.session_state.history:
                        st.session_state.history.append(user_input)
                    st.session_state.history_index = st.session_state.history.index(user_input)
                    st.session_state.page = 'summary'
                    st.rerun()
                except ValueError as e:
                    st.error(f"Błąd przetwarzania: {e}")

def render_summary_page():
    """Strona 2: Podsumowanie i predykcja."""
    st.title("📊 Podsumowanie i Predykcja")
    st.header("Krok 2: Weryfikacja danych")

    if not st.session_state.runner_data:
        st.warning("Brak danych biegacza. Wróć do strony głównej.")
        if st.button("⬅️ Wróć"): st.session_state.page = 'input'; st.rerun()
        return

    data = st.session_state.runner_data
    gender_full = "Kobieta" if data['gender'] == 'F' else "Mężczyzna"

    st.subheader("Potwierdź wyodrębnione informacje:")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wiek", f"{data['age']} lat")
    col2.metric("Płeć", gender_full)
    col3.metric("Czas na 5km", seconds_to_ms(data['5_km_sec']))

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Wróć do edycji"):
        st.session_state.page = 'input'
        st.rerun()
    if c2.button("🚀 Oszacuj czas w półmaratonie!", type="primary", use_container_width=True):
        with st.spinner("Ładowanie modelu i wykonywanie predykcji..."):
            model = get_prediction_model()
            if model:
                input_df = pd.DataFrame([data])
                prediction = predict_model(model, data=input_df)
                st.session_state.predicted_time_sec = prediction['prediction_label'].iloc[0]
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Nie udało się załadować modelu. Predykcja niemożliwa.")

def render_results_page():
    """Strona 3: Wyniki i wizualizacja."""
    st.title("🏆 Wyniki Predykcji i Analiza")
    st.header("Krok 3: Zobacz swój potencjalny wynik")

    if st.session_state.predicted_time_sec is None:
        st.error("Brak przewidywanego czasu. Wróć do kroku 2.")
        if st.button("⬅️ Wróć"): st.session_state.page = 'summary'; st.rerun()
        return

    predicted_time_hms = seconds_to_hms(st.session_state.predicted_time_sec)
    st.metric("Przewidywany czas ukończenia półmaratonu:", predicted_time_hms)

    st.markdown("---")
    st.subheader("Gdzie by Cię to uplasowało w Półmaratonie Wrocławskim?")

    s3_client = get_s3_client()
    if not s3_client:
        st.error("Nie można wyświetlić wizualizacji z powodu problemu z połączeniem S3.")
        return

    tabs = st.tabs(["Półmaraton Wrocławski 2024", "Półmaraton Wrocławski 2023"])
    for i, tab in enumerate(tabs):
        with tab:
            year = 2024 - i
            file_key = f"zadanie_9/current/halfmarathon_wroclaw_{year}__final_cleaned_full.csv"

            hist_data = load_csv_from_s3(s3_client, file_key)
            if hist_data is None:
                st.warning(f"Nie udało się załadować danych dla roku {year}.")
                continue

            gender_filter = st.radio(
                "Pokaż wyniki dla:", ("Wszystkich uczestników", "Tylko mojej płci"),
                key=f"gender_filter_{year}", horizontal=True
            )

            filtered_data = hist_data.copy()
            if gender_filter == "Tylko mojej płci":
                filtered_data = hist_data[hist_data['gender'] == st.session_state.runner_data['gender']]

            user_time_sec = st.session_state.predicted_time_sec
            faster_runners = filtered_data[filtered_data['finish_sec'] < user_time_sec].shape[0]
            user_rank = faster_runners + 1
            total_runners = len(filtered_data)

            st.metric(
                label=f"Szacowane miejsce w {year} ({'wszyscy' if gender_filter.startswith('W') else 'w kat. płci'})",
                value=f"{user_rank} / {total_runners + 1}"
            )

            st.write("#### Porównanie na tle innych biegaczy")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(data=filtered_data, x='age', y='finish_sec', alpha=0.3, label='Inni uczestnicy', ax=ax)
            ax.scatter(
                [st.session_state.runner_data['age']], [user_time_sec],
                color='red', s=250, edgecolor='black', marker='*', label='Twój przewidywany wynik'
            )
            ax.set_title(f"Wyniki Półmaratonu {year} vs. Twoja Prognoza", fontsize=16)
            ax.set_xlabel("Wiek", fontsize=12)
            ax.set_ylabel("Czas ukończenia (HH:MM:SS)", fontsize=12)
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.6)

            # Formatowanie osi Y
            y_ticks = ax.get_yticks()
            ax.set_yticklabels([seconds_to_hms(int(s)) for s in y_ticks])
            st.pyplot(fig)

    if st.button("🏁 Rozpocznij od nowa", use_container_width=True):
        # Czyszczenie stanu sesji na potrzeby nowego przebiegu
        keys_to_reset = ['page', 'runner_data', 'predicted_time_sec', 'current_input', 'history', 'history_index']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        initialize_state() # Ponowna inicjalizacja do stanu początkowego
        st.rerun()

# --- Główny router aplikacji ---
PAGES = {
    'input': render_input_page,
    'summary': render_summary_page,
    'results': render_results_page,
}
PAGES[st.session_state.page]()
