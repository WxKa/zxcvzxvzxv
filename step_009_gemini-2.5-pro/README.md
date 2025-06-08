
### Gemini 2.5 Pro

#### prompt:

stwórz prompt, który wygeneruje aplikację zbliżoną do poniższej,

nie jest wymagana zgodność styli, napisów, komentarzy i przycisków,

ważna jest logika aplikacji

#### odzew:

Oto prompt, który opisuje logikę i strukturę aplikacji, pomijając szczegóły stylistyczne. Jest on napisany w języku angielskim, ponieważ modele AI są na nim najlepiej wytrenowane, co daje największą szansę na uzyskanie poprawnego i kompletnego kodu.

Prompt został podzielony na sekcje, aby precyzyjnie opisać każdy element aplikacji, tak jak prosiłeś – skupiając się na logice.

### **Prompt dla modelu AI**

**Cel:** Stwórz skrypt w języku Python dla wielostronicowej aplikacji Streamlit, która przewiduje czas biegacza w półmaratonie na podstawie danych wprowadzonych przez użytkownika. Aplikacja powinna działać zgodnie z określoną logiką przepływu, od wprowadzania danych po wyświetlanie wyników predykcji wraz z wizualizacjami.

**Kluczowe technologie:**
*   `streamlit` do stworzenia interfejsu webowego.
*   `pandas` do manipulacji danymi.
*   biblioteka `openai` do przetwarzania danych wprowadzonych w języku naturalnym.
*   `pycaret` do ładowania wytrenowanego modelu regresji i tworzenia predykcji.
*   `boto3` do pobierania modelu i plików z danymi z bucketa AWS S3.
*   `matplotlib` lub `seaborn` do tworzenia wykresów.

**Logika i struktura aplikacji:**

Aplikacja powinna być zorganizowana jako aplikacja wielostronicowa, kontrolowana za pomocą `st.session_state`. Główne strony to `input` (wprowadzanie), `data` (dane) i `results` (wyniki).

**1. Konfiguracja ogólna i zarządzanie stanem:**
*   Użyj `st.session_state` do zarządzania stanem aplikacji, w tym:
    *   `st.session_state.page`: ciąg znaków do kontrolowania, która strona jest wyświetlana (`input`, `data`, `results`).
    *   `st.session_state.runner_info`: obiekt lub słownik do przechowywania przetworzonych danych użytkownika (wiek, płeć, czas na 5 km).
    *   `st.session_state.prediction_seconds`: do przechowywania ostatecznego przewidywanego czasu w sekundach.
    *   `st.session_state.history`: lista ciągów znaków do przechowywania historii wprowadzanych danych.
*   Wczytaj zmienne środowiskowe (np. `OPENAI_API_KEY`) używając `dotenv`.
*   Zainicjuj klienta OpenAI.
*   Zainicjuj klienta S3 `boto3`.

**2. Ładowanie danych i modelu:**
*   Stwórz funkcję do pobierania wytrenowanego modelu regresji `pycaret` z określonej ścieżki w buckecie S3 (np. bucket `my-bucket`, ścieżka `models/my_model`). Użyj `pycaret.regression.load_model`. Ta funkcja powinna być cachowana za pomocą `@st.cache_data`.
*   Stwórz funkcję do pobierania historycznych danych z zawodów (plik CSV) dla danego roku z S3. Nazwa pliku powinna być dynamiczna w zależności od roku (np. `race_data_{year}.csv`). Ta funkcja również powinna być cachowana za pomocą `@st.cache_data`.

**3. Strona 1: Strona wprowadzania danych (`page == 'input'`)**
*   Wyświetl tytuł, np. "Prognoza czasu w półmaratonie".
*   Udostępnij komponent `st.text_area`, w którym użytkownik będzie mógł opisać siebie w języku naturalnym.
    *   Przykłady danych wejściowych: "Jestem 35-letnim mężczyzną, a mój czas na 5 km to 22:30.", "Jestem kobietą, mam 28 lat, a moje tempo na 5 km to 4:45."
*   Zaimplementuj funkcjonalność historii wprowadzanych danych:
    *   Użyj `st.session_state.history` do przechowywania listy wpisów.
    *   Dodaj przyciski "Poprzedni" i "Następny" do nawigacji po historii.
    *   Dodaj przyciski "Wyczyść" i "Usuń" do zarządzania wpisami w historii.
*   Gdy użytkownik kliknie przycisk "Dalej":
    *   Wywołaj funkcję, która przetworzy tekst w języku naturalnym z pola tekstowego.
    *   Jeśli przetwarzanie się powiedzie, zapisz wynik w `st.session_state.runner_info` i zmień `st.session_state.page` na `data`.
    *   Jeśli przetwarzanie się nie powiedzie, wyświetl komunikat o błędzie za pomocą `st.error()`.

