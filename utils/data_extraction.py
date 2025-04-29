import instructor
import openai
from pydantic import BaseModel, Field

# Patchowanie klienta OpenAI
client = instructor.patch(openai.Client())

# Definiowanie modelu danych
class UserData(BaseModel):
    Wiek: int | None = Field(default=None, ge=10, le=99)
    Płeć: str | None = Field(default=None)
    Czas_5_km: str = Field(default="00:00:00")

# Funkcja wyciągająca dane użytkownika
def retrieve_structure(text):
    prompt = f"""
        Wyciągnij z tekstu następujące informacje:
        - Wiek (liczba całkowita, z zakresu 10 <= x <= 99, w przeciwnym razie zwróć None)
        - Płeć (K dla kobiety, M dla mężczyzny, lub None, jeśli nie można ustalić)
        - Czas na 5 km (w formacie HH:MM:SS, lub 00:00:00 jeśli nie można ustalić)

        Tekst:
        '{text}'
    """
    try:
        # Wywołanie modelu OpenAI za pomocą Langfuse i OpenAI API
        res = client.chat.completions.create(
            model="gpt-4o-mini",  # Upewnij się, że to właściwy model
            temperature=0,
            response_model=UserData,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.model_dump()
    except Exception as e:
        raise Exception(f"Błąd podczas przetwarzania tekstu: {e}")
