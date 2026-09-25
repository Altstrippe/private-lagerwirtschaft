import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from pydantic_settings import BaseSettings

RAEUME = ["Halle", "Werkstatt", "EVA", "Honigraum"]

class Settings(BaseSettings):
    app_name: str = "Lagerverwaltung"
    app_env: str = "production"

    class Config:
        extra = "ignore"

@st.cache_resource
def get_settings() -> Settings:
    return Settings()

@st.cache_resource
def get_spreadsheet():
    """Stellt die Verbindung her oder bricht mit klarer Meldung im UI ab."""
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ Secret '[gcp_service_account]' wurde in den App-Settings nicht gefunden.")
        st.info("Bitte trage die Google-Zertifikatsdaten in den Streamlit Cloud Secrets ein.")
        st.stop()

    if "spreadsheet_url" not in st.secrets:
        st.error("⚠️ Secret 'spreadsheet_url' fehlt in den App-Settings.")
        st.stop()

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["spreadsheet_url"])
