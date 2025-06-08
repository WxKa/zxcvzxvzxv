###### Anthropic Console
#### Pytanie:

zbuduj prompt najbardziej zrozumiały dla AI, (ale z zachowaniem dystansu do implementacji w streamlit) zamiast tekstu:

wygeneruj aplikację do uruchomienia w streamlit,
aplikacja składa się z trzech kolejnych ekranów,
1. na pierwszym ekranie jest pole tekstowe z pytaniem o podanie tekstu i button potwierdzający przejście do kolejnej strony,
2. na drugim ekranie ekranie użytkownik potwierdza to co napisał na pierwszym ekranie i dwa buttony: przejście do kolejnej strony i powrót do strony poprzedniej,
3. na trzecim ekranie jest to co zostało potwierdzone na ekranie drugim i jeden button, powrót do pierwszej strony. 

#### Odpowiedź:

Oto zoptymalizowany prompt dla AI:

**Stwórz aplikację webową z nawigacją wieloekranową składającą się z trzech następujących widoków:**<br>
**EKRAN 1 - Wprowadzanie danych:**

* Pole tekstowe do wprowadzenia dowolnego tekstu przez użytkownika
* Przycisk "Dalej" umożliwiający przejście do następnego ekranu

**EKRAN 2 - Potwierdzenie danych:**

* Wyświetlenie tekstu wprowadzonego na ekranie 1 w trybie tylko do odczytu
* Przycisk "Potwierdź i przejdź dalej"
* Przycisk "Wróć i edytuj"

**EKRAN 3 - Finalizacja:**

* Wyświetlenie potwierdzonego tekstu z ekranu 2
* Przycisk "Rozpocznij od nowa" (powrót do ekranu 1)

**Wymagania funkcjonalne:**

* Zachowanie danych wprowadzonych przez użytkownika podczas nawigacji między ekranami
* Możliwość powrotu i edycji na każdym etapie
* Intuicyjny przepływ użytkownika z jasnym oznaczeniem aktualnego kroku

**Wymagania techniczne:**

* Implementacja w frameworku Streamlit
* Użycie session state do zarządzania stanem aplikacji
* Czytelny i responsywny interfejs użytkownika

<br/>
<br/>
Ten prompt jest bardziej precyzyjny, używa terminologii zrozumiałej dla AI i jasno definiuje zarówno funkcjonalności, jak i wymagania techniczne.