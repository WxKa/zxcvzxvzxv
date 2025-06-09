Jasne, oto kompletna implementacja aplikacji Streamlit do prognozowania czasu w półmaratonie, zgodnie z podanymi wytycznymi. Aplikacja jest podzielona na logiczne moduły, aby zachować czytelność i łatwość w zarządzaniu kodem.

### Struktura projektu

Sugerowana struktura plików wygląda następująco:

```
.
├── .env                  # Plik ze zmiennymi środowiskowymi
├── app.py                # Główny plik aplikacji Streamlit
├── llm_parser.py         # Moduł do parsowania danych przez LLM
├── requirements.txt      # Zależności projektu
├── s3_utils.py           # Narzędzia do obsługi S3
└── utils.py              # Funkcje pomocnicze (np. konwersja czasu)
```

### Krok 1: Plik `.env`

Utwórz plik `.env` w głównym katalogu projektu i umieść w nim swoje klucze.

```ini
# .env
OPENAI_API_KEY="sk-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="eu-central-1" # lub inny region, w którym jest bucket
```

### Krok 2: Plik `requirements.txt`

```text
# requirements.txt
streamlit
pandas
numpy
boto3
pycaret[full]
langfuse
openai
python-dotenv
matplotlib
seaborn
```

Zainstaluj zależności: `pip install -r requirements.txt`

### Krok 3: Kod źródłowy

#### Plik `s3_utils.py`

Ten moduł będzie zawierał funkcje do interakcji z Amazon S3. Użycie `@st.cache_data` jest kluczowe dla wydajności.

```python
# s3_utils.py
import os
import pandas as pd
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from pycaret.regression import load_model
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

# Konfiguracja klienta BOTO3
S3_BUCKET = "wk1"

@st.cache_resource
def get_s3_client():
    """Tworzy i zwraca klienta S3, cachowane dla całej sesji."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "eu-central-1")
        )
        # Sprawdzenie połączenia poprzez listowanie bucketów
        s3_client.list_buckets()
        return s3_client
    except (NoCredentialsError, ClientError) as e:
        st.error(f"Błąd konfiguracji AWS S3: Nie można połączyć się z S3. Sprawdź swoje klucze dostępu w pliku .env. Błąd: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache na 1 godzinę
def load_csv_from_s3(_s3_client, file_key: str) -> pd.DataFrame | None:
    """Ładuje plik CSV z S3 do ramki danych Pandas."""
    if not _s3_client:
        return None
    try:
        obj = _s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        return pd.read_csv(obj['Body'])
    except ClientError as e:
        st.error(f"Błąd podczas pobierania pliku CSV z S3 ('{file_key}'): {e}")
        return None
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd podczas przetwarzania pliku CSV: {e}")
        return None

@st.cache_data(ttl=3600) # Cache na 1 godzinę
def download_model_from_s3(_s3_client, file_key: str, local_path: str):
    """Pobiera plik modelu z S3 i zapisuje go lokalnie."""
    if not _s3_client:
        return False
    try:
        _s3_client.download_file(S3_BUCKET, file_key, local_path)
        return True
    except ClientError as e:
        st.error(f"Błąd podczas pobierania modelu z S3 ('{file_key}'): {e}")
        return False

@st.cache_resource
def get_prediction_model():
    """Ładuje model PyCaret, pobierając go z S3 w razie potrzeby."""
    s3_client = get_s3_client()
    if not s3_client:
        return None

    model_s3_key = "zadanie_9/models/time_sec_model"
    local_model_path = "time_sec_model"

    if not os.path.exists(f"{local_model_path}.pkl"):
        st.info("Model nie został znaleziony lokalnie. Pobieranie z S3...")
        with st.spinner("Pobieranie modelu..."):
            if not download_model_from_s3(s3_client, f"{model_s3_key}.pkl", f"{local_model_path}.pkl"):
                return None
    
    try:
        model = load_model(local_model_path)
        return model
    except Exception as e:
        st.error(f"Nie udało się załadować modelu PyCaret. Błąd: {e}")
        return None

```

#### Plik `llm_parser.py`

Moduł odpowiedzialny za ekstrakcję danych z tekstu użytkownika przy użyciu GPT.

