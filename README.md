# Wrocław Marathon Predictor

This application allows users to predict their half marathon time based on their 5k time. It uses regression models that take into account age, gender, pace stability, and 5k time to predict the time needed to complete a half marathon.

## Features

- **Half Marathon Time Prediction**: Enter your age, gender, 5k time, and pace stability to get a predicted half marathon time.
- **Model Source Selection**: You can choose to load the model from a local disk or from a cloud repository (e.g., DigitalOcean Spaces via S3).
- **Data Formatting**: The app supports various time formats (e.g., MM:SS, HH:MM:SS) and maps them to appropriate input data.

How it Works
This app uses machine learning models to predict a runner's half marathon time based on their performance in a 5k. The process follows these steps:

Data Input: The user enters their age, gender, 5k time, and pace stability.

Model Selection: The user selects where to load the model from (S3 or local disk). The model is a trained regression model that uses the input data to predict the half marathon time.

Data Preparation: The input data is formatted and preprocessed, including converting the 5k time to seconds and categorizing the age and gender.

Prediction: The preprocessed data is passed to the regression model to predict the half marathon time.

Output: The predicted time is displayed in a human-readable format (e.g., hours, minutes, and seconds).

The app uses Langfuse and OpenAI for language processing, allowing users to extract and format data from text inputs.

## Przewidywanie Czasu
Aplikacja korzysta z modeli regresyjnych wytrenowanych na danych biegowych, w tym czasach na 5 km, wieku, płci oraz stabilności tempa. Modele te przewidują czas, jaki użytkownikowi zajmie ukończenie półmaratonu na podstawie wprowadzonych danych. Modele są przechowywane na DigitalOcean Spaces (S3) lub mogą być załadowane z lokalnego dysku.

## Requirements

To run the application, you need to install the following packages:

- Python 3.x
- Streamlit
- Pandas
- Joblib
- Boto3
- Langfuse
- Pydantic
- OpenAI
- dotenv

You can install all the required dependencies with the following command:

```bash
pip install -r requirements.txt