### Pytanie:

jeśli w generownym kodzie programu będzie potrzeba umieszczenia kodu algorytmu np. sortującego, to skąd on się bierze, czy jest dostępny w postaci wzorca, czy generowany jest na bieżąco

### Odpowiedź:

Kod algorytmów w programach generowanych może pochodzić z kilku źródeł, w zależności od podejścia:

#### 1. Biblioteki i wzorce gotowe
```python
# Najczęściej używane - gotowe implementacje
sorted_list = sorted(data)  # Python
std::sort(vec.begin(), vec.end());  // C++
Arrays.sort(array);  // Java
```

#### 2. Szablony i wzorce projektowe
```python
# Generator może mieć przygotowane szablony
SORT_TEMPLATES = {
    'quicksort': """
        def quicksort(arr):
            if len(arr) <= 1:
                return arr
            pivot = arr[len(arr) // 2]
            left = [x for x in arr if x < pivot]
            middle = [x for x in arr if x == pivot]
            right = [x for x in arr if x > pivot]
            return quicksort(left) + middle + quicksort(right)
    """,
    'bubble_sort': "..."
}
```

#### 3. Generowanie na podstawie specyfikacji

Nowoczesne AI (jak GPT) mogą generować algorytmy na żądanie:
```
Prompt: "Wygeneruj funkcję sortowania bąbelkowego w Pythonie"
→ AI generuje kompletny kod
```

#### 4. Komponenty modularne
```python
class CodeGenerator:
    def generate_sort(self, algorithm_type, data_type):
        if algorithm_type == "quick":
            return self._generate_quicksort(data_type)
        elif algorithm_type == "merge":
            return self._generate_mergesort(data_type)
```

#### 5. Repozytoria wzorców

- Bazy danych algorytmów
- Snippet libraries
- Code repositories (GitHub, GitLab)
- Algorithm catalogs

#### W praktyce najczęściej:

1.**Używa się gotowych bibliotek** (99% przypadków)
2. **Szablony** dla standardowych algorytmów
3. ***Generowanie AI** dla specjalnych przypadków
4. **Kompozycja** z mniejszych elementów

Nowoczesne generatory kodu rzadko "wymyślają" algorytmy od zera - raczej adaptują sprawdzone rozwiązania do konkretnego kontekstu.