```python
# llm_parser.py
import os
import json
import re
from langfuse.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Inicjalizacja klienta OpenAI z Langfuse
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
)

def parse_runner_data_with_llm(text_input: str) -> dict:
    """Używa LLM do ekstrakcji i walidacji danych biegacza."""
    
    system_prompt = f"""
    Twoim zadaniem jest precyzyjne wyekstrahowanie informacji o biegaczu z podanego tekstu.
    Zwróć odpowiedź wyłącznie w formacie JSON. Nie dodawaj żadnych wyjaśnień ani dodatkowego tekstu.

    Oczekiwany format wyjściowy JSON:
    {{
      "age": <liczba całkowita>,
      "gender": <"M" lub "F">,
      "time_5k_sec": <liczba zmiennoprzecinkowa>
    }}

    Zasady ekstrakcji i walidacji:
    1.  **age**: Wiek musi być liczbą całkowitą z zakresu od 18 do 105.
    2.  **gender**: Płeć musi być zmapowana na "M" (dla mężczyzny, m, male, facet itp.) lub "F" (dla kobiety, k, female, kobieta itp.).
    3.  **time_5k_sec**:
        -   Jeśli podano czas na 5km (np. "25:30", "25 min 30 sek"), przekonwertuj go na łączną liczbę sekund.
        -   Jeśli podano tempo na 1km (np. "5'06''", "5:06/km", "tempo 5 minut 6 sekund"), najpierw przekonwertuj je na sekundy na kilometr, a następnie pomnóż przez 5, aby uzyskać czas na 5km w sekundach.
        -   Wynikowy czas na 5km w sekundach musi być realistyczny. Zaakceptuj wartości od 900 sekund (15 minut) do 7200 sekund (120 minut).
        -   Jeśli nie uda się wyekstrahować żadnej z tych informacji, zwróć `null` dla odpowiedniego pola.

    Przykłady:
    -   Tekst: "mam 35 lat, jestem kobietą, a moje 5km biegam w 28:15" -> {{"age": 35, "gender": "F", "time_5k_sec": 1695.0}}
    -   Tekst: "mężczyzna, 42l. tempo na piątkę 5'30''" -> {{"age": 42, "gender": "M", "time_5k_sec": 1650.0}}
    -   Tekst: "wiek 29, płeć M, czas 5km 21 minut" -> {{"age": 29, "gender": "M", "time_5k_sec": 1260.0}}
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input},
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        response_json = json.loads(completion.choices[0].message.content)
        
        # Walidacja danych
        age = response_json.get("age")
        gender = response_json.get("gender")
        time_5k_sec = response_json.get("time_5k_sec")

        errors = []
        if not (isinstance(age, int) and 18 <= age <= 105):
            errors.append(f"Wiek ({age}) musi być liczbą całkowitą z zakresu 18-105.")
        if gender not in ["M", "F"]:
            errors.append(f"Płeć ({gender}) musi być rozpoznana jako 'M' lub 'F'.")
        if not (isinstance(time_5k_sec, (int, float)) and 900 <= time_5k_sec <= 7200):
             errors.append(f"Czas/Tempo na 5km musi być w realistycznym zakresie (15 - 120 minut). Otrzymano: {time_5k_sec/60:.2f} min.")
        
        if errors:
            raise ValueError("Błędy walidacji: " + " ".join(errors))
            
        return {
            "age": age,
            "gender": gender,
            "5_km_sec": float(time_5k_sec)
        }

    except json.JSONDecodeError:
        raise ValueError("Model LLM zwrócił niepoprawny format JSON. Spróbuj sformułować dane inaczej.")
    except Exception as e:
        raise ValueError(f"Błąd podczas przetwarzania danych przez LLM: {e}")

```

#### Plik `utils.py`

Zawiera funkcje pomocnicze, np. do formatowania czasu.

```python
# utils.py
import pandas as pd

def seconds_to_hms(seconds: float) -> str:
    """Konwertuje sekundy na format HH:MM:SS."""
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def seconds_to_ms(seconds: float) -> str:
    """Konwertuje sekundy na format MM:SS."""
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def create_pace_conversion_table() -> pd.DataFrame:
    """Tworzy tabelę konwersji tempa na prędkość."""
    paces_min_sec = []
    for minutes in range(3, 11):
        for seconds in [0, 15, 30, 45]:
            paces_min_sec.append(f"{minutes}:{seconds:02d}")

    data = []
    for pace_str in paces_min_sec:
        minutes, seconds = map(int, pace_str.split(':'))
        total_seconds_per_km = minutes * 60 + seconds
        speed_kmh = 3600 / total_seconds_per_km
        data.append({"Tempo (min:sek/km)": pace_str, "Prędkość (km/h)": f"{speed_kmh:.2f}"})
    
    return pd.DataFrame(data)
```

#### Plik `app.py`

Główny plik aplikacji, który łączy wszystkie elementy.

