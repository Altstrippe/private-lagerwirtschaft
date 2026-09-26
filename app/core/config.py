import os
import streamlit as st
from pydantic_settings import BaseSettings

RAEUME = ["Halle", "Werkstatt", "EVA", "Honigraum"]

class Settings(BaseSettings):
    app_name: str = "Lagerverwaltung Suhring"
    app_env: str = "production"
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

@st.cache_resource
def get_settings() -> Settings:
    # 1. Aus Streamlit Secrets prüfen (Groß- und Kleinschreibung abfangen)
    db_url = ""
    if "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
    elif "database_url" in st.secrets:
        db_url = st.secrets["database_url"]

    # 2. Fallback auf lokale Umgebungsvariablen (.env)
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "")

    # 3. Saubere UI-Meldung statt internem SQLAlchemy-Crash, falls URL fehlt
    if not db_url or not db_url.strip():
        st.error("⚠️ Keine Datenbankverbindung gefunden: 'DATABASE_URL' fehlt in den Secrets.")
        st.info("Trage deinen Neon-Verbindungsstring in den Streamlit Cloud Secrets unter 'DATABASE_URL' ein.")
        st.stop()

    # 4. Dialekt korrigieren: postgres:// -> postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return Settings(database_url=db_url)
