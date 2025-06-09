a może skoro to gemini wygenerowało tego prompta, to niech samo go wykona,
dlaczego inne AI mają się z tym męczyć, niech każdy sam radzi sobie ze swoimi problemami:

###### Google AI Studio

źródło: gemini 2.5 flash

##### Gemini 2.5 Pro

Jasne, oto kompletna implementacja aplikacji Streamlit do prognozowania czasu w półmaratonie, zgodna z podanymi wymaganiami.

### Struktura projektu

Aby uruchomić aplikację, potrzebujesz następującej struktury plików:

```
.
├── .env
├── app.py
├── requirements.txt
└── utils.py
```

**1. Plik `.env`:**

Ten plik przechowuje wrażliwe dane. Pamiętaj, aby nigdy nie udostępniać go publicznie.

```ini
# .env
OPENAI_API_KEY="sk-..."
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="eu-central-1"  # lub inny region S3
```

**2. Plik `requirements.txt`:**

Plik z listą wszystkich zależności. Zainstaluj je za pomocą `pip install -r requirements.txt`.

```text
# requirements.txt
streamlit
pandas
boto3
pycaret[full]
langfuse
openai
python-dotenv
matplotlib
seaborn
```

**3. Plik `utils.py`:**

Plik pomocniczy z funkcjami do konwersji czasu, stylizacji CSS i innymi.

```python
# utils.py
import re
import streamlit as st
import pandas as pd
from datetime import timedelta

def better_styling_css():
    """Aplikuje niestandardowe style CSS do aplikacji Streamlit."""
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: #F0F2F6;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #FFFFFF;
            }
        </style>""", unsafe_allow_html=True)

def parse_time_to_seconds(time_str: str) -> int | None:
    """Parsuje czas w formacie MM:SS, M:SS, MM'SS'' do sekund."""
    time_str = time_str.replace("'", "").replace('"', '')
    parts = re.split(r'[:]', time_str)
    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 1:
            return int(parts[0]) # Zakładamy, że to sekundy
    except (ValueError, IndexError):
        return None
    return None

def seconds_to_hms(seconds: int) -> str:
    """Konwertuje sekundy na format HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))

def seconds_to_ms(seconds: int) -> str:
    """Konwertuje sekundy na format MM:SS."""
    td = timedelta(seconds=int(seconds))
    minutes = (td.seconds // 60) % 60
    secs = td.seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def generate_pace_conversion_table() -> pd.DataFrame:
    """Generuje tabelę konwersji tempa na prędkość."""
    paces = []
    for minutes in range(3, 11):
        for seconds in range(0, 60, 5):
            total_seconds_per_km = minutes * 60 + seconds
            speed_kmh = 3600 / total_seconds_per_km
            pace_str = f"{minutes}:{seconds:02d}"
            paces.append({"Tempo (min/km)": pace_str, "Prędkość (km/h)": f"{speed_kmh:.2f}"})
    return pd.DataFrame(paces)

```

**4. Główny plik aplikacji `app.py`:**

To jest serce naszej aplikacji. Zawiera logikę dla wszystkich trzech widoków, obsługę stanu i interakcje z zewnętrznymi usługami (OpenAI, S3).

