import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
from langfuse.decorators import observe
from langfuse.openai import OpenAI
import boto3
from pycaret.regression import load_model, predict_model

from utils import utils_css

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Initialize S3 client
s3 = boto3.client("s3")

BUCKET_NAME = "wk1"

@st.cache_data
def get_model():
    try:
        return load_model("time_sec_model", platform="aws", authentication={"bucket": BUCKET_NAME, "path": "zadanie_9/models"})
    except Exception as e:
        st.error(f"Błąd ładowania modelu: {str(e)}.")
        raise Exception("Nie znaleziono modelu.")

@st.cache_data
def get_full_csv_df(year):
    file_name = f"halfmarathon_wroclaw_{year}__final_cleaned_full.csv"
    s3_file_name = "zadanie_9/current/" + file_name
    local_path = file_name
    try:
        s3.download_file(BUCKET_NAME, s3_file_name, local_path)
    except Exception as e:
        st.error(f"Błąd ładowania csv z maratonem: {str(e)}.")
        raise Exception(f"Błąd ładowania {s3_file_name} do {local_path}")
        pass
    return pd.read_csv(local_path, sep=";")

def html(st, html):
    st.markdown(html, unsafe_allow_html=True)

@dataclass
class RunnerInfo:
    age: int
    sex: str
    time_5k: float  # time in seconds
    pace_5k: str # pace as string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gender": self.sex.upper(),  # Match the model's expected format
            "age": self.age,
            "5_km_sec": self.time_5k
        }

    def sex_str(self) -> str:
        if self.sex == 'F':
            return 'kobieta'
        elif self.sex == 'M':
            return 'mężczyzna'
        else:
            return 'nie podano'

    def time_5k_str(self) -> str:
        """Format seconds to MM:SS"""
        minutes = int(self.time_5k // 60)
        remaining_seconds = int(self.time_5k % 60)
        return f"{minutes}:{remaining_seconds:02d}"

    def pace_5k_str(self) -> str:
        return self.pace_5k if not self.pace_5k is None else 'nie podano'


def parse_time(time_str: str) -> float:
    """Parse time string in format MM:SS to seconds"""
    match = re.match(r"^(\d+)[:](\d{2})$", time_str)
    if not match:
        match = re.match(r"^(\d+)[\"\'](\d{2})[\"\']*$", time_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return minutes * 60 + seconds
    raise ValueError(f"Could not parse time: {time_str}")

@observe()
def parse_user_input(text: str) -> RunnerInfo:
    """Parse user input using OpenAI to extract runner information"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract information about the runner from the text."
                        "Return a JSON object with the following fields:"
                            "age (int - age),"
                            "sex ((possible shortcuts: 'm'='mężczyzna', 'k'='kobieta'), string 'M' for male or 'F' for female),"
                            "time_5k (string in MM:SS format if time given),"
                            "pace_5k (string in MM:SS format if pace given)",
                },
                {
                    "role": "user",
                    "content": text
                },
            ],
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)

        time_5k = data.get("time_5k")
        pace_5k = data.get("pace_5k")
        if time_5k is None and pace_5k is None:
            raise ValueError("Nie podano czasu na 5 km.")
        # Parse time if it's in MM:SS format
        if time_5k:
            time_5k = parse_time(time_5k)
        else:
            time_5k = parse_time(pace_5k) * 5

        if time_5k < 15 + 60 or time_5k > 120 * 60:
            raise ValueError("Podany czas na 5 km przekracza ludzkie pojęcie.")

        sex = data.get("sex")
        if sex is None:
            raise ValueError("Nie podano płci.")
        else:
            if sex in ["k", "K"]:
                sex = 'F'
            if sex in ["m", "M"]:
                sex = 'M'
            if sex not in ["F", "M"]:
                raise ValueError(f"{sex} - spróbuj bardziej wyraźnie określić swoją płeć.")

        age = data.get("age")
        if age is None:
            raise ValueError("Nie podano wieku.")
        else:
            if age < 18 or age > 105:
                raise ValueError("W tym wieku nie możesz startować w maratonie.")

        runner = RunnerInfo(age=age, sex=sex, time_5k=time_5k, pace_5k=pace_5k)

        return runner
    except ValueError as e:
        st.error(f"Zły format danych: {str(e)}")
        raise
    except Exception as e:
        st.error(f"Wystąpił błąd: {str(e)}")
        raise

def main():
    stss = st.session_state
    if "history" not in stss:
        stss.history = [
            "Mam 18 lat i jestem piękna, a moje średnie tempo na 5 km to 4\"59'",
            "Mam 28 lat, nie jestem m, a moje średnie tempo na 5 km to 4\"33'",
            "Jestem 35-letnim mężczyzną, a mój czas na 5 km to 22:30.",
            ""
        ]
        stss.hist_idx = len(stss.history)-1
    if "runner_info" not in stss:
        stss.runner_info = None
    if "page" not in stss:
        stss.page = "input"
    if "prediction_results" not in stss:
        stss.prediction_results = None

    st.set_page_config(
        page_title="Prognoza czasu w półmaratonie",
        page_icon="🏃",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    html(st, utils_css.better_styling_css())

    if stss.page == "input":
        display_input_page()
    elif stss.page == "data":
        display_data_page()
    elif stss.page == "results":
        display_results_page()

def save_input(user_input):
    stss = st.session_state
    if user_input != "":
        if user_input != stss.history[stss.hist_idx]:
            if user_input in stss.history:
                stss.history.remove(user_input)
            if stss.history[len(stss.history)-1] == "":
                stss.history[len(stss.history)-1] = user_input
            else:
                stss.history.append(user_input)
            stss.hist_idx = len(stss.history)-1

def display_input_page():
    html(st, '<h1 class="main-header">🏃 Prognoza czasu w Półmaratonie Wrocławskim</h1>')
    tab1, tab2 = st.tabs(['Prognoza', 'Tempo/Prędkość'])
    with tab1:
        html(st, f'<h3 class="sub-header">💬 Już za chwilę dowiesz się jaki czas uzyskał(a)byś w Półmaratonie Wrocławskim.</h3>')
        html(st, """
            <div class="highlight-box">
                <p>Powiedz coś o sobie, ile masz lat, czy jesteś (m)ężczyzną czy (k)obietą, jaki masz czas (lub jakie jest Twoje tempo) na 5 km.<br>
                W razie wątpliwości skorzystaj z tabeli Tempo/Prędkość.<br>
            </div>
        """)

        stss = st.session_state

        user_input = st.text_area(
            "Opisz siebie i swój czas lub tempo na 5 km",
            stss.history[stss.hist_idx],
            height=120,
            label_visibility="collapsed",
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"👈 poprzedni ({stss.hist_idx})"):
                save_input(user_input)
                if stss.hist_idx > 0:
                    stss.hist_idx -= 1
                    st.rerun()

        with col2:
            if st.button("☄️ wyczyść"):
                if stss.history[len(stss.history)-1] != "":
                    stss.history.append("")
                stss.hist_idx = len(stss.history)-1
                st.rerun()

        with col3:
            if st.button("❌ usuń"):
                if len(stss.history) > 1:
                    del stss.history[stss.hist_idx]
                    if stss.hist_idx >= len(stss.history):
                        stss.hist_idx -= 1
                st.rerun()

        with col4:
            if st.button(f"👉 następny ({len(stss.history)-stss.hist_idx-1})"):
                save_input(user_input)
                if stss.hist_idx < len(stss.history) - 1:
                    stss.hist_idx += 1
                    st.rerun()

        if st.button("🏁 Dalej", key="analyze_btn", use_container_width=True):
            save_input(user_input)
            try:
                st.session_state.runner_info = parse_user_input(user_input)
                st.session_state.page = "data"
                st.rerun()
            except Exception as e:
                html(st, f'<div class="warning-box">❌ Nie udało się przeanalizować danych: {str(e)}</div>')

    with tab2:
        html(st, """
            <table>
                <tr>
                    <th>Tempo min"sec'/km</th><th>Prędkość km/h</th><th></th>
                </tr>
                <tr>
                    <td>3"20'</td><td>18</td><td></td>
                </tr>
                <tr>
                    <td>3"31'</td><td>17</td><td>tak biegają najlepsi</td>
                </tr>
                <tr>
                    <td>3"45'</td><td>16</td><td></td>
                </tr>
                <tr>
                    <td>4"00'</td><td>15</td><td></td>
                </tr>
                <tr>
                    <td>4"17'</td><td>14</td><td></td>
                </tr>
                <tr>
                    <td>4"47'</td><td>13</td><td></td>
                </tr>
                <tr>
                    <td>5"00'</td><td>12</td><td></td>
                </tr>
                <tr>
                    <td>5"27'</td><td>11</td><td></td>
                </tr>
                <tr>
                    <td>6"00'</td><td>10</td><td></td>
                </tr>
                <tr>
                    <td>6"40'</td><td>9</td><td></td>
                </tr>
                <tr>
                    <td>7"30'</td><td>8</td><td></td>
                </tr>
                <tr>
                    <td>8"34'</td><td>7</td><td></td>
                </tr>
                <tr>
                    <td>10"00'</td><td>6</td><td></td>
                </tr>
                <tr>
                    <td>12"00'</td><td>5</td><td></td>
                </tr>
                <tr>
                    <td>15"00'</td><td>4</td><td>tempo marszu</td>
                </tr>
            </table>
        """)

def display_data_page():

    with st.spinner("Analizowanie danych..."):
        runner = st.session_state.runner_info
        html(st, f"""
            <div class="success-box">
                <h6 style="margin-top: 0;">✅ ... i co my tu mamy...</h6>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">👤 Wiek:</td>
                        <td style="padding: 0.5rem;">{runner.age} lat</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">⚧️ Płeć:</td>
                        <td style="padding: 0.5rem;">{runner.sex_str()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">⏱️ Czas na 5 km:</td>
                        <td style="padding: 0.5rem;">{runner.time_5k_str()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">⏱️ Tempo przez 5 km:</td>
                        <td style="padding: 0.5rem;">{runner.pace_5k_str()}</td>
                    </tr>
                </table>
            </div>
        """)

    estimate_button = st.button("🚀 Oszacuj czas w półmaratonie", key="estimate_btn", use_container_width=True)

    if estimate_button:
        with st.spinner("Obliczanie czasu..."):
            try:
                model = get_model()

                input_data = pd.DataFrame([st.session_state.runner_info.to_dict()])

                # ML model prediction
                pred = predict_model(model, data=input_data)
                prediction_seconds = int(pred["prediction_label"].iloc[0])

                st.session_state.prediction_seconds = prediction_seconds

                st.session_state.page = "results"
                st.rerun()

            except Exception as e:
                st.error(f"Nie udało się oszacować czasu półmaratonu: {str(e)}")

    back_button()

def place(year):
    df_all = get_full_csv_df(year)

    runner = st.session_state.runner_info

    kto = 'sami mężczyźni' if runner.sex == 'M' else 'same kobiety'
    optiony = st.radio(label='tu musi coś pisać', options=[f'wszyscy w {year}', kto], horizontal=True)    
    sex = runner.sex if optiony == kto else None

    df_1 = pd.DataFrame(
        {
            'Miejsce': [None],
            '5_km_sec': [None],
            'finish_sec': [st.session_state.prediction_seconds],
            'age': [runner.age],
            'gender': [runner.sex]
        }
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    if sex:
        df = df_all[df_all['gender'] == sex]
    else:
        df = df_all
    sns.scatterplot(data=df, x="finish_sec", y="age", ax=ax, color="lightgray", linewidth=0, alpha=0.5, label="Inni, pozostali")
    label = f"To Ty,🙂 {'tu' if runner.sex == 'M' else 'tu'} najważniejsz{'y' if runner.sex == 'M' else 'a'} 🙂"
    sns.scatterplot(data=df_1, x="finish_sec", y="age", ax=ax, color="red", linewidth=0, alpha=0.8, label=label)
    ax.set_title("Czasy wg wieku")
    ax.legend()
    ax.set_xticklabels([timedelta(seconds=int(x.get_text())) for x in ax.get_xticklabels()])
    ax.set_ylabel("Wiek")
    ax.set_xlabel("Czas")
    plt.tight_layout()
    st.pyplot(fig)    

    df_plus_1 = pd.concat([df, df_1], ignore_index=True)
    df_plus_1.sort_values(by='finish_sec', ascending=True, inplace=True)
    df_plus_1['Miejsce'].interpolate(method='linear', inplace=True)

    if sex:
        df_plus_1['Miejsce'] = df_plus_1['Miejsce'] * df.size / df_all.size

    html(st, "<h6>Poniżej to chyba ilość startujących i Twoje miejsce</h6>")
    df_plus_1[df_plus_1['5_km_sec'].isna()]['Miejsce']

def display_results_page():

    html(st, '<h1 class="main-header">🏆 Wyniki Predykcji Czasu Półmaratonu</h1>')

    runner = st.session_state.runner_info

    html(st, '<h2 class="sub-header">👤 Dane biegacza</h2>')

    col1, col2, col3 = st.columns(3)
    with col1:
        html(st, f"""
            <div class="metric-container">
                <div class="metric-label">👤 Wiek</div>
                <div class="metric-value">{runner.age} lat</div>
            </div>
        """)
    with col2:
        html(st, f"""
            <div class="metric-container">
                <div class="metric-label">⚧️ Płeć</div>
                <div class="metric-value">{runner.sex_str()}</div>
            </div>
        """)
    with col3:
        html(st, f"""
            <div class="metric-container">
                <div class="metric-label">⏱️ Czas 5 km</div>
                <div class="metric-value">{runner.time_5k_str()}</div>
            </div>
        """)
    tab1, tab2, tab3 = st.tabs(["Czas", "Miejsce w 2023", "Miejsce w 2024"])
    with tab1:
        html(st, f"""
            <div>
                <div class="divider"></div>
                <h2 class="sub-header">🔮 Czas</h2>
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="font-size: 2.5rem; font-weight: 700;">{timedelta(seconds=st.session_state.prediction_seconds)}</div>
                </div>
            </div>
        """)

    with tab2:
        place(2023)

    with tab3:
        place(2024)

    back_button()

def back_button():
    html(st, '<div class="divider"></div>')
    if st.button("🔄 Wróć do strony głównej", use_container_width=True):
        st.session_state.runner_info = None
        st.session_state.prediction_results = None
        st.session_state.page = "input"
        st.rerun()


if __name__ == "__main__":
    main()
