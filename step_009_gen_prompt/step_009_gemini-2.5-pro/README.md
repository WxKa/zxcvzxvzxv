###### Google AI Studio

### Gemini 2.5 Pro

#### prompt:

- stwórz prompt, który wygeneruje aplikację analogiczną do poniższej,
- nie jest wymagana zgodność styli, komentarzy i przycisków,
- ważna jest logika aplikacji,
- zachowaj nazwy zasobów zewnętrznych
#### odpowiedź:

Oto prompt, który precyzyjnie opisuje logikę działania aplikacji, zachowując nazwy zasobów zewnętrznych, zgodnie z Twoją prośbą.

### Prompt

**Cel:** Stwórz aplikację internetową w Pythonie z wykorzystaniem biblioteki **Streamlit**. Aplikacja ma prognozować czas ukończenia półmaratonu na podstawie danych wprowadzonych przez użytkownika w języku naturalnym. Aplikacja powinna być wieloetapowa, z nawigacją zarządzaną przez `st.session_state`.

**Zależności:** `streamlit`, `pandas`, `openai`, `boto3`, `pycaret`, `matplotlib`, `seaborn`.

---

### **Logika Aplikacji**

**1. Zarządzanie Stanem i Główna Struktura:**

*   Użyj `st.session_state` do kontrolowania przepływu aplikacji. Zdefiniuj w nim klucze:
    *   `page`: Przechowuje nazwę bieżącej strony (np. `"input"`, `"data"`, `"results"`).
    *   `runner_info`: Przechowuje sparsowane dane biegacza (wiek, płeć, czas na 5km w sekundach).
    *   `prediction_seconds`: Przechowuje wynik predykcji modelu.
    *   `history`: Lista przechowująca poprzednie wpisy tekstowe użytkownika.
    *   `hist_idx`: Indeks wskazujący na aktualny wpis w `history`.
*   Główna funkcja aplikacji powinna działać jak router, wyświetlając odpowiednią funkcję (`display_input_page`, `display_data_page`, `display_results_page`) w zależności od wartości `st.session_state.page`.

**2. Pobieranie Zasobów Zewnętrznych:**

*   **Model ML:** Stwórz funkcję `get_model()` opakowaną w dekorator `@st.cache_data`. Funkcja ma ładować model regresyjny z AWS S3 za pomocą `pycaret.regression.load_model`.
    *   Nazwa modelu: `"time_sec_model"`
    *   Platforma: `"aws"`
    *   Uwierzytelnienie: `{"bucket": "wk1", "path": "zadanie_9/models"}`
*   **Dane Historyczne:** Stwórz funkcję `get_full_csv_df(year)` opakowaną w `@st.cache_data`. Funkcja ma pobierać plik CSV z AWS S3 za pomocą klienta `boto3`.
    *   Nazwa bucketu S3: `"wk1"`
    *   Ścieżka do pliku S3: `"zadanie_9/current/halfmarathon_wroclaw_{year}__final_cleaned_full.csv"`
    *   Plik ma być wczytany do `pandas.DataFrame`.

---

### **Krok 1: Strona Wejściowa (`display_input_page`)**

1.  **Interfejs:**
    *   Wyświetl pole `st.text_area`, w którym użytkownik opisuje siebie. Wartość początkowa pola powinna pochodzić z `st.session_state.history[st.session_state.hist_idx]`.
    *   Dodaj przyciski do nawigacji po historii: "poprzedni", "następny", "wyczyść", "usuń". Przyciski te powinny modyfikować listę `history` i indeks `hist_idx` w `st.session_state`.
    *   Dodaj główny przycisk "Dalej" do rozpoczęcia analizy.

