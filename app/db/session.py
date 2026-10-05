from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Neon PostgreSQL Engine mit strikten Timeouts & Verbindungspooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # Prüft vor jeder Abfrage, ob die Verbindung noch lebt
    pool_recycle=300,        # Erneuert Verbindungen nach 5 Min. (verhindert Neon-Standby-Abbrüche)
    future=True,
    connect_args={
        "connect_timeout": 10,  # Bricht nach 10 s ab, statt den Worker endlos zu blockieren
        "sslmode": "require",   # Erzwingt die für Neon erforderliche SSL-Verschlüsselung
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
