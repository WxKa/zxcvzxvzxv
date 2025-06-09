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

# Initialize OpenAI client (dummy client for example purposes)
class OpenAI:
    def __init__(self, api_key):
        self.api_key = api_key

    def extract_information(self, text):
        # Mock function to simulate OpenAI's response
        return {
            "age": 25,
            "sex": "M",
            "time_5k": "22:30",
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
    s3_file_name = "zadanie_9/current/" + file_name
    local_path = file_name
    try:
        s3.download_file(BUCKET_NAME, s3_file_name, local_path)
    except Exception as e:
        st.error(f"Error loading marathon CSV: {str(e)}.")
        raise Exception(f"Error downloading {s3_file_name} to {local_path}")
    return pd.read_csv(local_path, sep=";")

def html(st, html):
    st.markdown(html, unsafe_allow_html=True)

@dataclass
class RunnerInfo:
    age: int
    sex: str
    time_5k: float  # time in seconds
    pace_5k: str  # pace as string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gender": self.sex.upper(),
            "age": self.age,
            "5_km_sec": self.time_5k
        }

    def sex_str(self) -> str:
        return "kobieta" if self.sex == 'F' else "mężczyzna"

    def time_5k_str(self) -> str:
        minutes = int(self.time_5k // 60)
        seconds = int(self.time_5k % 60)
        return f"{minutes}:{seconds:02d}"

def parse_time(time_str: str) -> float:
    match = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return minutes * 60 + seconds
    raise ValueError(f"Could not parse time: {time_str}")

def parse_user_input(text: str) -> RunnerInfo:
    # Use OpenAI model to extract runner information (mocked for this example)
    user_data = client.extract_information(text)
    time_5k = parse_time(user_data["time_5k"])
    return RunnerInfo(age=user_data["age"], sex=user_data["sex"], time_5k=time_5k, pace_5k="")

def main():
    st.set_page_config(
        page_title="Half Marathon Prediction",
        page_icon="🏃",
        layout="centered"
    )

    st.session_state.setdefault('page', 'input')
    st.session_state.setdefault('history', [])
    st.session_state.setdefault('runner_info', None)
    st.session_state.setdefault('prediction_seconds', None)

    if st.session_state.page == "input":
        display_input_page()
    elif st.session_state.page == "summary":
        display_summary_page()
    elif st.session_state.page == "results":
        display_results_page()

def display_input_page():
    st.title("🏃 Half Marathon Time Prediction")

    user_input = st.text_area("Enter your details (age, sex, 5 km time or pace):", "")

    st.session_state.history.append(user_input)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        if st.button("Clear"):
            user_input = ""

    with col2:
        if st.button("Next"):
            try:
                st.session_state.runner_info = parse_user_input(user_input)
                st.session_state.page = "summary"
                st.experimental_rerun()
            except ValueError as e:
                st.error(f"Input error: {str(e)}")

def display_summary_page():
    st.header("Runner Summary")

    runner = st.session_state.runner_info
    st.write(f"Age: {runner.age}")
    st.write(f"Sex: {runner.sex_str()}")
    st.write(f"5 km Time: {runner.time_5k_str()}")

    if st.button("Predict Half Marathon Time"):
        model = get_model()
        input_data = pd.DataFrame([runner.to_dict()])
        prediction = predict_model(model, data=input_data)
        st.session_state.prediction_seconds = int(prediction["prediction_label"].iloc[0])
        st.session_state.page = "results"
        st.experimental_rerun()

def display_results_page():
    st.header("Prediction Results")
    prediction_seconds = st.session_state.prediction_seconds
    st.write(f"Estimated Half Marathon Time: {timedelta(seconds=prediction_seconds)}")

# Run the app
if __name__ == "__main__":
    main()
    