2.  **Logika Analizy:**
    *   Po kliknięciu "Dalej", wywołaj funkcję `parse_user_input(text)`.
    *   **Funkcja `parse_user_input`:**
        *   Użyj klienta **OpenAI API** (np. model `gpt-4o-mini`), aby wysłać tekst użytkownika.
        *   W prompcie systemowym poinstruuj model, aby wyodrębnił: `age` (int), `sex` (jako 'M' lub 'F'), `time_5k` (w formacie "MM:SS") oraz `pace_5k` (w formacie "MM:SS"). Odpowiedź modelu musi być w formacie **JSON**.
        *   Przetwórz odpowiedź JSON.
        *   Jeśli podano `pace_5k`, a nie ma `time_5k`, oblicz `time_5k` (czas tempa * 5).
        *   Przekonwertuj czas z formatu "MM:SS" na łączną liczbę sekund, używając wyrażeń regularnych.
        *   Zwaliduj dane: wiek (np. 18-105) i czas na 5 km (w realistycznym zakresie). W razie błędu rzuć wyjątek.
        *   Zwróć obiekt lub słownik z ustrukturyzowanymi danymi biegacza.
    *   Jeśli parsowanie się powiedzie, zapisz wynik w `st.session_state.runner_info`, zmień `st.session_state.page` na `"data"` i odśwież aplikację. W razie błędu, wyświetl go.

---

### **Krok 2: Strona Przeglądu Danych (`display_data_page`)**

1.  **Interfejs:**
    *   Wyświetl dane zapisane w `st.session_state.runner_info` (wiek, płeć, czas 5km) w celu weryfikacji przez użytkownika.
    *   Dodaj przycisk "Oszacuj czas w półmaratonie".

2.  **Logika Predykcji:**
    *   Po kliknięciu przycisku:
        *   Wywołaj `get_model()` w celu załadowania modelu.
        *   Przygotuj dane wejściowe dla modelu w postaci `pandas.DataFrame` z jedną linijką, używając danych z `runner_info`. Nazwy kolumn muszą pasować do tych, których oczekuje model (`gender`, `age`, `5_km_sec`).
        *   Użyj `pycaret.regression.predict_model`, aby uzyskać predykcję.
        *   Zapisz wynik (przewidywany czas w sekundach) w `st.session_state.prediction_seconds`.
        *   Zmień `st.session_state.page` na `"results"` i odśwież aplikację.

---

### **Krok 3: Strona Wyników (`display_results_page`)**

1.  **Interfejs:**
    *   Wyświetl prognozowany czas półmaratonu, formatując go z sekund na `HH:MM:SS` (np. za pomocą `datetime.timedelta`).
    *   Użyj `st.tabs`, aby zorganizować wyniki w sekcje, np. "Czas", "Miejsce w 2023", "Miejsce w 2024".

2.  **Logika Wizualizacji i Rankingu (funkcja `place(year)`):**
    *   Stwórz funkcję, która przyjmuje rok jako argument.
    *   Wewnątrz funkcji wywołaj `get_full_csv_df(year)`, aby pobrać dane historyczne.
    *   **Wykres:**
        *   Użyj `matplotlib/seaborn`, aby stworzyć wykres punktowy (`scatterplot`), gdzie oś X to czas ukończenia (`finish_sec`), a oś Y to wiek (`age`).
        *   Narysuj dane historyczne jako tło (np. szare, przezroczyste punkty).
        *   Dodaj na wykresie jeden, wyróżniający się punkt reprezentujący wiek użytkownika i jego prognozowany czas z `st.session_state`.
        *   Dodaj `st.radio` pozwalające filtrować dane tła na wykresie (wszyscy biegacze vs. biegacze tej samej płci co użytkownik).
    *   **Ranking:**
        *   Dodaj dane użytkownika (w tym jego prognozowany `finish_sec`) jako nowy wiersz do `DataFrame` z danymi historycznymi.
        *   Posortuj `DataFrame` po `finish_sec`.
        *   Użyj `pandas.DataFrame.interpolate()` na kolumnie z miejscami, aby oszacować miejsce w rankingu dla użytkownika.
        *   Wyświetl oszacowane miejsce.
    *   Wywołaj tę funkcję w odpowiednich zakładkach dla różnych lat.
3.  **Nawigacja:**
    *   Dodaj przycisk "Wróć do strony głównej", który resetuje stan (`runner_info`, `prediction_seconds`) i ustawia `st.session_state.page` na `"input"`.