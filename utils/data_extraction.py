import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from langfuse.decorators import observe
import streamlit as st
import os


def get_patched_openai_client():
    """
    Obsługuje ochronę klucza API OpenAI, jego pobranie z .env lub formularza,
    oraz zwraca spatchowanego klienta OpenAI przez `instructor.patch()`.
    """
    # Sprawdzenie, czy klucz API OpenAI już istnieje w sesji
    if "openai_api_key" not in st.session_state:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            st.session_state["openai_api_key"] = openai_api_key
        else:
            st.info("Podaj swój klucz API OpenAI, aby móc korzystać z tej aplikacji")
            st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
            if st.session_state["openai_api_key"]:
                st.session_state["openai_api_key"] = st.session_state["openai_api_key"]  # Upewniamy się, że zapisujemy klucz
                st.rerun()

    # Jeśli klucz API nadal nie został podany, zatrzymaj aplikację
    if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
        st.stop()

    # Tworzenie klienta OpenAI i jego patchowanie
    openai_client = OpenAI(api_key=st.session_state["openai_api_key"])
    patched_client = instructor.patch(openai_client)
    return patched_client


# Uzyskujemy spatchowanego klienta OpenAI
instructor_openai_client = get_patched_openai_client()

# Definicja danych użytkownika jako modelu Pydantic
class UserData(BaseModel):
    Wiek: int | None = Field(default=None, ge=10, le=99)
    Płeć: str | None = Field(default=None)
    Czas_5_km: str = Field(default="00:00:00")


@observe
def retrieve_structure(text):
    prompt = f"""
        Wyciągnij z tekstu następujące informacje:
        - Wiek (liczba całkowita, z zakresu 10<= x <= 99, w przeciwnym razie zwróć None)
        - Płeć (K dla kobiety, M dla mężczyzny, lub None, jeśli nie można ustalić)
        - Czas na 5 km (w formacie HH:MM:SS, lub 00:00:00 jeśli nie można ustalić)

        Postaraj się być jak najbardziej elastyczny i "inteligentny" w interpretacji danych.
        - Jeśli podano imię, spróbuj na jego podstawie określić płeć, zwróć również uwagę na czasowniki męskoosobowe i żeńskoosobowe.
        - Jeśli czas jest podany w innym formacie niż HH:MM:SS, spróbuj go przekonwertować.
        - Jeśli brakuje niektórych danych, oznacz je jako wartość domyślną.

        Tekst:
        '{text}'
    """

    # Wykonanie zapytania do API OpenAI
    res = instructor_openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_model=UserData,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    
    # Zwrócone dane
    dane = res.model_dump()

    # Sprawdzamy, czy wiek jest pustym stringiem (co oznacza, że nie został znaleziony lub jest niepoprawny)
    if dane["Wiek"] == "":
        dane["Wiek"] = None  # Ustawiamy wiek na None
    
    return dane

# Przykładowe użycie:
# (Tutaj możesz dodać formularz w Streamlit do wprowadzenia danych przez użytkownika)

