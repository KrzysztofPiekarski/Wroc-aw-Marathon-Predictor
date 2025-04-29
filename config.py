import os
from dotenv import load_dotenv

load_dotenv()  # Załaduj dane z pliku .env

class Config:
    # DigitalOcean Spaces
    AWS_REGION = os.environ.get("AWS_REGION")
    AWS_ENDPOINT_URL_S3 = os.environ.get("AWS_ENDPOINT_URL_S3")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    # Inne ustawienia, np. OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST")

    # Model S3
    BUCKET_NAME = "halfmarathon"
    MODEL_KEY = "marathon_pipeline_regression_model.pkl"