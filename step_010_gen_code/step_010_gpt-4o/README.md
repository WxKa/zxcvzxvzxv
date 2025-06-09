
###### ChatGPT

źródło: gemini-2.5-flash

* w prompt trzeba dopisać, że:
 - python 3.11
 - streamlit >= 1.27

# kod się wygenerował i jest <span style="color: red;">SCHLUDNY</span>

##### żeby działało, i żeby nie przedłużać, zrobiłem poprawki na żywca:
  - poprawka w regexp: zmiana hh:mm:ss na mm:ss dla czasu na 5 km
  - zamiana wszystkich experimental_rerun na rerun (nie rozumie streamlit version)
  - poprawka błędu streamit, gdzie chemy mieć takie same radio na każdej z dwóch zakładek,
    wtedy trzeba zmienić zawartość options, żeby nie były takie same,

