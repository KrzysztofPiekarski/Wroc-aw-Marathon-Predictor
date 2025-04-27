import streamlit as st
import pandas as pd
import boto3
import joblib
import io
import os
from langfuse import Langfuse
from langfuse.decorators import observe
from pycaret.regression import predict_model
from config import Config
from utils.time_utils import format_time_string, convert_time_to_seconds, format_time
from utils.data_extraction import retrieve_structure
from utils.prediction import load_model_from_s3, load_model_from_disk

# Konfiguracja klienta AWS S3
session = boto3.session.Session()
client = session.client(
    's3',
    region_name='us-east-1',
    endpoint_url=Config.AWS_ENDPOINT_URL_S3,
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
)

# Inicjalizacja Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")  # Opcjonalnie
)

# Funkcja do przewidywania wyniku
def predict_halfmarathon_time(model, df):
    try:
        st.write(f"🔍 Typ modelu: {type(model)}")
        st.write(f"🔍 Dane wejściowe: {df.head()}")
        
        # Przewidywanie za pomocą PyCaret (zamiast model.predict)
        prediction = predict_model(model, data=df)
        
        # Wyciąganie wyniku z kolumny 'Label'
        st.write(f"🔍 Wynik przewidywania: {prediction['Label'][0]}")
        return prediction['Label'][0]  # Zwróć przewidywaną wartość
    except Exception as e:
        raise Exception(f"❗ Błąd podczas przewidywania czasu: {e}")

# Funkcja mapująca wiek na kategorię wiekową
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

# Funkcja obserwująca wybór modelu
@observe
def log_model_choice(model_choice):
    st.write(f"Model wybrany: {model_choice}")

# Interfejs użytkownika
st.markdown("<h1 style='text-align: center; font-family: cursive;'>🏃‍♂️ Kalkulator maratończyka wrocławskiego 🏃‍♀️</h1>", unsafe_allow_html=True)
st.image("marathon.png", use_container_width=True)

# Wybór źródła modelu
model_choice = st.radio("📦 Skąd załadować model?", ["S3", "Dysk lokalny"])

log_model_choice(model_choice)

model_halfmarathon = None

if model_choice == "S3":
    with st.spinner("🔄 Ładuję model z S3..."):
        try:
            model_halfmarathon = load_model_from_s3(client, 'halfmarathon20232024', 'marathon_pipeline_regression_model.pkl')
            st.success("✅ Model załadowany z S3!")
        except Exception as e:
            st.error(f"❌ Wystąpił błąd podczas ładowania modelu: {e}")
elif model_choice == "Dysk lokalny":
    with st.spinner("🔄 Ładuję model z dysku..."):
        try:
            model_path = "models/marathon_pipeline_regression_model.pkl"
            model_halfmarathon = load_model_from_disk(model_path)
            st.success("✅ Model załadowany z dysku!")
        except Exception as e:
            st.error(f"❌ Wystąpił błąd podczas ładowania modelu: {e}")

# Formularz danych użytkownika
with st.form("prediction_form"):
    col1, col2 = st.columns(2)

    with col1:
        wiek = st.number_input("🎂 Podaj swój wiek:", min_value=10, max_value=99, value=30)
        plec = st.radio("🧑‍🤝‍🧑 Wybierz płeć:", options=["Mężczyzna", "Kobieta"])
    
    with col2:
        czas_5km = st.text_input("⏱️ Podaj czas na 5 km (format: mm:ss)", "00:00")
        tempo_stabilnosc = st.number_input("📊 Podaj tempo stabilności (domyślnie 0.1)", min_value=0.0, max_value=10.0, value=0.1, step=0.01)

    submitted = st.form_submit_button("🔍 Oblicz przewidywany czas")

# Funkcja przygotowująca dane
def prepare_input_data(wiek, płeć, czas_5km, tempo_stabilność):
    """Przygotowuje dane wejściowe do predykcji."""
    if not (10 <= wiek <= 99):
        raise ValueError("Wiek musi być w zakresie 10-99 lat.")
    if tempo_stabilnosc < 0 or tempo_stabilnosc > 10:
        raise ValueError("Stabilność tempa musi być liczbą w zakresie 0-10.")
    
    # Formatowanie czasu 5 km
    czas_5km = format_time_string(czas_5km)

    # Konwersja czasu na sekundy
    czas_5km_w_sekundach = convert_time_to_seconds(czas_5km)
    
    # Mapowanie wieku na kategorię wiekową
    kategoria_wiekowa_num = map_age_to_category(wiek)
    
    # Mapowanie płci na liczbę
    plec_num = 0 if plec == "Mężczyzna" else 1

    # Przygotowanie danych wejściowych w postaci słownika
    dane_json = {
        "kategoria_wiekowa_num": kategoria_wiekowa_num,
        "płeć": płeć,
        "5_km_tempo_s": czas_5km_w_sekundach,
        "tempo_stabilność": tempo_stabilność
    }

    return dane_json, plec_num

# Funkcja pokazująca wynik
def show_summary(wiek, plec, czas_5km, tempo_stabilnosc, formatted_time):
    st.success("✅ Twoje dane:")
    st.markdown(f"""
    - 🎂 **Wiek:** {wiek} lat  
    - 🧑‍🤝‍🧑 **Płeć:** {plec}  
    - ⏱️ **Czas na 5 km:** {czas_5km}  
    - 📊 **Stabilność tempa:** {tempo_stabilnosc} 
    """)
    st.success(f"🏅 Przewidywany czas ukończenia półmaratonu: **{formatted_time}**.") 

if submitted:
    if model_halfmarathon is None:
        st.error("❗ Model nie został załadowany. Proszę najpierw wybrać źródło i załadować model.")
    else:
        try:
            # Przygotowanie danych
            try:
                dane_json, plec_num = prepare_input_data(wiek, plec, czas_5km, tempo_stabilnosc)
            except ValueError as ve:
                st.error(f"⚠️ Błąd danych wejściowych: {ve}")
                st.stop()  # Zatrzymaj dalsze działanie jeśli dane są złe

            # Predykcja
            df_predykcja = pd.DataFrame([dane_json])
            predicted_time = predict_halfmarathon_time(model_halfmarathon, df_predykcja)
            formatted_time = format_time(predicted_time)

            # Wyświetlenie wyniku
            show_summary(wiek, plec, czas_5km, tempo_stabilnosc, formatted_time)

        except Exception as e:
            st.error(f"❌ Wystąpił nieoczekiwany błąd: {e}") 