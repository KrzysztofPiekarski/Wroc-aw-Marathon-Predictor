import re
import pandas as pd

# Funkcja do poprawiania formatu czasu
def format_time_string(time_str):
    parts = time_str.strip().split(':')
    if len(parts) == 2:
        # Jeżeli brak godzin (format MM:SS), dodajemy "00" na początek
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    elif len(parts) == 3:
        # Jeżeli poprawny format HH:MM:SS
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    else:
        raise ValueError("Nieprawidłowy format czasu. Poprawnie: HH:MM:SS.") 

# Funkcja do konwersji minut
def format_time(minutes):
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

# Funkcja konwertująca czas na sekundy
def convert_time_to_seconds(time):
    if pd.isnull(time) or time in ['DNS', 'DNF']:
        raise ValueError("Czas na 5 km jest wymagany.")

    print(f"Received time: {time}")  # Debug print

    if isinstance(time, str):
        parts = time.split(':')
        try:
            if len(parts) == 2:
                # Prawidłowy format MM:SS
                minutes = int(parts[0])
                seconds = int(parts[1])
            elif len(parts) == 3:
                # Format HH:MM:SS — ignorujemy godzinę
                minutes = int(parts[1])
                seconds = int(parts[2])
            else:
                raise ValueError("Niepoprawny format czasu. Podaj czas w formacie MM:SS, np. 25:30.")

            total_seconds = minutes * 60 + seconds
            print(f"Parsed values - Minutes: {minutes}, Seconds: {seconds}")  # Debug print

            if total_seconds < 300:
                raise ValueError("Czas na 5 km musi być dłuższy niż 5 minut (300 sekund).")

            return total_seconds
        except ValueError:
            raise ValueError("Błąd podczas przetwarzania czasu. Upewnij się, że wszystkie części to liczby.")
    else:
        raise ValueError("Czas na 5 km powinien być tekstem w formacie MM:SS lub HH:MM:SS.")
