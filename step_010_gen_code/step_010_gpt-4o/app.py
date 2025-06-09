import streamlit as st
import pandas as pd
import os
import re
from datetime import timedelta
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
from pycaret.regression import load_model, predict_model

# Load environment variables
load_dotenv()

# Dummy OpenAI client class for demonstration
class OpenAI:
    def __init__(self, api_key):
        self.api_key = api_key

    def extract_information(self, text):
        # Mock response for demonstration purposes
        # Replace this with actual OpenAI call or similar service
        return {
            "age": 30,
            "sex": "M",
            "time_5k": "25:30",
        }

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize S3 client
s3 = boto3.client("s3")
BUCKET_NAME = "wk1"

@st.cache_data
def get_model():
    try:
        return load_model("time_sec_model", platform="aws", authentication={"bucket": BUCKET_NAME, "path": "zadanie_9/models"})
    except Exception as e:
        st.error(f"Error loading model: {str(e)}.")
        raise Exception("Model not found.")

@st.cache_data
def get_full_csv_df(year):
    file_name = f"halfmarathon_wroclaw_{year}__final_cleaned_full.csv"
    s3_file_name = f"zadanie_9/current/{file_name}"
    local_path = file_name
    try:
        s3.download_file(BUCKET_NAME, s3_file_name, local_path)
    except Exception as e:
        st.error(f"Error loading marathon CSV: {str(e)}.")
        raise Exception(f"Error downloading {s3_file_name} to {local_path}")
    return pd.read_csv(local_path, sep=";")

