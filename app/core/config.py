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
    # Zuerst in Streamlit Secrets suchen, sonst Environment / .env nutzen
    db_url = st.secrets.get("DATABASE_URL", "")
    if not db_url:
        import os
        db_url = os.getenv("DATABASE_URL", "")
        
    return Settings(database_url=db_url)
