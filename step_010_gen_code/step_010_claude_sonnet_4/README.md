
###### Anthropic Claude Sonnet 4

źródło: gemini-2.5-flash

kod się wygenerował, ale szału nie ma,

##### pierwsze problemy jakie się pojawiły od razu to:

- pokazuje się pierwsza strona i na początku jest wrażenie, że coś działa,
- przy przejściu na drugą stronę, drobiazg: brak sprawdzenia, czy result['error'] nie jest przypadkiem None,
- inna konstrukcja system: user: prompta i brak explicite, że odpowiedzią jest json, czyli trzeba narzucić z góry jak ma być zbudowany klient do gpt,
- pomieszało mu się, kiedy ma być dodana końcówka .pkl a kiedy nie, przy ładowaniu modelu,
- zamiast przyjąć, że w csv są kolumny finish_sec i age to je próbuje odszukać na zasadzie substringów, bezskutecznie, cała pętelka do usunięcia,
- to nad czym teraz siedzę, to zastosowanie get_object przy pobieraniu csv z s3 i prawdopodobnie w resulcie nie jest to DataFrame,
-
-
- we wszystkich akcjach w necie, po takim wygenerowaniu kodu z promptu autorzy prześcigali się w dopowiadaniu sonnetowi kolejnymi podpromptami co poprawić, żeby zadziałało, i w mig odgadywali co jest nie tak np. endpoint nie działa, bo zapytanie jest małymi literami a endpoint ma dużą literę i trzeba go skorygować - no przecież to oczywiste, że tak może być i należy na to zwrócić uwagę nawet jeszcze przed ochroną na None, to takie proste, itd, itd.
-
-
- dlatego niestety, na tym etapie trzeba ten kod doprowadzić do działania ręcznie,
