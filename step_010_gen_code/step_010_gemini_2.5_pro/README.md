
###### Google AI Studio

źródło: gemini-2.5-flash

* w prompt trzeba dopisać, że:
 - python 3.11
 - csv sep =';'
 - nie dopisuj credentials do OpenAI i S3

# kod się wygenerował i jest <span style="color: red;">WSPANIALE</span>

##### nawet mój ostatni wynalazek: **prompt roller** jest zaimplementowany na pierwszej stronie,

##### żeby działało, i żeby nie przedłużać, zrobiłem poprawki na żywca:
- do S3 i tak dopisał credentiale więc kasujemy,
- zmieniłem odwołania do kolumny za pomocą 'time_sec' na 'finish_sec', bo tak ją nazwałem w swoim w csv,
