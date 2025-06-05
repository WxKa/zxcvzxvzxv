### Pytanie:

podaj przykład użycia pseudo kodu, pomiędzy językiem naturalnym w przykładowym prompt do generowania kodu

### Odpowiedź:

Oto przykład promptu łączącego język naturalny z pseudokodem:

#### Przykład promptu:

Stwórz funkcję w Pythonie do sortowania listy użytkowników według wieku.

##### Pseudokod logiki:
```
FUNKCJA sortuj_uzytkownikow(lista_uzytkownikow):
    DLA KAŻDEGO użytkownika W lista_uzytkownikow:
        JEŚLI użytkownik nie ma pola 'wiek':
            USTAW domyślny wiek = 0

POSORTUJ listę WEDŁUG pola 'wiek' ROSNĄCO
ZWRÓĆ posortowaną listę
```
##### Wymagania dodatkowe:
- Obsłuż przypadek gdy użytkownik nie ma ustawionego wieku
- Dodaj walidację czy przekazany parametr to lista
- Funkcja powinna działać z listą słowników gdzie każdy użytkownik to {'nazwa': str, 'wiek': int}


### Wygenerowany kod Python:
```python
def sortuj_uzytkownikow(lista_uzytkownikow):
    # Walidacja czy parametr to lista
    if not isinstance(lista_uzytkownikow, list):
        raise ValueError("Parametr musi być listą")
    
    # Obsługa brakującego pola 'wiek'
    for uzytkownik in lista_uzytkownikow:
        if 'wiek' not in uzytkownik:
            uzytkownik['wiek'] = 0
    
    # Sortowanie według wieku
    posortowana_lista = sorted(lista_uzytkownikow, key=lambda x: x['wiek'])
    
    return posortowana_lista

# Przykład użycia:
uzytkownicy = [
    {'nazwa': 'Anna', 'wiek': 25},
    {'nazwa': 'Jan', 'wiek': 30},
    {'nazwa': 'Piotr'}  # brak wieku
]

wynik = sortuj_uzytkownikow(uzytkownicy)
print(wynik)
```
##### Korzyści takiego podejścia:

- **Jasność intencji** - pseudokod pokazuje dokładnie jaką logikę chcemy zaimplementować
- **Łatwość zrozumienia** - AI lepiej interpretuje strukturę algorytmu
- **Kontrola nad logiką** - możemy określić kluczowe kroki przed implementacją
- **Uniwersalność** - ten sam pseudokod można użyć dla różnych języków programowania