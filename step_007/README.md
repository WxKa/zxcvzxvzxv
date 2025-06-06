errata:
  pytanie to zostało zadane niewłaściwemu AI, tj, Anthropic Claude Sonet 4, który ma odcięcie (tak to się mówi) w kwietniu 2024 r. czyli ma lekko nieaktualną wiedzę
  i nie jest najlepszy w tego typu pytaniach, więc pytanie o narzędzia trzeba zadać AI, która ma najpóźniejsze odcięcie i dodatkowo korzysta z aktualnej wiedzy z internentu i jest aktualnie najlepsza, czyli mowa tu raczej o ChatGPT i Gemini.

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



Postanowiłem zacząć od Cursor

staciłem już 2h żeby znaleźć Composer w cursor 1.0.0. pod linuxem,
podobno ma się otwierać na Ctrl-I, ale w tym panelu pokazuje się tylko Chat
czytam dalej w web, że 

Cursor Composer is not a free feature in Cursor.
While Cursor offers a free plan, Composer is a Pro subscription feature. 

wchodzę na upgrade do Pro i widzę $20/month

więc cursor na razie odpuszczam.