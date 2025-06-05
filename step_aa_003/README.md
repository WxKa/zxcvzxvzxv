#### Pytanie:

zbuduj prompt najbardziej zrozumiały dla AI zamiast tekstu:

wygeneruj aplikację do uruchomienia w streamlit,
aplikacja składa się z trzech kolejnych ekranów,
1. na pierwszym ekranie jest pole tekstowe z pytaniem o podanie tekstu i button potwierdzający przejście do kolejnej strony,
2. na drugim ekranie ekranie użytkownik potwierdza to co napisał na pierwszym ekranie i dwa buttony: przejście do kolejnej strony i powrót do strony poprzedniej,
3. na trzecim ekranie jest to co zostało potwierdzone na ekranie drugim i jeden button, powrót do pierwszej strony. 

#### Odpowiedź:

Oto szczegółowy prompt dla AI:

**ZADANIE**: Stwórz kompletną aplikację Streamlit z trójstronową nawigacją

**SPECYFIKACJA TECHNICZNA:**

* Język: Python
* Framework: Streamlit
* Nawigacja: Używaj st.session_state do zarządzania stanem między stronami

**STRUKTURA APLIKACJI:**
**STRONA 1 - Wprowadzanie danych**

* Tytuł strony: wyraźnie oznacz jako pierwszą stronę
* Element: st.text_input() lub st.text_area() z etykietą "Wprowadź tekst:"
* Element: st.button() z tekstem "Dalej" lub "Przejdź do potwierdzenia"
* Logika: Po kliknięciu zapisz tekst w st.session_state i przejdź do strony 2

**STRONA 2 - Potwierdzenie**

* Tytuł strony: wyraźnie oznacz jako stronę potwierdzenia
* Wyświetl: Tekst wprowadzony na stronie 1 (z st.session_state)
* Element: st.button() "Potwierdź i dalej" → przejście do strony 3
* Element: st.button() "Wróć do edycji" → powrót do strony 1
* Logika: Obsłuż oba przyciski z odpowiednią nawigacją

**STRONA 3 - Finał**

* Tytuł strony: wyraźnie oznacz jako stronę końcową
* Wyświetl: Potwierdzony tekst z poprzedniej strony
* Element: st.button() "Rozpocznij od nowa" → powrót do strony 1
* Opcjonalnie: Dodaj komunikat o pomyślnym zakończeniu procesu

**WYMAGANIA TECHNICZNE:**

* Użyj zmiennej w st.session_state do śledzenia aktualnej strony (np. current_page)
* Użyj zmiennej w st.session_state do przechowywania tekstu użytkownika
* Zastosuj strukturę if/elif/else do renderowania odpowiedniej strony
* Dodaj podstawowe stylowanie dla lepszej czytelności
* Upewnij się, że aplikacja nie resetuje się po każdym kliknięciu

**FORMAT ODPOWIEDZI:**
Dostarcz kompletny, gotowy do uruchomienia kod Python z wszystkimi niezbędnymi importami i komentarzami wyjaśniającymi kluczowe fragmenty.