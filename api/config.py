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
#
# Auto-detect dev/prod: se --port 8001 (o DATABASE_URL non settato su porta dev)
# usa crm_dev.db automaticamente. Zero rischio di toccare dati prod per sbaglio.
def _resolve_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    # Auto-detect da porta uvicorn: --port 8001 = dev
    import sys
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port") + 1
            if port_idx < len(sys.argv) and sys.argv[port_idx] == "8001":
                return f"sqlite:///{DATA_DIR / 'crm_dev.db'}"
        except (ValueError, IndexError):
            pass
    return f"sqlite:///{DATA_DIR / 'crm.db'}"

DATABASE_URL: str = _resolve_database_url()

# JWT Authentication
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    import logging
    logging.getLogger("fitmanager.config").warning(
        "JWT_SECRET non configurato — uso default di sviluppo. "
        "NON usare in produzione!"
    )
    JWT_SECRET = "dev-secret-change-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 ore

# API
API_PREFIX: str = "/api"
API_VERSION: str = "v1"
