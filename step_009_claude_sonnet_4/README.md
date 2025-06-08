###### Anthropic Console
### Anthropic Claude Sonnet 4
#### prompt:

- utwórz prompt, który wygeneruje aplikację zbliżoną do poniższej,
- nie jest istotna zgodność styli, treści komentarzy i przycisków,
- ważna jest logika aplikacji

#### odzew:

Utwórz aplikację Streamlit do przewidywania czasu w półmaratonie z następującą logiką:

**Główna funkcjonalność:**
1. Aplikacja ma 3 główne strony: "input", "data", "results" przechowywane w session_state["page"]
2. Użytkownik wprowadza dane tekstowe opisujące siebie (wiek, płeć, czas na 5km)
3. AI parsuje tekst i wyciąga strukturalne dane
4. Model ML przewiduje czas półmaratonu na podstawie danych
5. Wyniki są wyświetlane z wizualizacjami

**Struktura danych:**
- Klasa RunnerInfo z polami: age (int), sex (str), time_5k (float w sekundach), pace_5k (str)
- Metody: to_dict(), sex_str(), time_5k_str(), pace_5k_str()
- Funkcja parse_time() konwertująca MM:SS na sekundy

**Session State:**
- history: lista poprzednich wpisów użytkownika z nawigacją (poprzedni/następny/usuń/wyczyść)
- hist_idx: aktualny indeks w historii
- runner_info: sparsowane dane biegacza
- page: aktualna strona ("input"/"data"/"results")
- prediction_seconds: przewidywany czas w sekundach

**Strona INPUT:**
- Taby: "Prognoza" i pomocnicza tabela "Tempo/Prędkość"
- Text area do opisu siebie
- 4 przyciski nawigacji po historii: poprzedni, wyczyść, usuń, następny
- Przycisk "Dalej" wywołujący parsowanie AI
- Tabela konwersji tempo/prędkość w drugim tabie

**Strona DATA:**
- Wyświetla sparsowane dane w tabeli
- Przycisk "Oszacuj czas" uruchamiający model ML
- Przycisk powrotu

**Strona RESULTS:**
- Wyświetla dane biegacza w 3 kolumnach
- Taby: "Czas", "Miejsce w 2023", "Miejsce w 2024"
- Tab "Czas": główny wynik predykcji
- Taby "Miejsce": scatter plot wieku vs czasu z danymi historycznymi, obliczanie pozycji
- Przycisk powrotu

**Funkcje AI i ML:**
- parse_user_input(): używa OpenAI do ekstrakcji danych z tekstu naturalnego
- Zwraca JSON z polami: age, sex, time_5k, pace_5k
- Walidacja danych (wiek 18-105, czas 15min-2h, płeć M/F)
- Model ML przewiduje czas na podstawie wieku, płci i czasu na 5km

**Funkcje pomocnicze:**
- save_input(): zarządza historią wpisów
- display_*_page(): funkcje dla każdej strony
- place(): generuje wykresy pozycji dla danego roku
- back_button(): nawigacja powrotna

**Wymagane biblioteki:**
streamlit, pandas, json, matplotlib, seaborn, openai, dataclasses, datetime, re

**Wizualizacje:**
- Scatter plot wieku vs czasu ukończenia z oznaczeniem pozycji użytkownika
- Obliczanie miejsca w klasyfikacji na podstawie historycznych danych
- Formatowanie czasu jako timedelta

Stwórz pełną aplikację zachowującą tę logikę przepływu danych i nawigacji między stronami.