```python
# app.py
import os
import json
import re
import streamlit as st
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from pycaret.regression import load_model, predict_model
from langfuse.openai import OpenAI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from utils import (
    better_styling_css,
    parse_time_to_seconds,
    seconds_to_hms,
    seconds_to_ms,
    generate_pace_conversion_table,
)

# --- KONFIGURACJA I INICJALIZACJA ---

# Ładowanie zmiennych środowiskowych z pliku .env
load_dotenv()

# Ustawienie stylu strony i tytułu
st.set_page_config(page_title="Prognoza Czasu w Półmaratonie", layout="wide")
better_styling_css()

# Inicjalizacja klienta OpenAI
try:
    client_openai = OpenAI()
except Exception as e:
    st.error(f"Nie udało się zainicjować klienta OpenAI. Sprawdź klucz API. Błąd: {e}")
    client_openai = None

# Konfiguracja S3
S3_BUCKET_NAME = 'wk1'
MODEL_PATH = 'zadanie_9/models/time_sec_model'
DATA_PATH_TEMPLATE = 'zadanie_9/current/halfmarathon_wroclaw_{}__final_cleaned_full.csv'

# Inicjalizacja stanu sesji (kluczowe do nawigacji i przechowywania danych)
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
    st.session_state.current_input = ""


# --- FUNKCJE CACHE'OWANE ---

@st.cache_data
def get_pace_table():
    """Pobiera tabelę konwersji tempa (cache'owana)."""
    return generate_pace_conversion_table()

@st.cache_data(ttl=3600)  # Cache na 1 godzinę
def get_s3_client():
    """Tworzy i zwraca klienta S3, obsługując błędy."""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        # Sprawdzenie, czy wiadro istnieje
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        return s3
    except NoCredentialsError:
        st.error("Błąd: Brak danych uwierzytelniających AWS. Sprawdź plik .env.")
        return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            st.error(f"Błąd: Wiadro S3 '{S3_BUCKET_NAME}' nie istnieje.")
        else:
            st.error(f"Błąd połączenia z S3: {e}")
        return None

@st.cache_data(ttl=3600)
def load_prediction_model(_s3_client, bucket, key):
    """Pobiera model z S3 i ładuje go za pomocą PyCaret."""
    if _s3_client is None:
        return None
    local_model_path = "time_sec_model"
    try:
        _s3_client.download_file(bucket, f"{key}.pkl", f"{local_model_path}.pkl")
        model = load_model(local_model_path)
        os.remove(f"{local_model_path}.pkl")  # Sprzątanie po załadowaniu
        return model
    except ClientError as e:
        st.error(f"Nie można pobrać modelu z S3 (ścieżka: {key}). Błąd: {e}")
        return None
    except Exception as e:
        st.error(f"Błąd podczas ładowania modelu PyCaret: {e}")
        return None

@st.cache_data(ttl=3600)
def load_marathon_data(_s3_client, bucket, key):
    """Pobiera dane historyczne z pliku CSV z S3."""
    if _s3_client is None:
        return None
    try:
        obj = _s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(obj['Body'])
        # Konwersja potrzebnych kolumn na typ numeryczny
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df['time_sec'] = pd.to_numeric(df['time_sec'], errors='coerce')
        df.dropna(subset=['age', 'time_sec'], inplace=True)
        return df
    except ClientError as e:
        st.error(f"Nie można załadować danych historycznych z S3 (ścieżka: {key}). Błąd: {e}")
        return None
    except Exception as e:
        st.error(f"Błąd podczas przetwarzania pliku CSV: {e}")
        return None


# --- FUNKCJE LOGIKI APLIKACJI ---

def extract_runner_data_with_llm(text_input):
    """Używa LLM do ekstrakcji danych z tekstu."""
    if not client_openai:
        st.error("Klient OpenAI nie jest dostępny.")
        return None

    prompt = f"""
    Przeanalizuj poniższy tekst wprowadzony przez użytkownika i wyekstrahuj następujące informacje:
    1. Wiek (age): jako liczba całkowita.
    2. Płeć (gender): jako "M" dla mężczyzny lub "F" dla kobiety.
    3. Czas na 5 km (time_5k) LUB Tempo na 5 km (pace_5k): w formacie "MM:SS" lub "M:SS".

    Tekst użytkownika: "{text_input}"

    Zwróć odpowiedź w formacie JSON. Jeśli brakuje jakiejś informacji, ustaw jej wartość na null.
    Przykłady:
    - Tekst: "Mam 35 lat, jestem kobietą, a moje 5km to 25:30." -> {{"age": 35, "gender": "F", "time_5k": "25:30", "pace_5k": null}}
    - Tekst: "m, 42l, tempo 5'10''" -> {{"age": 42, "gender": "M", "time_5k": null, "pace_5k": "05:10"}}
    - Tekst: "28 lat, czas 5km 22 min 15 sek" -> {{"age": 28, "gender": null, "time_5k": "22:15", "pace_5k": null}}

    JSON:
    """
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        st.error(f"Błąd podczas komunikacji z modelem językowym: {e}")
        return None

def process_and_validate_data(data):
    """Waliduje i przetwarza dane wyekstrahowane przez LLM."""
    errors = []
    validated_data = {}

    # Wiek
    age = data.get('age')
    if age is None:
        errors.append("Nie udało się rozpoznać wieku.")
    elif not (isinstance(age, int) and 18 <= age <= 105):
        errors.append(f"Wiek musi być liczbą całkowitą od 18 do 105 (wykryto: {age}).")
    else:
        validated_data['age'] = age

    # Płeć
    gender = str(data.get('gender')).upper()
    if gender not in ['M', 'F']:
        errors.append(f"Nie udało się rozpoznać płci jako 'M' lub 'F' (wykryto: {data.get('gender')}).")
    else:
        validated_data['gender'] = gender

    # Czas/Tempo na 5 km
    time_5k = data.get('time_5k')
    pace_5k = data.get('pace_5k')
    total_seconds = None

    if time_5k:
        total_seconds = parse_time_to_seconds(time_5k)
    elif pace_5k:
        pace_seconds = parse_time_to_seconds(pace_5k)
        if pace_seconds:
            total_seconds = pace_seconds * 5
    
    if total_seconds is None:
        errors.append("Nie udało się rozpoznać czasu ani tempa na 5 km. Użyj formatu MM:SS lub MM'SS''.")
    elif not (15 * 60 <= total_seconds <= 120 * 60):
        errors.append(f"Czas na 5 km ({seconds_to_ms(total_seconds)}) jest poza realistycznym zakresem (15:00 - 120:00).")
    else:
        validated_data['5_km_sec'] = total_seconds

    return validated_data, errors

def plot_results_distribution(df_history, user_age, user_time_sec, user_gender, filter_by_gender=False):
    """Tworzy wykres rozrzutu z wynikami historycznymi i pozycją użytkownika."""
    
    df_filtered = df_history.copy()
    if filter_by_gender:
        df_filtered = df_filtered[df_filtered['gender'] == user_gender]

    if df_filtered.empty:
        st.warning("Brak danych historycznych dla wybranej płci.")
        return None, None, None

    # Obliczanie miejsca
    faster_runners = df_filtered[df_filtered['time_sec'] < user_time_sec].shape[0]
    rank = faster_runners + 1
    total_runners = len(df_filtered)

    # Tworzenie wykresu
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Wykres rozrzutu dla danych historycznych
    sns.scatterplot(
        data=df_filtered, x='age', y='time_sec', ax=ax,
        alpha=0.3, label='Pozostali uczestnicy', s=20
    )
    
    # Punkt użytkownika
    ax.scatter(
        user_age, user_time_sec, color='red', s=150,
        edgecolor='black', zorder=5, label='Twój przewidywany wynik'
    )
    
    # Stylizacja
    ax.set_title(f"Rozkład wyników Półmaratonu Wrocławskiego (n={total_runners})", fontsize=16)
    ax.set_xlabel("Wiek", fontsize=12)
    ax.set_ylabel("Czas ukończenia", fontsize=12)
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Formatowanie osi Y na czas HH:MM:SS
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda s, _: seconds_to_hms(s)))
    
    plt.tight_layout()
    return fig, rank, total_runners

# --- WIDOKI (STRONY) APLIKACJI ---

def render_input_page():
    """Strona 1: Wprowadzanie danych."""
    st.title("Krok 1: Wprowadź swoje dane")
    
    # --- Historia ---
    st.subheader("Historia wpisów")
    if not st.session_state.history:
        st.info("Brak wpisów w historii.")
    
    cols = st.columns([1, 1, 2, 2])
    
    with cols[0]:
        if st.button("Poprzedni", disabled=st.session_state.history_index <= 0):
            st.session_state.history_index -= 1
            st.session_state.current_input = st.session_state.history[st.session_state.history_index]
            st.rerun()

    with cols[1]:
        if st.button("Następny", disabled=st.session_state.history_index >= len(st.session_state.history) - 1):
            st.session_state.history_index += 1
            st.session_state.current_input = st.session_state.history[st.session_state.history_index]
            st.rerun()
            
    with cols[2]:
        if st.button("Wyczyść bieżący wpis"):
            st.session_state.current_input = ""
            st.rerun()

    with cols[3]:
        if st.button("Usuń wpis z historii", type="primary", disabled=st.session_state.history_index == -1):
            del st.session_state.history[st.session_state.history_index]
            if st.session_state.history:
                st.session_state.history_index = min(st.session_state.history_index, len(st.session_state.history) - 1)
                if st.session_state.history_index > -1:
                    st.session_state.current_input = st.session_state.history[st.session_state.history_index]
                else:
                    st.session_state.current_input = ""
            else:
                st.session_state.history_index = -1
                st.session_state.current_input = ""
            st.rerun()

    # --- Główny formularz i tabela konwersji ---
    tab1, tab2 = st.tabs(["Formularz", "Tabela konwersji tempa"])

    with tab1:
        st.info("Opisz siebie w polu poniżej. Podaj swój wiek, płeć oraz czas lub tempo na 5 km.")
        input_text = st.text_area(
            "Dane biegacza:",
            value=st.session_state.current_input,
            key="user_input_text_area",
            height=150,
            placeholder="Np. 'Jestem mężczyzną w wieku 35 lat, a mój najlepszy czas na 5 km to 24:15.'\n"
                        "lub 'K, 28 lat, tempo na 5km 5'20\"'"
        )
        st.session_state.current_input = input_text

        if st.button("Dalej", type="primary"):
            if not input_text.strip():
                st.warning("Proszę wprowadzić dane.")
                return

            with st.spinner("Przetwarzanie danych..."):
                extracted_data = extract_runner_data_with_llm(input_text)
                if extracted_data:
                    validated_data, errors = process_and_validate_data(extracted_data)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        st.session_state.runner_data = validated_data
                        # Dodaj do historii, jeśli to nowy wpis
                        if input_text not in st.session_state.history:
                            st.session_state.history.append(input_text)
                            st.session_state.history_index = len(st.session_state.history) - 1
                        st.session_state.page = 'summary'
                        st.rerun()

    with tab2:
        st.subheader("Konwersja tempa (min/km) na prędkość (km/h)")
        st.dataframe(get_pace_table(), use_container_width=True, hide_index=True)

def render_summary_page():
    """Strona 2: Podsumowanie i przycisk predykcji."""
    st.title("Krok 2: Podsumowanie danych")
    
    data = st.session_state.runner_data
    if not data:
        st.warning("Brak danych biegacza. Wróć do kroku 1.")
        if st.button("Powrót"):
            st.session_state.page = 'input'
            st.rerun()
        return

    gender_str = "Kobieta" if data['gender'] == 'F' else "Mężczyzna"
    
    st.subheader("Zweryfikowane dane:")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wiek", f"{data['age']} lat")
    col2.metric("Płeć", gender_str)
    col3.metric("Czas na 5 km", seconds_to_ms(data['5_km_sec']))

    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Powrót do wprowadzania danych"):
            st.session_state.page = 'input'
            st.rerun()
    with col_btn2:
        if st.button("Oszacuj czas w półmaratonie", type="primary"):
            with st.spinner("Ładowanie modelu i wykonywanie predykcji..."):
                s3 = get_s3_client()
                if s3:
                    model = load_prediction_model(s3, S3_BUCKET_NAME, MODEL_PATH)
                    if model:
                        input_df = pd.DataFrame([data])
                        prediction = predict_model(model, data=input_df)
                        predicted_seconds = prediction['prediction_label'].iloc[0]
                        st.session_state.predicted_time_sec = predicted_seconds
                        st.session_state.page = 'results'
                        st.rerun()
                    else:
                        st.error("Nie udało się załadować modelu predykcyjnego.")
                else:
                    st.error("Nie udało się połączyć z S3.")

def render_results_page():
    """Strona 3: Wyniki i wizualizacja."""
    st.title("Krok 3: Wyniki prognozy")
    
    if st.session_state.predicted_time_sec is None or st.session_state.runner_data is None:
        st.warning("Brak wyników predykcji. Wróć do strony głównej.")
        if st.button("Powrót do strony głównej"):
            st.session_state.page = 'input'
            st.rerun()
        return

    predicted_time_hms = seconds_to_hms(st.session_state.predicted_time_sec)
    st.success(f"**Twój przewidywany czas w półmaratonie to:**")
    st.metric(label="Przewidywany czas", value=predicted_time_hms)

    st.markdown("---")
    st.subheader("Twoja pozycja względem historycznych wyników")

    s3 = get_s3_client()
    if not s3:
        st.error("Nie można wyświetlić wizualizacji z powodu problemów z połączeniem S3.")
        return

    tabs = st.tabs(["Półmaraton Wrocławski 2024", "Półmaraton Wrocławski 2023"])
    years = [2024, 2023]
    
    for i, tab in enumerate(tabs):
        with tab:
            year = years[i]
            data_key = DATA_PATH_TEMPLATE.format(year)
            df_history = load_marathon_data(s3, S3_BUCKET_NAME, data_key)

            if df_history is not None:
                filter_choice = st.radio(
                    f"Porównaj z:",
                    options=["Wszystkimi biegaczami", "Tylko biegaczami tej samej płci"],
                    key=f"radio_{year}",
                    horizontal=True
                )
                
                filter_gender = (filter_choice == "Tylko biegaczami tej samej płci")

                fig, rank, total = plot_results_distribution(
                    df_history,
                    st.session_state.runner_data['age'],
                    st.session_state.predicted_time_sec,
                    st.session_state.runner_data['gender'],
                    filter_by_gender=filter_gender
                )
                
                if fig:
                    st.pyplot(fig)
                    st.info(f"**Twoje szacowane miejsce w tej grupie:** **{rank}** na **{total}** uczestników.")
                else:
                    st.warning(f"Nie można wygenerować wykresu dla roku {year}.")
            else:
                st.warning(f"Brak danych historycznych dla roku {year}.")

    if st.button("Powrót do strony głównej"):
        # Resetowanie stanu dla nowego cyklu
        st.session_state.page = 'input'
        st.session_state.runner_data = None
        st.session_state.predicted_time_sec = None
        st.rerun()

# --- GŁÓWNA LOGIKA NAWIGACJI ---

if st.session_state.page == 'input':
    render_input_page()
elif st.session_state.page == 'summary':
    render_summary_page()
elif st.session_state.page == 'results':
    render_results_page()
```

### Jak uruchomić aplikację?

1.  Upewnij się, że masz poprawnie skonfigurowany plik `.env` z kluczami API i dostępem do AWS.
2.  Zainstaluj wszystkie pakiety z pliku `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  Uruchom aplikację Streamlit z terminala w głównym folderze projektu:
    ```bash
    streamlit run app.py
    ```

Aplikacja otworzy się w przeglądarce, gotowa do użycia. Użytkownik będzie mógł przechodzić przez kolejne kroki, a aplikacja będzie zarządzać stanem i danymi zgodnie z podanymi wytycznymi.
