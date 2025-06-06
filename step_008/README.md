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






Postanowiłem zacząć od Cursor

staciłem już 2h żeby znaleźć Composer w cursor 1.0.0. pod linuxem,
podobno ma się otwierać na Ctrl-I, ale w tym panelu pokazuje się tylko Chat
czytam dalej w web, że 

Cursor Composer is not a free feature in Cursor.
While Cursor offers a free plan, Composer is a Pro subscription feature. 

wchodzę na upgrade do Pro i widzę $20/month

więc cursor na razie odpuszczam.