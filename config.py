import os
from dotenv import load_dotenv

load_dotenv()  # Załaduj dane z pliku .env

class Config:
    # DigitalOcean Spaces
    AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
    AWS_ENDPOINT_URL_S3 = os.environ["AWS_ENDPOINT_URL_S3"]
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    
    # Inne ustawienia, np. OpenAI
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    LANGFUSE_PUBLIC_KEY = os.environ["LANGFUSE_PUBLIC_KEY"]
    LANGFUSE_SECRET_KEY = os.environ["LANGFUSE_SECRET_KEY"]
    LANGFUSE_HOST = os.environ["LANGFUSE_HOST"]

    # Model S3
    BUCKET_NAME = "halfmarathon"
    MODEL_KEY = "marathon_pipeline_regression_model.pkl"