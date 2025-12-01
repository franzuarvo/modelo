# config.py
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()


def get_config(name: str, default=None):
    """
    Lee SIEMPRE de variables de entorno.
    - En local: vienen del archivo .env
    - En Streamlit Cloud: vienen de la sección Secrets (también se exponen como env vars)
    """
    return os.getenv(name, default)


# -----------------------------
# Config Redis
# -----------------------------
# 👉 URL completa (Upstash u otro Redis gestionado)
REDIS_URL = get_config("REDIS_URL", "")

# Fallback por si algún día usas Redis local
REDIS_HOST = get_config("REDIS_HOST", "localhost")
REDIS_PORT = int(get_config("REDIS_PORT", "6379"))
REDIS_PASSWORD = get_config("REDIS_PASSWORD")  # normalmente None en local


# -----------------------------
# Config LinkedIn
# -----------------------------
LINKEDIN_GEO_ID_PERU = get_config("LINKEDIN_GEO_ID_PERU", "102927786")


# -----------------------------
# Ticketmaster / Eventbrite / RapidAPI
# -----------------------------
TICKETMASTER_API_KEY = get_config("TICKETMASTER_API_KEY", "")
RAPIDAPI_KEY = get_config("RAPIDAPI_KEY", "")
EVENTBRITE_TOKEN = get_config("EVENTBRITE_TOKEN", "")


# -----------------------------
# Vertex AI / Gemini
# -----------------------------
GCP_PROJECT_ID = get_config("GCP_PROJECT_ID", "prueba-419502")
GCP_LOCATION = get_config("GCP_LOCATION", "us-central1")
GEMINI_MODEL_NAME = get_config("GEMINI_MODEL_NAME", "gemini-2.5-pro")

# Ruta del JSON (para LOCAL)
GCP_SERVICE_ACCOUNT_FILE = get_config("GCP_SERVICE_ACCOUNT_FILE", "")

# Contenido JSON como string (para DEPLOY si usas JSON en un env var)
GCP_SERVICE_ACCOUNT_JSON = get_config("GCP_SERVICE_ACCOUNT_JSON", "")
