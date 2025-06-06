
przeprosiłem się z cursorem,

Cursor zintegrował funkcje "Composer" z głównym interfejsem czatu AI.

Oznacza to, że to, co wcześniej było dostępne w "Composerze" (np. generowanie i edytowanie wielu plików, tryby "Agent" i "Edit"), jest teraz dostępne bezpośrednio w oknie czatu AI.

ale moja radość trwała krótko,

w oknie chat, po próbie wysłania prompt do claude-4-sonnet dostałem w trąbę:

Anthropic's latest models are currently only available to paid users.

Please upgrade to a paid plan to use these models.

czyli znowu klikamy w aplikacji cursor w górnym prawym rogu w ikonkę ❌.

ale, może nie,

a z claude-3.7-sonnet ....

działa !!!

### Pytanie:

Jakie poleciłbyś narzędzie dostępne w web online lub do pobrania i zainstalowania **np.** z GitHub do zbudowania niedużej aplikacji np. w streamlit w oparciu WYŁĄCZNIE o kod generowany przez Anthropic Claude Sonet 4, nie chodzi tu o narzędzia wspierające prace mozolnie klepiących kod programistów, chodzi o generowanie aplikacji wyłącznie na podstawie promptów dla Anthropic Claude Sonet 4, nie interesuje mnie też wsparcie do uruchamiania/debuggowania i testowania tego kodu, chodzi jedynie o wsparcie procesu
kreowania aplikacji

### Odpowiedź:

Oto najlepsze narzędzia do kreowania aplikacji Streamlit wyłącznie poprzez prompty do Claude Sonnet:

#### Narzędzia webowe (gotowe do użycia):
##### 1. Cursor (cursor.sh)
- Edytor z wbudowaną integracją z Claude
- Tryb "Composer" - generuje całą aplikację na podstawie promptu
- Bezpośrednie wsparcie dla Streamlit
- Możliwość iteracyjnego rozwijania aplikacji poprzez kolejne prompty
##### 2. Replit Agent
- Platforma webowa z AI agent
- Generuje kompletne aplikacje Streamlit z promptu
- Automatycznie tworzy strukturę plików
- Bezpośrednie wdrażanie online
##### 3. v0.dev (Vercel)
- Choć skupia się na React, ma eksperymentalne wsparcie dla Pythona
- Generuje kod na podstawie opisów w języku naturalnym

#### Narzędzia do pobrania:
##### 1. Aider (GitHub)
```bash
pip install aider-chat
```
- CLI tool do generowania kodu z Claude
- Świetne wsparcie dla projektów Streamlit
- Automatyczne tworzenie struktury aplikacji
##### 2. Continue.dev
- Plugin do VS Code
- Integracja z Claude Sonnet
- Tryb generowania całych aplikacji

#### Moja rekomendacja:
**Cursor** - najbardziej intuicyjny dla Twojego przypadku użycia. Wystarczy opisać aplikację w Composer i otrzymasz gotowy kod Streamlit.

Które rozwiązanie brzmi najciekawiej?
