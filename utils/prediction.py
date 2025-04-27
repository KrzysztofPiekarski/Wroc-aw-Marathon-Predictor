import joblib
import pandas as pd
import io  # Nie zapomnij zaimportować io

# Funkcja do ładowania modelu z S3
def load_model_from_s3(client, bucket_name, model_key):
    try:
        # Pobieranie modelu z S3
        response = client.get_object(Bucket=bucket_name, Key=model_key)
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
