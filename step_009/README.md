
### prompt:

- opracuj prompt, który wygeneruje aplikację zbliżoną funkcjonalnością do app.py,
- nie jest wymagana zgodność styli ani treści komentarzy i przycisków,
- kluczowa jest logika

### odzew:

Stwórz aplikację Streamlit do prognozowania czasu w półmaratonie na podstawie danych użytkownika. Aplikacja powinna:

1. Przyjmować dane od użytkownika w formie tekstowej, gdzie użytkownik opisuje swój wiek, płeć i czas/tempo na 5 km.

2. Wykorzystywać model GPT do ekstrakcji kluczowych informacji z tekstu:
   - wieku (liczba całkowita)
   - płci (M/F)
   - czasu na 5 km (w formacie MM:SS) lub tempa na kilometr

3. Konwertować czas/tempo na sekundy i przeprowadzać walidację danych:
   - sprawdzać czy wiek jest w rozsądnym zakresie (18-105)
   - sprawdzać czy czas na 5 km jest realistyczny
   - sprawdzać czy podano wszystkie wymagane informacje

4. Mieć interfejs z kilkoma stronami/stanami:
   - strona wprowadzania danych z historią poprzednich zapytań
   - strona potwierdzenia danych
   - strona wyników z prognozą

5. Używać modelu ML do przewidywania czasu w półmaratonie na podstawie wieku, płci i czasu na 5 km.

6. Wizualizować wyniki:
   - pokazywać przewidywany czas
   - pokazywać miejsce użytkownika w porównaniu do innych biegaczy (z lat 2023 i 2024)
   - generować wykresy porównujące wynik użytkownika z innymi biegaczami

7. Umożliwiać filtrowanie porównań według płci.

8. Zawierać tabelę konwersji tempa na prędkość dla referencji.

9. Wykorzystywać AWS S3 do przechowywania modelu ML i danych historycznych.

10. Zawierać system nawigacji między stronami i zarządzania historią zapytań.

Aplikacja powinna być zorganizowana w sposób modułowy, z funkcjami do obsługi poszczególnych zadań, i wykorzystywać stan sesji Streamlit do przechowywania danych między interakcjami.

----------

Dziękuję, pozamiatane, prompt już jest,

ale, ale,

a gdzie program ?
