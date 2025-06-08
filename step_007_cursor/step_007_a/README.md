###### Anthropic Console

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

Jakie poleciłbyś narzędzie dostępne w web online lub do pobrania i zainstalowania z GitHub do zbudowania niedużej aplikacji np. w streamlit w oparciu WYŁĄCZNIE o kod generowany przez Anthropic Claude Sonet 4, nie chodzi tu o narzędzia wspierające prace mozolnie klepiących kod programistów, chodzi o generowanie aplikacji wyłącznie na podstawie promptów dla Anthropic Claude Sonet 4, nie interesuje mnie też wsparcie do uruchamiania/debuggowania i testowania tego kodu, chodzi jedynie o wsparcie procesu kreowania aplikacji

### Odpowiedź:

Do tworzenia aplikacji wyłącznie na podstawie promptów dla Claude Sonnet, polecam następujące narzędzia:

#### Web-based (najprostsze)

##### 1. Cursor IDE (web version)
- Dostępne online przez przeglądarkę
- Bezpośrednia integracja z Claude API
- Możliwość generowania całych projektów jednym promptem
- Automatyczne tworzenie struktury folderów i plików

##### 2. Replit + Claude Integration
- Platform online do kodowania
- Można skonfigurować z Claude API
- Natychmiastowe uruchamianie Streamlit
- Wszystko w przeglądarce

#### Do pobrania z GitHub

##### 1. AI Code Generator Tools
```
https://github.com/paul-gauthier/aider
```
- Narzędzie CLI do generowania kodu przez AI
- Obsługuje Claude API
- Generuje kompletne aplikacje z pojedynczego prompta

##### 2. GPT-Engineer (obsługuje Claude)
```
https://github.com/AntonOsika/gpt-engineer
```
- Specjalnie do tworzenia aplikacji z opisów
- Można skonfigurować z Claude
- Generuje gotowe projekty Streamlit

#### Moja rekomendacja:
- **Cursor IDE** - najprostsze w użyciu, bezpośrednia integracja, bez konieczności instalacji. Wystarczy wpisać prompt opisujący aplikację, a Claude wygeneruje - - kompletny kod Streamlit.

Którego typu rozwiązanie preferujesz - webowe czy do instalacji?