**4. Funkcja przetwarzania języka naturalnego (`parse_user_input`)**
*   Funkcja ta powinna przyjmować jako wejście ciąg znaków.
*   Powinna wykorzystywać API Chat Completions od OpenAI (np. `gpt-4o-mini` lub `gpt-3.5-turbo`) z włączonym trybem JSON.
*   Prompt systemowy powinien instruować model, aby wyodrębnił następujące pola do obiektu JSON:
    *   `age` (liczba całkowita)
    *   `sex` (ciąg znaków, powinien być znormalizowany do 'M' dla mężczyzny i 'F' dla kobiety)
    *   `time_5k` (ciąg znaków w formacie "MM:SS", jeśli podano czas)
    *   `pace_5k` (ciąg znaków w formacie "MM:SS", jeśli podano tempo)
*   **Przetwarzanie końcowe i walidacja:**
    *   Jeśli `time_5k` nie jest podany, ale `pace_5k` jest, oblicz czas na 5 km w sekundach (tempo w sekundach * 5).
    *   Jeśli podano `time_5k`, przekształć ciąg "MM:SS" na łączną liczbę sekund.
    *   Przeprowadź walidację:
        *   Wiek musi mieścić się w rozsądnym zakresie (np. od 18 do 100 lat).
        *   Płeć musi być 'M' lub 'F'.
        *   Czas na 5 km musi być realistyczny.
    *   Jeśli walidacja się nie powiedzie, zgłoś błąd `ValueError`.
    *   Zwróć obiekt strukturalny (np. `dataclass` lub słownik) zawierający zweryfikowany `wiek`, `płeć` i `czas_na_5km` w sekundach.

**5. Strona 2: Strona potwierdzenia danych (`page == 'data'`)**
*   Wyświetl przetworzone dane z `st.session_state.runner_info`, aby użytkownik mógł je potwierdzić (Wiek, Płeć, Czas na 5 km).
*   Dodaj przycisk "Oszacuj mój czas".
*   Gdy przycisk zostanie kliknięty:
    *   Wyświetl komponent `st.spinner`.
    *   Załaduj model `pycaret` z S3 (używając funkcji z cache).
    *   Stwórz obiekt `pandas.DataFrame` z danych użytkownika (`st.session_state.runner_info`), upewniając się, że nazwy kolumn odpowiadają tym, których oczekuje model (np. 'age', 'gender', '5_km_sec').
    *   Użyj `pycaret.regression.predict_model`, aby uzyskać predykcję.
    *   Zapisz przewidywany czas (w sekundach) w `st.session_state.prediction_seconds`.
    *   Zmień `st.session_state.page` na `results`.
*   Dodaj przycisk "Wróć", aby powrócić na stronę `input`.

**6. Strona 3: Strona wyników (`page == 'results'`)**
*   Wyświetl tytuł, np. "Wyniki predykcji".
*   Ponownie wyświetl dane wejściowe użytkownika (Wiek, Płeć, Czas na 5 km).
*   Wyświetl ostateczny przewidywany czas półmaratonu. Sformatuj sekundy z `st.session_state.prediction_seconds` do czytelnego formatu GG:MM:SS.
*   **Sekcja analizy porównawczej (używając `st.tabs`):**
    *   Stwórz zakładki dla różnych lat zawodów (np. "Bieg 2023", "Bieg 2024").
    *   Wewnątrz każdej zakładki zaimplementuj następującą logikę wizualizacji:
        1.  Załaduj historyczne dane z pliku CSV dla danego roku z S3.
        2.  Stwórz wykres punktowy (`matplotlib`/`seaborn`) z:
            *   oś x: Czas ukończenia (`finish_sec`)
            *   oś y: Wiek (`age`)
        3.  Narysuj wszystkich biegaczy z danych historycznych jako punkty o jasnym kolorze i częściowej przezroczystości.
        4.  Narysuj przewidywany czas i wiek obecnego użytkownika jako wyraźny punkt w jaskrawym kolorze (np. czerwonym).
        5.  Dodaj legendę, aby odróżnić użytkownika od innych biegaczy.
        6.  Dodaj przycisk `st.radio`, aby umożliwić użytkownikowi filtrowanie punktów danych w tle na wykresie według płci ("Wszyscy" lub płeć użytkownika).
        7.  (Opcjonalnie, ale warto) Oszacuj pozycję (miejsce) użytkownika w rankingu. Aby to zrobić, dodaj wynik predykcji użytkownika do historycznej ramki danych, posortuj według czasu ukończenia i znajdź jego pozycję. Wyświetl tę pozycję.
*   Dodaj przycisk "Zacznij od nowa", który resetuje stan sesji i wraca do strony `input`.