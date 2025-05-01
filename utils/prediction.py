import joblib
import pandas as pd
import io  # Nie zapomnij zaimportować io

BUCKET_NAME = 'halfmarathon2023'
MODEL_KEY = 'halfmarathon_model.pkl'

# Funkcja do ładowania modelu z S3
def load_model_from_s3(client, bucket_name, model_key):
    try:
        # Pobieranie modelu z S3
        response = client.get_object(Bucket=BUCKET_NAME, Key=MODEL_KEY)
        model_bytes = response['Body'].read()
        model = joblib.load(io.BytesIO(model_bytes))  # Wczytanie modelu z pamięci
        return model
    except Exception as e:
        raise Exception(f"Wystąpił błąd podczas ładowania modelu: {e}")

# Funkcja do ładowania modelu z dysku
def load_model_from_disk(model_path):
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        raise Exception(f"❗ Błąd podczas ładowania modelu z dysku: {e}")
