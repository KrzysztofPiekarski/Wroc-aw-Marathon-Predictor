
import pandas as pd

# Standaryzacja formatu czasu
def format_time_string(time_str: str) -> str:
    parts = time_str.strip().split(':')
    if len(parts) == 2:
        # Format MM:SS -> dodaj godziny
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    elif len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    else:
        raise ValueError("Nieprawidłowy format. Użyj MM:SS lub HH:MM:SS (np. 25:30 lub 00:25:30).")

# Formatowanie czasu w sekundach do czytelnego zapisu
def format_time(minutes: float) -> str:
    total_seconds = int(minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}min {seconds}s"
    elif minutes > 0:
        return f"{minutes}min {seconds}s"
    else:
        return f"{seconds}s"

# Konwersja czasu tekstowego na sekundy
def convert_time_to_seconds(time: str) -> int:
    if pd.isnull(time) or time.upper() in ['DNS', 'DNF', '']:
        raise ValueError("Czas na 5 km jest wymagany.")

    time = format_time_string(time)  # Ujednolicenie formatu
    parts = time.split(':')

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
    except ValueError:
        raise ValueError("Czas zawiera nieprawidłowe znaki. Użyj cyfr i dwukropków, np. 25:30.")

    total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds < 300:
        raise ValueError("Czas na 5 km musi być dłuższy niż 5 minut (300 sekund).")

    return total_seconds