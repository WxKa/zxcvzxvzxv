# utils.py
import pandas as pd

def seconds_to_hms(seconds: float) -> str:
    """Konwertuje sekundy na format HH:MM:SS."""
    if pd.isna(seconds): return "N/A"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def seconds_to_ms(seconds: float) -> str:
    """Konwertuje sekundy na format MM:SS."""
    if pd.isna(seconds): return "N/A"
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def create_pace_conversion_table() -> pd.DataFrame:
    """Tworzy tabelę konwersji tempa na prędkość do wyświetlenia w aplikacji."""
    paces_min_sec = []
    for minutes in range(3, 10):
        for seconds in [0, 15, 30, 45]:
            paces_min_sec.append(f"{minutes}:{seconds:02d}")

    data = []
    for pace_str in paces_min_sec:
        minutes, seconds = map(int, pace_str.split(':'))
        total_seconds_per_km = minutes * 60 + seconds
        speed_kmh = 3600 / total_seconds_per_km
        data.append({"Tempo (min:sek / km)": pace_str, "Prędkość (km/h)": f"{speed_kmh:.2f}"})

    return pd.DataFrame(data)
