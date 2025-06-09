Doskonale. Poniżej znajduje się kompletna implementacja aplikacji Streamlit, podzielona na logiczne moduły zgodnie z najlepszymi praktykami. Struktura ta zapewnia czytelność kodu i łatwość w jego dalszym rozwoju.

### Struktura projektu

Zalecana struktura plików dla tego projektu:

```
.
├── .env                  # Plik konfiguracyjny ze zmiennymi środowiskowymi
├── app.py                # Główny plik aplikacji
├── llm_parser.py         # Moduł do interakcji z LLM
├── requirements.txt      # Lista zależności projektu
├── s3_utils.py           # Narzędzia do obsługi S3 i modelu
└── utils.py              # Funkcje pomocnicze (np. konwersje, tabele)
```

---

### Krok 1: Plik `.env` (Zmienne Środowiskowe)

Utwórz plik `.env` w głównym katalogu projektu i wklej do niego swoje klucze. Aplikacja załaduje je automatycznie.

```ini
# .env
OPENAI_API_KEY="sk-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
AWS_ACCESS_KEY_ID="TWOJ_KLUCZ_DOSTEPU_AWS"
AWS_SECRET_ACCESS_KEY="TWOJ_SEKRETNY_KLUCZ_AWS"
AWS_REGION="eu-central-1" # Region, w którym znajduje się bucket S3
```

---

### Krok 2: Plik `requirements.txt` (Zależności)

Zapisz poniższą listę w pliku `requirements.txt`, a następnie zainstaluj pakiety poleceniem: `pip install -r requirements.txt`.

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

---

### Krok 3: Kod źródłowy aplikacji

#### Plik `s3_utils.py`
Ten moduł obsługuje całą komunikację z AWS S3, włącznie z pobieraniem danych i modelu. Użycie dekoratorów cache'ujących (`@st.cache_resource`, `@st.cache_data`) jest kluczowe dla wydajności.

```python
# s3_utils.py
import os
import pandas as pd
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from pycaret.regression import load_model
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "wk1"

@st.cache_resource
def get_s3_client():
    """Tworzy i zwraca klienta S3. Wynik jest cachowany dla całej sesji."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        s3_client.list_buckets()  # Sprawdzenie poprawności połączenia
        return s3_client
    except (NoCredentialsError, ClientError) as e:
        st.error(f"Błąd konfiguracji AWS S3. Sprawdź swoje klucze w pliku .env. Błąd: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache na 1 godzinę
def load_csv_from_s3(_s3_client, file_key: str) -> pd.DataFrame | None:
    """Ładuje plik CSV z S3, używając separatora ';'. Wynik jest cachowany."""
    if not _s3_client:
        return None
    try:
        obj = _s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        # Zgodnie z wymaganiem, używamy separatora ';'
        return pd.read_csv(obj['Body'], sep=';')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            st.error(f"Nie znaleziono pliku w S3: {file_key}")
        else:
            st.error(f"Błąd S3 podczas pobierania pliku '{file_key}': {e}")
        return None
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd podczas przetwarzania pliku CSV: {e}")
        return None

@st.cache_data(ttl=3600)
def download_file_from_s3(_s3_client, file_key: str, local_path: str):
    """Pobiera plik z S3 i zapisuje go lokalnie."""
    if not _s3_client:
        return False
    try:
        _s3_client.download_file(S3_BUCKET, file_key, local_path)
        return True
    except ClientError as e:
        st.error(f"Błąd S3 podczas pobierania modelu '{file_key}': {e}")
        return False

@st.cache_resource
def get_prediction_model():
    """Ładuje model PyCaret, pobierając go z S3, jeśli nie istnieje lokalnie."""
    s3_client = get_s3_client()
    if not s3_client:
        return None

    model_s3_key = "zadanie_9/models/time_sec_model.pkl"
    local_model_path_base = "time_sec_model"
    local_model_path_pkl = f"{local_model_path_base}.pkl"

    if not os.path.exists(local_model_path_pkl):
        st.info("Model nie istnieje lokalnie. Pobieranie z S3...")
        with st.spinner("Pobieranie modelu... To może chwilę potrwać."):
            if not download_file_from_s3(s3_client, model_s3_key, local_model_path_pkl):
                return None
    
    try:
        model = load_model(local_model_path_base)
        st.success("Model predykcyjny został pomyślnie załadowany.")
        return model
    except Exception as e:
        st.error(f"Nie udało się załadować modelu PyCaret z pliku. Błąd: {e}")
        return None
```

#### Plik `llm_parser.py`
Ten moduł zawiera logikę parsowania tekstu użytkownika przy użyciu modelu językowego.

