
import streamlit as st
import pandas as pd
import boto3
import random
import os
import time
from langfuse import Langfuse
from langfuse.decorators import observe
from pycaret.regression import predict_model
from pydantic import ValidationError
from config import Config
from utils.time_utils import convert_time_to_seconds
from utils.data_extraction import retrieve_structure
from utils.prediction import load_model_from_s3, load_model_from_disk

# --- Inicjalizacja ---
session = boto3.session.Session()
client = session.client(
    's3',
    region_name='us-east-1',
    endpoint_url=Config.AWS_ENDPOINT_URL_S3,
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
)

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

# --- Funkcje pomocnicze ---
def predict_halfmarathon_time(model, df):
    try:
        st.write(f"🔍 Typ modelu: {type(model)}")
        st.write(f"🔍 Dane wejściowe: {df.head()}")
        prediction = predict_model(model, data=df)
        st.write(f"🔍 Wynik przewidywania: {prediction['Label'][0]}")
        return prediction['Label'][0]
    except Exception as e:
        raise Exception(f"❗ Błąd podczas przewidywania czasu: {e}")

def map_age_to_category(wiek):
    if 10 <= wiek <= 19:
        return 1
    elif 20 <= wiek <= 29:
        return 2
    elif 30 <= wiek <= 49:
        return 3
    elif 50 <= wiek <= 69:
        return 4
    elif 70 <= wiek <= 99:
        return 5
    else:
        raise ValueError("Wiek musi być w zakresie 10-99 lat.")

@observe
def log_model_choice(model_choice):
    st.write(f"Model wybrany: {model_choice}")

# --- UI: Nagłówek ---
st.markdown("<h1 style='text-align: center; font-family: cursive;'>🏃‍♂️ Kalkulator maratończyka wrocławskiego 🏃‍♀️</h1>", unsafe_allow_html=True)
st.image("marathon.png", use_container_width=True)

# --- Wybór modelu ---
model_choice = st.radio("📦 Skąd załadować model?", ["S3", "Dysk lokalny"])
log_model_choice(model_choice)

model_halfmarathon = None
if model_choice == "S3":
    with st.spinner("🔄 Ładuję model z S3..."):
        try:
            model_halfmarathon = load_model_from_s3(client, 'marathon_pipeline_regression_model.pkl', 'marathon_pipeline_regression_model.pkl')
            st.success("✅ Model załadowany z S3!")
        except Exception as e:
            st.error(f"❌ Błąd ładowania modelu: {e}")
else:
    with st.spinner("🔄 Ładuję model z dysku..."):
        try:
            model_halfmarathon = load_model_from_disk("models/marathon_pipeline_regression_model.pkl")
            st.success("✅ Model załadowany z dysku!")
        except Exception as e:
            st.error(f"❌ Błąd ładowania modelu: {e}")

# --- Formularz użytkownika ---
with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        wiek = st.number_input("🎂 Podaj swój wiek:", min_value=10, max_value=99, value=30)
        plec = st.radio("🧑‍🤝‍🧑 Wybierz płeć:", options=["Mężczyzna", "Kobieta"])
    with col2:
        czas_5km = st.text_input("⏱️ Podaj czas na 5 km (format: mm:ss)", "00:00")
        tempo_stabilnosc = st.number_input("📊 Podaj tempo stabilności (domyślnie 0.1)", min_value=0.0, max_value=10.0, value=0.1, step=0.01)
    submitted = st.form_submit_button("🔍 Oblicz przewidywany czas")

# --- Textarea i jego obsługa ---
if "dane_użytkownika" not in st.session_state:
    st.session_state["dane_użytkownika"] = ""

st.markdown("<div class='custom-label'>Proszę wpisz swoje dane: wiek, płeć oraz ile czasu zajmuje Ci pokonanie dystansu 5 km.</div>", unsafe_allow_html=True)

dane_użytkownika = st.text_area("", value=st.session_state["dane_użytkownika"], height=100)

# --- Sprawdzanie danych ---
if st.button("Sprawdź dane", key="check_data"):
    try:
        # Pobieranie danych
        dane = retrieve_structure(dane_użytkownika)
        st.session_state.update({
            "wiek": dane["Wiek"],
            "plec": dane["Płeć"],
            "czas_5km": dane["Czas_5_km"]
        })

        # Konwersja danych wejściowych na wymagane przez model
        dane_json = {
            "5_km_tempo_s": convert_time_to_seconds(st.session_state["czas_5km"]),
            "kategoria_wiekowa_num": map_age_to_category(st.session_state["wiek"]),
            "tempo_stabilność": tempo_stabilnosc,
            "płeć": st.session_state["plec"]
        }

        st.write("Dane wejściowe do modelu:", dane_json)

        brakujace_dane = []
        if st.session_state["wiek"] is None:
            brakujace_dane.append("wieku")
        if st.session_state["plec"] is None:
            brakujace_dane.append("płci")
        if st.session_state["czas_5km"] is None:
            brakujace_dane.append("czasu na 5 km")

        if brakujace_dane:
            st.error("Brakuje danych dla: " + ", ".join(brakujace_dane))
        else:
            st.success("Dane poprawne. Rozpoczynam predykcję...")
            time.sleep(2)

            df_predykcja = pd.DataFrame([dane_json])
            st.write("DataFrame przed predykcją:", df_predykcja)

            try:
                predicted_time = model_halfmarathon.predict(df_predykcja)[0]
                h, m, s = int(predicted_time / 3600), int((predicted_time % 3600) / 60), int(predicted_time % 60)
                predicted_time_format = f"{h:02d}:{m:02d}:{s:02d}"

                kolory = ["#fab387", "#f9e2af", "#89b4fa", "#a6e3a1", "#FFA500", "#a6adc8", "#eba0ac"]
                kolory = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd", "#c8d6e5"]
                title = "Czas ukończenia półmaratonu:"

                title_container = st.empty()
                time_container = st.empty()

                # --- ANIMACJA TYTUŁU ---
                title_html = "<div style='text-align: center; font-size: 24px; font-family: cursive;'>"
                for litera in title:
                    kolor = random.choice(kolory)
                    title_html += f"<span style='color: {kolor};'>{litera}</span>"
                    title_container.markdown(title_html + "</div>", unsafe_allow_html=True)
                    time.sleep(0.05)

                time.sleep(0.5)  # Pauza po tytule

                # --- ANIMACJA CZASU ---
                time_html = "<div style='text-align: center; font-size: 46px; font-weight: bold; font-family: cursive;'>"
                for znak in predicted_time_format:
                    kolor = random.choice(kolory)
                    time_html += f"<span style='color: {kolor};'>{znak}</span>"
                    time_container.markdown(time_html + "</div>", unsafe_allow_html=True)
                    time.sleep(0.15)

            except Exception as e:
                st.error(f"Błąd predykcji: {e}")

            time.sleep(1)
            if st.button("Wyczyść dane", key="clear_button"):
                for key in ["dane_użytkownika", "wiek", "plec", "czas_5km"]:
                    st.session_state[key] = ""
                st.stop()

    except ValueError as e:
        st.error(f"Błąd: {e}")

    except ValidationError as e:
        missing_fields = [error['loc'][0] for error in e.errors()]
        messages = []
        if 'Wiek' in missing_fields:
            messages.append("Brakuje wieku.")
        if 'Płeć' in missing_fields:
            messages.append("Brakuje płci.")
        if 'Czas_5_km' in missing_fields:
            messages.append("Brakuje czasu na 5 km.")
        st.error("Błąd: " + " ".join(messages))

    except Exception as e:
        st.error(f"Nieoczekiwany błąd: {e}")
