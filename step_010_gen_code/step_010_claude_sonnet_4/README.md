
###### Anthropic Claude Sonnet 4

kod się wygenerował, ale szału nie ma,

##### pierwsze problemy jakie się pojawiły od razu to:

- pokazuje się pierwsza strona i na początku jest wrażenie, że coś działa,
- przy przejściu na drugą stronę, drobiazg: brak sprawdzenia, czy result['error'] nie jest przypadkiem None,
- inna konstrukcja system: user: prompta i brak explicite, że odpowiedzią jest json, czyli trzeba narzucić z góry jak ma być zbudowany klient do gpt,
- to nad czy teraz siedzę, to zastosowanie get_object przy pobieraniu csv z s3 i prawdopodobnie w resulcie nie jest to DataFrame,
