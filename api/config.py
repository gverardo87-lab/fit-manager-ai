# api/config.py
"""
Configurazione API — tutti i valori sensibili da variabili d'ambiente.

Per sviluppo locale basta il .env. In produzione, usa secrets management.
DATABASE_URL e' l'unica riga da cambiare per passare a PostgreSQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Database — Phase 1: SQLite. Phase 2: cambia solo questa riga.
# SQLite:     "sqlite:///data/crm.db"
# PostgreSQL: "postgresql://user:pass@localhost:5432/fitmanager"
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'crm.db'}"
)

# JWT Authentication
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 ore

# API
API_PREFIX: str = "/api"
API_VERSION: str = "v1"
