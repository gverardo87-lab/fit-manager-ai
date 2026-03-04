# api/config.py
"""
Configurazione API — tutti i valori sensibili da variabili d'ambiente.

Per sviluppo locale basta il .env. In produzione, usa secrets management.
DATABASE_URL e' l'unica riga da cambiare per passare a PostgreSQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Paths (prima di load_dotenv per poter caricare data/.env)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Carica .env dal progetto (sviluppo) + data/.env (produzione/bootstrap)
load_dotenv()  # .env nella root del progetto
load_dotenv(DATA_DIR / ".env", override=False)  # data/.env come fallback

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
    # Auto-detect da porta uvicorn: --port 8001 o --port=8001 = dev
    import sys
    for arg in sys.argv:
        # Forma: --port 8001
        if arg == "--port":
            try:
                port_idx = sys.argv.index("--port") + 1
                if port_idx < len(sys.argv) and sys.argv[port_idx] == "8001":
                    return f"sqlite:///{DATA_DIR / 'crm_dev.db'}"
            except (ValueError, IndexError):
                pass
            break
        # Forma: --port=8001
        if arg.startswith("--port="):
            if arg.split("=", 1)[1] == "8001":
                return f"sqlite:///{DATA_DIR / 'crm_dev.db'}"
            break
    return f"sqlite:///{DATA_DIR / 'crm.db'}"

DATABASE_URL: str = _resolve_database_url()

# Catalog Database — tassonomia scientifica (muscoli, articolazioni, condizioni, metriche)
# Shared tra prod e dev (stessi dati di riferimento), sempre in data/catalog.db.
# Se CATALOG_DATABASE_URL e' settato esplicitamente, ha priorita'.
CATALOG_DATABASE_URL: str = os.getenv(
    "CATALOG_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'catalog.db'}",
)

# JWT Authentication — bootstrap automatico al primo avvio
def _resolve_jwt_secret() -> str:
    """Risolve JWT_SECRET: env > data/.env > auto-genera e persiste."""
    import logging
    import secrets
    _logger = logging.getLogger("fitmanager.config")

    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return secret

    # Auto-genera e persiste in data/.env
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    env_file = DATA_DIR / ".env"
    secret = secrets.token_hex(32)

    # Appendi senza sovrascrivere altre variabili gia' presenti
    with open(env_file, "a", encoding="utf-8") as f:
        f.write(f"\nJWT_SECRET={secret}\n")

    _logger.info(
        "JWT_SECRET generato automaticamente e salvato in %s", env_file
    )
    return secret


JWT_SECRET: str = _resolve_jwt_secret()
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 ore

# API
API_PREFIX: str = "/api"
API_VERSION: str = "v1"