```python
# llm_parser.py
import os
import json
from langfuse.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Zgodnie z poleceniem, używamy klienta Langfuse
client = OpenAI(
    # Klucze Langfuse są opcjonalne, ale pozwalają na śledzenie wywołań
    # public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    # secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
)

def parse_runner_data_with_llm(text_input: str) -> dict:
    """Używa LLM do ekstrakcji i walidacji danych biegacza z tekstu."""
    
    system_prompt = """
    Twoim zadaniem jest precyzyjne wyekstrahowanie informacji o biegaczu z podanego tekstu.
    Zwróć odpowiedź WYŁĄCZNIE w formacie JSON. Bez żadnych dodatkowych wyjaśnień.

    Oczekiwany format wyjściowy JSON i jego klucze:
    {
      "age": <liczba całkowita>,
      "gender": <"M" lub "F">,
      "5_km_sec": <liczba zmiennoprzecinkowa>
    }

    Zasady ekstrakcji i walidacji:
    1.  **age**: Wiek musi być liczbą całkowitą w przedziale od 18 do 105.
    2.  **gender**: Płeć musi być zmapowana na "M" (dla mężczyzny, m, male) lub "F" (dla kobiety, k, female).
    3.  **5_km_sec**: 
        -   Jeśli podano czas na 5 km (np. "25:30", "25 min 30 sek"), przelicz go na łączną liczbę sekund.
        -   Jeśli podano tempo na 1 km (np. "5'06''", "5:06/km", "tempo 5 minut 6 sekund"), najpierw przelicz je na sekundy na kilometr, a następnie pomnóż przez 5, aby uzyskać czas na 5 km w sekundach.
        -   Wynikowy czas na 5 km w sekundach musi mieścić się w zakresie od 900 (15 minut) do 7200 (120 minut).
    -   Jeśli którejś informacji nie da się wyekstrahować, zwróć `null` dla tego pola.
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
        
        # Walidacja po stronie Pythona - NIGDY nie ufaj w 100% LLM
        errors = []
        age = response_json.get("age")
        gender = response_json.get("gender")
        time_5k_sec = response_json.get("5_km_sec")

        if not (isinstance(age, int) and 18 <= age <= 105):
            errors.append(f"Wiek musi być liczbą całkowitą z zakresu 18-105 (otrzymano: {age}).")
        if gender not in ["M", "F"]:
            errors.append(f"Płeć musi być 'M' lub 'F' (otrzymano: {gender}).")
        if not (isinstance(time_5k_sec, (int, float)) and 900 <= time_5k_sec <= 7200):
            time_min = f"{time_5k_sec / 60:.1f} min" if time_5k_sec else "brak"
            errors.append(f"Czas na 5km musi być w realistycznym zakresie [15, 120] minut (otrzymano: {time_min}).")
        
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
        raise ValueError(f"Błąd podczas parsowania danych przez AI: {e}")
```

#### Plik `utils.py`
Moduł na funkcje pomocnicze, które utrzymują główny plik aplikacji w czystości.

```python
# utils.py
import pandas as pd

def seconds_to_hms(seconds: float) -> str:
    """Konwertuje sekundy na format HH:MM:SS."""
    if pd.isna(seconds): return "N/A"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def seconds_to_ms(seconds: float) -> str:
    """Konwertuje sekundy na format MM:SS."""
    if pd.isna(seconds): return "N/A"
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def create_pace_conversion_table() -> pd.DataFrame:
    """Tworzy tabelę konwersji tempa na prędkość do wyświetlenia w aplikacji."""
    paces_min_sec = []
    for minutes in range(3, 10):
        for seconds in [0, 15, 30, 45]:
            paces_min_sec.append(f"{minutes}:{seconds:02d}")

    data = []
    for pace_str in paces_min_sec:
        minutes, seconds = map(int, pace_str.split(':'))
        total_seconds_per_km = minutes * 60 + seconds
        speed_kmh = 3600 / total_seconds_per_km
        data.append({"Tempo (min:sek / km)": pace_str, "Prędkość (km/h)": f"{speed_kmh:.2f}"})
    
    return pd.DataFrame(data)
```

#### Plik `app.py`
Główny plik aplikacji, który spina wszystko w całość.

```python
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
            faster_runners = filtered_data[filtered_data['time_sec'] < user_time_sec].shape[0]
            user_rank = faster_runners + 1
            total_runners = len(filtered_data)

            st.metric(
                label=f"Szacowane miejsce w {year} ({'wszyscy' if gender_filter.startswith('W') else 'w kat. płci'})",
                value=f"{user_rank} / {total_runners + 1}"
            )

            st.write("#### Porównanie na tle innych biegaczy")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(data=filtered_data, x='age', y='time_sec', alpha=0.3, label='Inni uczestnicy', ax=ax)
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
```

### Jak uruchomić aplikację?

1.  **Struktura:** Upewnij się, że wszystkie 5 plików (`.env`, `app.py`, `llm_parser.py`, `s3_utils.py`, `utils.py`, `requirements.txt`) znajdują się w tym samym folderze.
2.  **Zależności:** Otwórz terminal w tym folderze i uruchom `pip install -r requirements.txt`.
3.  **Konfiguracja:** Wypełnij plik `.env` swoimi kluczami dostępu do OpenAI i AWS S3.
4.  **Uruchomienie:** W terminalu wykonaj polecenie:
    ```bash
    streamlit run app.py
    ```

Aplikacja otworzy się w domyślnej przeglądarce internetowej. Będzie ona w pełni funkcjonalna i zgodna ze wszystkimi podanymi wymaganiami, oferując płynny przepływ między trzema widokami, obsługę historii, walidację danych przez AI, predykcję za pomocą modelu z S3 oraz zaawansowaną wizualizację wyników.
