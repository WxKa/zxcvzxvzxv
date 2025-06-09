# llm_parser.py
import os
import json
from langfuse.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Zgodnie z poleceniem, używamy klienta Langfuse
client = OpenAI(
    # Klucze Langfuse są opcjonalne, ale pozwalają na śledzenie wywołań
    # public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    # secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
)

def parse_runner_data_with_llm(text_input: str) -> dict:
    """Używa LLM do ekstrakcji i walidacji danych biegacza z tekstu."""

    system_prompt = """
    Twoim zadaniem jest precyzyjne wyekstrahowanie informacji o biegaczu z podanego tekstu.
    Zwróć odpowiedź WYŁĄCZNIE w formacie JSON. Bez żadnych dodatkowych wyjaśnień.

    Oczekiwany format wyjściowy JSON i jego klucze:
    {
      "age": <liczba całkowita>,
      "gender": <"M" lub "F">,
      "5_km_sec": <liczba zmiennoprzecinkowa>
    }

    Zasady ekstrakcji i walidacji:
    1.  **age**: Wiek musi być liczbą całkowitą w przedziale od 18 do 105.
    2.  **gender**: Płeć musi być zmapowana na "M" (dla mężczyzny, m, male) lub "F" (dla kobiety, k, female).
    3.  **5_km_sec**:
        -   Jeśli podano czas na 5 km (np. "25:30", "25 min 30 sek"), przelicz go na łączną liczbę sekund.
        -   Jeśli podano tempo na 1 km (np. "5'06''", "5:06/km", "tempo 5 minut 6 sekund"), najpierw przelicz je na sekundy na kilometr, a następnie pomnóż przez 5, aby uzyskać czas na 5 km w sekundach.
        -   Wynikowy czas na 5 km w sekundach musi mieścić się w zakresie od 900 (15 minut) do 7200 (120 minut).
    -   Jeśli którejś informacji nie da się wyekstrahować, zwróć `null` dla tego pola.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input},
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        response_json = json.loads(completion.choices[0].message.content)

        # Walidacja po stronie Pythona - NIGDY nie ufaj w 100% LLM
        errors = []
        age = response_json.get("age")
        gender = response_json.get("gender")
        time_5k_sec = response_json.get("5_km_sec")

        if not (isinstance(age, int) and 18 <= age <= 105):
            errors.append(f"Wiek musi być liczbą całkowitą z zakresu 18-105 (otrzymano: {age}).")
        if gender not in ["M", "F"]:
            errors.append(f"Płeć musi być 'M' lub 'F' (otrzymano: {gender}).")
        if not (isinstance(time_5k_sec, (int, float)) and 900 <= time_5k_sec <= 7200):
            time_min = f"{time_5k_sec / 60:.1f} min" if time_5k_sec else "brak"
            errors.append(f"Czas na 5km musi być w realistycznym zakresie [15, 120] minut (otrzymano: {time_min}).")

        if errors:
            raise ValueError("Błędy walidacji: " + " ".join(errors))

        return {
            "age": age,
            "gender": gender,
            "5_km_sec": float(time_5k_sec)
        }

    except json.JSONDecodeError:
        raise ValueError("Model LLM zwrócił niepoprawny format JSON. Spróbuj sformułować dane inaczej.")
    except Exception as e:
        raise ValueError(f"Błąd podczas parsowania danych przez AI: {e}")
