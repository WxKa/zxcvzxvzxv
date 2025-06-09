
###### Anthropic Console

źródło: gemini-2.5-flash

* w prompt trzeba dopisać, że:
 - python 3.11
 - csv sep =';'
 - nie dopisuj credentials do s3 client create

# kod się wygenerował i jest <span style="color: red;">BARDZO DOBRZE</span>

##### żeby działało, i żeby nie przedłużać, zrobiłem poprawki na żywca w wygenerownym app.py:
- do prompta do gpt dodałem:
     response_format={"type": "json_object"},
- zmieniłem odwołania do kolumny za pomocą 'time_seconds' na 'finish_sec', bo tak ją nazwałem w swoim w csv,

###### cenzura.
