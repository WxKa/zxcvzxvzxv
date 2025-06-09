###### Google Gemini
### Gemini 2.5 Flash

### prompt:

stwórz prompt, który wygeneruje aplikację zbliżoną do poniższej,

nie jest wymagana zgodność styli, komentarzy i przycisków,

ważna jest logika aplikacji

### odpowiedź:

Twoje zapytanie dotyczy stworzenia promptu dla aplikacji opartej na Streamlit, która ma na celu **prognozowanie czasu ukończenia półmaratonu na podstawie danych biegacza**, takich jak wiek, płeć oraz czas lub tempo na 5 km. Aplikacja powinna również wizualizować przewidywane miejsce biegacza w odniesieniu do wyników z poprzednich lat.

Oto propozycja promptu, który możesz wykorzystać:

---

Stwórz aplikację Streamlit do **prognozowania czasu w półmaratonie**. Aplikacja powinna składać się z trzech głównych widoków (stron), pomiędzy którymi użytkownik może nawigować:

## Strona 1: Wprowadzanie danych biegacza

* Umożliw użytkownikowi wprowadzenie informacji o sobie za pomocą pola tekstowego. Przykładami danych są: wiek (liczba), płeć (np. "mężczyzna", "kobieta", "m", "k"), oraz czas na 5 km (np. "25:30") lub tempo na 5 km (np. "5'06''").
* Zaimplementuj mechanizm **historii wprowadzonych danych**, pozwalający na przeglądanie i wybieranie poprzednich wpisów. Użytkownik powinien mieć możliwość nawigacji między wpisami (poprzedni/następny), czyszczenia bieżącego wpisu oraz usuwania wpisów z historii.
* Dodaj drugą zakładkę zawierającą **tabelę konwersji tempa na prędkość** (minuty i sekundy na kilometr na km/h), aby pomóc użytkownikowi w podaniu poprawnego formatu danych.
* Przycisk "Dalej" powinien przetwarzać wprowadzone dane. Użyj modelu językowego (np. za pomocą `langfuse.openai.OpenAI` i `gpt-4o-mini`) do ekstrakcji i walidacji informacji (wieku, płci, czasu/tempa na 5 km) z tekstu.
    * Wiek: musi być liczbą całkowitą od 18 do 105 lat.
    * Płeć: musi być rozpoznana jako "M" (mężczyzna) lub "F" (kobieta).
    * Czas/Tempo na 5 km: Musi być poprawnie sparsowany na sekundy. Jeśli podano tempo, przelicz je na czas na 5 km. Wartość po konwersji musi mieścić się w realistycznym zakresie (np. od 15 minut do 120 minut).
* W przypadku błędów walidacji lub problemów z parsowaniem, wyświetl odpowiedni komunikat o błędzie.
* Po pomyślnym przetworzeniu danych, przejdź do widoku podsumowania danych.

## Strona 2: Podsumowanie danych biegacza i predykcja

* Wyświetl podsumowanie wprowadzonych danych biegacza: wiek, płeć (w formie słownej, np. "kobieta") oraz czas na 5 km (w formacie MM:SS).
* Dodaj przycisk "Oszacuj czas w półmaratonie", który po naciśnięciu załaduje wytrenowany model regresji (`pycaret.regression.load_model`) i użyje go do predykcji czasu ukończenia półmaratonu.
    * Model powinien być ładowany z zasobów S3 (wiadro `wk1`, ścieżka `zadanie_9/models/time_sec_model`).
    * Dane wejściowe dla modelu powinny być w formacie `{"gender": "M/F", "age": int, "5_km_sec": float}`.
* Po uzyskaniu predykcji, przejdź do widoku wyników.
* Umożliw powrót do strony wprowadzania danych.

## Strona 3: Wyniki predykcji i wizualizacja miejsca

* Wyświetl przewidywany czas ukończenia półmaratonu w czytelnym formacie (np. HH:MM:SS).
* Dodaj dwie zakładki do wizualizacji przewidywanego miejsca biegacza w odniesieniu do historycznych danych z Półmaratonu Wrocławskiego (np. dla lat 2023 i 2024).
    * Dla każdej zakładki (roku):
        * Załaduj historyczne dane biegaczy z pliku CSV z S3 (wiadro `wk1`, ścieżka `zadanie_9/current/halfmarathon_wroclaw_{rok}__final_cleaned_full.csv`).
        * Umożliw użytkownikowi wybór, czy chce wizualizować swoje miejsce w odniesieniu do wszystkich biegaczy, czy tylko do biegaczy tej samej płci.
        * Wygeneruj wykres rozrzutu (`matplotlib.pyplot` lub `seaborn`) pokazujący czasy ukończenia półmaratonu w zależności od wieku dla wszystkich uczestników (lub wybranej płci), a następnie nałóż na ten wykres punkt reprezentujący przewidywany wynik aktualnego biegacza (z wyraźnym oznaczeniem).
        * Poniżej wykresu wyświetl szacowane miejsce biegacza (interpolowane na podstawie danych historycznych).
* Umożliw powrót do strony głównej (wprowadzania danych).

## Wymagania ogólne:

* Użyj biblioteki `streamlit` do budowy interfejsu.
* Zadbaj o obsługę błędów (np. brak pliku CSV, problemy z S3, błędy modelu).
* Użyj `st.session_state` do zarządzania stanem aplikacji i nawigacji między stronami.
* Nie jest wymagana zgodność styli, komentarzy ani przycisków z podanym przykładem kodu, jednak **logika aplikacji i przepływ danych są kluczowe**.
* Do stylowania komponentów Streamlit możesz użyć własnych klas CSS (np. `utils_css.better_styling_css()`).
* Wymagane jest użycie `boto3` do interakcji z S3 oraz `pycaret` do ładowania modelu.
* Upewnij się, że klucze API OpenAI i dostęp do S3 są ładowane z zmiennych środowiskowych (`.env`).
* Zastosuj `@st.cache_data` do funkcji, które ładują dane lub model, aby zoptymalizować wydajność.

---

Ten prompt zawiera wszystkie kluczowe elementy i logikę, którą chcesz zaimplementować, jednocześnie pozostawiając swobodę w kwestii stylizacji i drobnych detali implementacyjnych.
