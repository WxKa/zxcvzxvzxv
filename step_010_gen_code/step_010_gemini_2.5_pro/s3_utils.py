# s3_utils.py
import os
import pandas as pd
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from pycaret.regression import load_model
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "wk1"

@st.cache_resource
def get_s3_client():
    """Tworzy i zwraca klienta S3. Wynik jest cachowany dla całej sesji."""
    try:
        s3_client = boto3.client('s3')
        s3_client.list_buckets()  # Sprawdzenie poprawności połączenia
        return s3_client
    except (NoCredentialsError, ClientError) as e:
        st.error(f"Błąd konfiguracji AWS S3. Sprawdź swoje klucze w pliku .env. Błąd: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache na 1 godzinę
def load_csv_from_s3(_s3_client, file_key: str) -> pd.DataFrame | None:
    """Ładuje plik CSV z S3, używając separatora ';'. Wynik jest cachowany."""
    if not _s3_client:
        return None
    try:
        obj = _s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        # Zgodnie z wymaganiem, używamy separatora ';'
        return pd.read_csv(obj['Body'], sep=';')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            st.error(f"Nie znaleziono pliku w S3: {file_key}")
        else:
            st.error(f"Błąd S3 podczas pobierania pliku '{file_key}': {e}")
        return None
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd podczas przetwarzania pliku CSV: {e}")
        return None

@st.cache_data(ttl=3600)
def download_file_from_s3(_s3_client, file_key: str, local_path: str):
    """Pobiera plik z S3 i zapisuje go lokalnie."""
    if not _s3_client:
        return False
    try:
        _s3_client.download_file(S3_BUCKET, file_key, local_path)
        return True
    except ClientError as e:
        st.error(f"Błąd S3 podczas pobierania modelu '{file_key}': {e}")
        return False

@st.cache_resource
def get_prediction_model():
    """Ładuje model PyCaret, pobierając go z S3, jeśli nie istnieje lokalnie."""
    s3_client = get_s3_client()
    if not s3_client:
        return None

    model_s3_key = "zadanie_9/models/time_sec_model.pkl"
    local_model_path_base = "time_sec_model"
    local_model_path_pkl = f"{local_model_path_base}.pkl"

    if not os.path.exists(local_model_path_pkl):
        st.info("Model nie istnieje lokalnie. Pobieranie z S3...")
        with st.spinner("Pobieranie modelu... To może chwilę potrwać."):
            if not download_file_from_s3(s3_client, model_s3_key, local_model_path_pkl):
                return None

    try:
        model = load_model(local_model_path_base)
        st.success("Model predykcyjny został pomyślnie załadowany.")
        return model
    except Exception as e:
        st.error(f"Nie udało się załadować modelu PyCaret z pliku. Błąd: {e}")
        return None
