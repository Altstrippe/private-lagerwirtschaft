import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

RAEUME = ["Halle", "Werkstatt", "EVA", "Honigraum"]

@st.cache_resource
def get_spreadsheet():
    """Stellt die authentifizierte Verbindung zum Google Sheet her."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet_url = st.secrets["spreadsheet_url"]
    return client.open_by_url(sheet_url)
