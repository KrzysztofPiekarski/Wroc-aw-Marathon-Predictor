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
# Konfiguracja dostępu do DigitalOcean Spaces
session = boto3.session.Session()
client = session.client(
    's3',
    region_name=os.getenv('AWS_REGION'),
    endpoint_url=os.getenv('AWS_ENDPOINT_URL_S3'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
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
    st.write(f"📌 Model wybrany: {model_choice}")

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
            st.success("✅  Model załadowany z dysku!")
        except Exception as e:
            st.error(f"❌ Błąd ładowania modelu: {e}")

# --- Wybór sposobu wprowadzania danych ---
input_method = st.radio("✍️ Wybierz sposób wprowadzania danych:", ["📝 Formularz", "📄 Textarea"], horizontal=True)

# --- Dane wejściowe ---
tempo_stabilnosc = 0.1
if "dane_użytkownika" not in st.session_state:
    st.session_state["dane_użytkownika"] = ""

if input_method == "📝 Formularz":
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        with col1:
            wiek = st.number_input("🎂 Podaj swój wiek:", min_value=10, max_value=99, value=30)
            plec = st.radio("🧑‍🤝‍🧑 Wybierz płeć:", options=["Mężczyzna", "Kobieta"])
        with col2:
            czas_5km = st.text_input("⏱️ Podaj czas na 5 km (format: mm:ss)", "00:00")
            tempo_stabilnosc = st.number_input("📊 Podaj tempo stabilności (domyślnie 0.1)", min_value=0.0, max_value=10.0, value=0.1, step=0.01)
        submitted = st.form_submit_button("🔍 Oblicz przewidywany czas")

        if submitted:
            st.session_state.update({
                "wiek": wiek,
                "plec": plec,
                "czas_5km": czas_5km
            })

else:
    st.markdown("""
        <style>
        .custom-label {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='custom-label'>⚠️ Jeśli pierwsze rozwiązanie nie działa poprawnie 😊</div>", unsafe_allow_html=True)
    st.markdown("<div class='custom-label'>📝 Wpisz dane: wiek, płeć i czas na 5 km.</div>", unsafe_allow_html=True)

    dane_użytkownika = st.text_area("", value=st.session_state["dane_użytkownika"], height=100)

    if st.button("📥 Sprawdź dane", key="check_data"):
        try:
            dane = retrieve_structure(dane_użytkownika)
            st.session_state.update({
                "wiek": dane["Wiek"],
                "plec": dane["Płeć"],
                "czas_5km": dane["Czas_5_km"]
            })
        except (ValueError, ValidationError) as e:
            st.error(f"❌ Błąd danych tekstowych: {e}")
        except Exception as e:
            st.error(f"❌ Nieoczekiwany błąd: {e}")

# --- Predykcja ---
if all(k in st.session_state for k in ["wiek", "plec", "czas_5km"]) and st.session_state["wiek"] and st.session_state["plec"] and st.session_state["czas_5km"]:
    try:
        dane_json = {
            "5_km_tempo_s": convert_time_to_seconds(st.session_state["czas_5km"]),
            "kategoria_wiekowa_num": map_age_to_category(st.session_state["wiek"]),
            "tempo_stabilność": tempo_stabilnosc,
            "płeć": st.session_state["plec"]
        }

        df_predykcja = pd.DataFrame([dane_json])
        st.write("📄 Dane wejściowe do modelu:", dane_json)

        predicted_time = model_halfmarathon.predict(df_predykcja)[0]
        h, m, s = int(predicted_time / 3600), int((predicted_time % 3600) / 60), int(predicted_time % 60)
        predicted_time_format = f"{h:02d}:{m:02d}:{s:02d}"

        kolory = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd", "#c8d6e5"]
        title = "⏱️ Czas ukończenia półmaratonu 🎉:"

        title_container = st.empty()
        time_container = st.empty()

        # --- ANIMACJA TYTUŁU ---
        title_html = "<div style='text-align: center; font-size: 45px; font-family: cursive;'>"
        for litera in title:
            kolor = random.choice(kolory)
            title_html += f"<span style='color: {kolor};'>{litera}</span>"
            title_container.markdown(title_html + "</div>", unsafe_allow_html=True)
            time.sleep(0.05)

        time.sleep(0.5)

        # --- ANIMACJA CZASU ---
        time_html = "<div style='text-align: center; font-size: 66px; font-weight: bold; font-family: cursive;'>"
        for znak in predicted_time_format:
            kolor = random.choice(kolory)
            time_html += f"<span style='color: {kolor};'>{znak}</span>"
            time_container.markdown(time_html + "</div>", unsafe_allow_html=True)
            time.sleep(0.15)

        if st.button("🧼 Wyczyść dane", key="clear_button"):
            for key in ["dane_użytkownika", "wiek", "plec", "czas_5km"]: 
                if key in st.session_state:
                    st.session_state[key] = ""
            st.rerun()

    except Exception as e:
        st.error(f"🚨 Błąd predykcji: {e}")