```python
# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pycaret.regression import predict_model

# Importy z lokalnych modułów
from s3_utils import get_s3_client, load_csv_from_s3, get_prediction_model
from llm_parser import parse_runner_data_with_llm
from utils import seconds_to_hms, seconds_to_ms, create_pace_conversion_table

# --- Konfiguracja strony i stanu ---
st.set_page_config(page_title="Prognoza Czasu w Półmaratonie", layout="wide")

# Inicjalizacja stanu sesji
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
    st.session_state.current_input = "Np. mężczyzna, 35 lat, czas na 5km 25:30"


# --- Funkcje renderujące widoki (strony) ---

def render_input_page():
    st.title("🏃 Prognoza Czasu w Półmaratonie")
    st.header("Krok 1: Wprowadź swoje dane")

    tab1, tab2 = st.tabs(["Wprowadzanie danych", "Tabela konwersji tempa"])

    with tab2:
        st.subheader("Tabela Konwersji Tempo ↔ Prędkość")
        st.dataframe(create_pace_conversion_table(), use_container_width=True, hide_index=True)

    with tab1:
        # --- Sekcja historii ---
        st.subheader("Historia wpisów")
        if not st.session_state.history:
            st.info("Brak wpisów w historii.")
        
        cols = st.columns([1, 1, 1, 1, 5])
        with cols[0]:
            if st.button("⬅️ Poprzedni", disabled=st.session_state.history_index <= 0):
                st.session_state.history_index -= 1
                st.session_state.current_input = st.session_state.history[st.session_state.history_index]
                st.rerun()

        with cols[1]:
            if st.button("➡️ Następny", disabled=st.session_state.history_index >= len(st.session_state.history) - 1):
                st.session_state.history_index += 1
                st.session_state.current_input = st.session_state.history[st.session_state.history_index]
                st.rerun()
        
        with cols[2]:
            if st.button("🗑️ Usuń", disabled=st.session_state.history_index == -1):
                st.session_state.history.pop(st.session_state.history_index)
                if st.session_state.history_index >= len(st.session_state.history):
                    st.session_state.history_index = len(st.session_state.history) - 1
                if st.session_state.history_index == -1:
                    st.session_state.current_input = "Np. mężczyzna, 35 lat, czas na 5km 25:30"
                else:
                    st.session_state.current_input = st.session_state.history[st.session_state.history_index]
                st.rerun()
        
        with cols[3]:
            if st.button("🧹 Wyczyść"):
                st.session_state.current_input = ""
                st.rerun()

        # --- Pole wprowadzania danych ---
        st.subheader("Opisz siebie i swoje wyniki")
        st.session_state.current_input = st.text_area(
            "Podaj swój wiek, płeć oraz czas na 5km lub tempo biegu.",
            value=st.session_state.current_input,
            height=100,
            key="runner_input_area"
        )
        
        if st.button("Dalej ➡️", type="primary", use_container_width=True):
            user_input = st.session_state.current_input
            if not user_input or user_input == "Np. mężczyzna, 35 lat, czas na 5km 25:30":
                st.warning("Proszę wprowadzić dane.")
                return

            with st.spinner("Przetwarzanie danych przy użyciu AI..."):
                try:
                    parsed_data = parse_runner_data_with_llm(user_input)
                    st.session_state.runner_data = parsed_data
                    
                    # Dodaj do historii, jeśli to nowy wpis
                    if user_input not in st.session_state.history:
                        st.session_state.history.append(user_input)
                    st.session_state.history_index = st.session_state.history.index(user_input)

                    st.session_state.page = 'summary'
                    st.rerun()
                except ValueError as e:
                    st.error(f"Błąd przetwarzania: {e}")
                except Exception as e:
                    st.error(f"Wystąpił nieoczekiwany błąd: {e}")

def render_summary_page():
    st.title("📊 Podsumowanie i Predykcja")
    st.header("Krok 2: Sprawdź dane i oszacuj czas")

    if st.session_state.runner_data:
        data = st.session_state.runner_data
        gender_full = "Kobieta" if data['gender'] == 'F' else "Mężczyzna"
        
        st.subheader("Twoje dane:")
        col1, col2, col3 = st.columns(3)
        col1.metric("Wiek", f"{data['age']} lat")
        col2.metric("Płeć", gender_full)
        col3.metric("Czas na 5km", seconds_to_ms(data['5_km_sec']))
        
        cols = st.columns([1, 2, 1])
        with cols[0]:
            if st.button("⬅️ Wróć do edycji"):
                st.session_state.page = 'input'
                st.rerun()
        
        with cols[1]:
            if st.button("🚀 Oszacuj czas w półmaratonie", type="primary", use_container_width=True):
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

    else:
        st.warning("Brak danych biegacza. Wróć do strony głównej.")
        if st.button("⬅️ Wróć na stronę główną"):
            st.session_state.page = 'input'
            st.rerun()

def render_results_page():
    st.title("🏆 Wyniki Predykcji")
    st.header("Krok 3: Analiza Twojego potencjalnego wyniku")

    if st.session_state.predicted_time_sec is None:
        st.error("Brak przewidywanego czasu. Wróć do kroku 2.")
        if st.button("⬅️ Wróć"):
            st.session_state.page = 'summary'
            st.rerun()
        return

    predicted_time_hms = seconds_to_hms(st.session_state.predicted_time_sec)
    st.subheader("Przewidywany czas ukończenia półmaratonu:")
    st.metric("Twój szacowany czas", predicted_time_hms)
    
    st.markdown("---")
    st.subheader("Gdzie plasowałbyś/plasowałabyś się w Półmaratonie Wrocławskim?")

    tabs = st.tabs(["Wyniki 2024", "Wyniki 2023"])
    years = [2024, 2023]

    s3_client = get_s3_client()
    if not s3_client:
        st.error("Nie można wyświetlić wizualizacji z powodu problemu z połączeniem S3.")
        return

    for i, tab in enumerate(tabs):
        with tab:
            year = years[i]
            file_key = f"zadanie_9/current/halfmarathon_wroclaw_{year}__final_cleaned_full.csv"
            
            with st.spinner(f"Ładowanie danych historycznych za rok {year}..."):
                hist_data = load_csv_from_s3(s3_client, file_key)

            if hist_data is None:
                st.warning(f"Nie udało się załadować danych dla roku {year}.")
                continue

            gender_filter = st.radio(
                "Pokaż wyniki dla:",
                ("Wszystkich", "Tylko mojej płci"),
                key=f"gender_filter_{year}",
                horizontal=True
            )

            filtered_data = hist_data.copy()
            user_gender = st.session_state.runner_data['gender']
            if gender_filter == "Tylko mojej płci":
                filtered_data = hist_data[hist_data['gender'] == user_gender]

            # Obliczanie miejsca
            user_time = st.session_state.predicted_time_sec
            faster_runners = filtered_data[filtered_data['time_sec'] < user_time].shape[0]
            total_runners = len(filtered_data)
            user_rank = faster_runners + 1

            st.metric(
                label=f"Szacowane miejsce w {year} ({gender_filter.lower()})",
                value=f"{user_rank} / {total_runners + 1}"
            )

            # Wizualizacja
            st.write("#### Rozkład wyników wg wieku")
            fig, ax = plt.subplots(figsize=(12, 7))
            sns.scatterplot(
                data=filtered_data,
                x='age',
                y='time_sec',
                alpha=0.3,
                label='Pozostali uczestnicy',
                ax=ax
            )
            
            user_age = st.session_state.runner_data['age']
            ax.scatter(
                [user_age], [user_time],
                color='red',
                s=200,
                edgecolor='black',
                marker='*',
                label='Twój przewidywany wynik'
            )
            
            ax.set_title(f"Wyniki Półmaratonu Wrocławskiego {year} vs Twój wynik")
            ax.set_xlabel("Wiek")
            ax.set_ylabel("Czas ukończenia (sekundy)")
            ax.legend()
            plt.grid(True, linestyle='--', alpha=0.6)
            
            # Konwersja y-tick na format MM:SS
            ax.set_yticklabels([seconds_to_hms(int(s)) for s in ax.get_yticks()])

            st.pyplot(fig)
            plt.close(fig)

    if st.button("🏁 Rozpocznij od nowa"):
        # Reset kluczowych stanów
        st.session_state.page = 'input'
        st.session_state.runner_data = None
        st.session_state.predicted_time_sec = None
        st.rerun()


# --- Główny router aplikacji ---
if st.session_state.page == 'input':
    render_input_page()
elif st.session_state.page == 'summary':
    render_summary_page()
elif st.session_state.page == 'results':
    render_results_page()

```

### Jak uruchomić aplikację?

1.  Upewnij się, że wszystkie pliki (`.env`, `app.py`, `llm_parser.py`, `s3_utils.py`, `utils.py`, `requirements.txt`) znajdują się w tym samym katalogu.
2.  Zainstaluj zależności: `pip install -r requirements.txt`.
3.  Wypełnij plik `.env` swoimi kluczami dostępu.
4.  Uruchom aplikację z terminala za pomocą polecenia: `streamlit run app.py`.

Aplikacja uruchomi się w przeglądarce, prowadząc użytkownika przez trzyetapowy proces: od wprowadzenia danych, przez ich weryfikację i predykcję, aż po wizualizację wyników na tle historycznych danych.