@dataclass
class RunnerInfo:
    age: int
    sex: str
    time_5k: float  # time in seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gender": self.sex.upper(),
            "age": self.age,
            "5_km_sec": self.time_5k
        }

    def sex_str(self) -> str:
        return "kobieta" if self.sex.lower() in ['f', 'kobieta'] else "mężczyzna"

    def time_5k_str(self) -> str:
        minutes = int(self.time_5k // 60)
        seconds = int(self.time_5k % 60)
        return f"{minutes}:{seconds:02d}"

def parse_time(time_str: str) -> float:
    # Parses time string into seconds
    match = re.match(r"^(\d+):(\d{2})$", time_str)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    raise ValueError(f"Could not parse time: {time_str}")

def parse_user_input(text: str) -> RunnerInfo:
    extracted_data = client.extract_information(text)
    age = int(extracted_data.get("age", 0))
    sex = extracted_data.get("sex", "").strip().lower()
    time_5k = parse_time(extracted_data.get("time_5k", ""))

    # Validation
    if not (18 <= age <= 105):
        raise ValueError("Age must be between 18 and 105.")

    if sex not in ["m", "k", "mężczyzna", "kobieta"]:
        raise ValueError("Sex must be recognized as 'M' or 'F'.")

    if not (15 * 60 <= time_5k <= 120 * 60):
        raise ValueError("5 km time should be between 15 to 120 minutes.")

    return RunnerInfo(age=age, sex=sex[0].upper(), time_5k=time_5k)

def main():
    st.set_page_config(
        page_title="Half Marathon Time Predictor",
        page_icon="🏃",
        layout="centered"
    )

    # Initialize session state variables
    st.session_state.setdefault('page', 'input')
    st.session_state.setdefault('history', [""])
    st.session_state.setdefault('history_idx', 0)
    st.session_state.setdefault('runner_info', None)
    st.session_state.setdefault('prediction_seconds', None)

    # Display the appropriate page
    if st.session_state.page == "input":
        display_input_page()
    elif st.session_state.page == "summary":
        display_summary_page()
    elif st.session_state.page == "results":
        display_results_page()

def display_input_page():
    st.title("Wprowadź swoje dane biegacza")

    tab1, tab2 = st.tabs(["Dane wejściowe", "Tabela konwersji"])

    with tab1:
        st.write("Podaj swoje dane:")

        user_input = st.text_area(
            "Wpisz wiek, płeć i czas/tempo na 5 km:",
            st.session_state.history[st.session_state.history_idx],
            height=150
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Poprzedni"):
                if st.session_state.history_idx > 0:
                    st.session_state.history_idx -= 1
                    st.rerun()

        with col2:
            if st.button("Następny"):
                if st.session_state.history_idx < len(st.session_state.history) - 1:
                    st.session_state.history_idx += 1
                    st.rerun()

        with col3:
            if st.button("Wyczyść"):
                user_input = ""
                st.session_state.history[st.session_state.history_idx] = user_input

        with col4:
            if st.button("Usuń"):
                if len(st.session_state.history) > 1:
                    del st.session_state.history[st.session_state.history_idx]
                    st.session_state.history_idx = min(
                        st.session_state.history_idx,
                        len(st.session_state.history) - 1
                    )
                    st.rerun()

        if st.button("Dalej"):
            try:
                st.session_state.runner_info = parse_user_input(user_input)
                st.session_state.page = "summary"
                st.rerun()
            except ValueError as e:
                st.error(f"Błąd: {str(e)}")

    with tab2:
        st.write("Konwersja tempa (min/km na km/h):")
        conversion_data = {
            "Tempo min/km": ["3:30", "4:00", "4:30", "5:00", "5:30", "6:00"],
            "Prędkość km/h": ["17.1", "15.0", "13.3", "12.0", "10.9", "10.0"]
        }
        st.table(conversion_data)

def display_summary_page():
    st.header("Podsumowanie danych")

    runner = st.session_state.runner_info
    st.write(f"Wiek: {runner.age}")
    st.write(f"Płeć: {runner.sex_str()}")
    st.write(f"Czas na 5 km: {runner.time_5k_str()}")

    if st.button("Oszacuj czas w półmaratonie"):
        try:
            model = get_model()
            input_data = pd.DataFrame([runner.to_dict()])
            prediction = predict_model(model, data=input_data)
            st.session_state.prediction_seconds = int(prediction["prediction_label"].iloc[0])
            st.session_state.page = "results"
            st.rerun()
        except Exception as e:
            st.error(f"Błąd predykcji: {str(e)}")

    if st.button("Wróć do wprowadzania danych"):
        st.session_state.page = "input"
        st.rerun()

def display_results_page():
    st.header("Wyniki predykcji")

    prediction_seconds = st.session_state.prediction_seconds
    predicted_time = timedelta(seconds=prediction_seconds)
    st.write(f"Przewidywany czas półmaratonu: {predicted_time}")

    tab1, tab2 = st.tabs(["Wizualizacja 2023", "Wizualizacja 2024"])

    def plot_graph(year: int):
        df = get_full_csv_df(year)
        runner = st.session_state.runner_info

        filter_option = st.radio("Wizualizuj względem:", [f"Wszyscy {year}", "Tylko moja płeć"], horizontal=True)

        if filter_option == "Tylko moja płeć":
            df = df[df['gender'].str.upper() == runner.sex]

        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x="age", y="finish_sec", ax=ax, color="grey", label='Inni biegacze', alpha=0.5)
        ax.scatter(runner.age, st.session_state.prediction_seconds, color="red", label='Twój wynik')
        ax.set_title(f"Czasy półmaratonu - {year}")
        ax.set_xlabel("Wiek")
        ax.set_ylabel("Czas w sekundach")
        ax.legend()

        st.pyplot(fig)

        # Calculate rank by time
        current_time = st.session_state.prediction_seconds
        rank = (df['finish_sec'] < current_time).sum() + 1
        st.write(f"Szacowane miejsce: {rank}/{len(df)}")

    with tab1:
        plot_graph(2023)

    with tab2:
        plot_graph(2024)

    if st.button("Powrót do wprowadzania danych"):
        st.session_state.page = "input"
        st.session_state.runner_info = None
        st.rerun()

if __name__ == "__main__":
    main()