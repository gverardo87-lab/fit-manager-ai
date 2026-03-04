#!/usr/bin/env python3
"""
Seed Dev — Popola crm_dev.db con dati di test realistici (4 mesi, 30 clienti).

Setta DATABASE_URL a crm_dev.db PRIMA di importare i moduli,
cosi' il seed NON tocca mai crm.db (dati reali di Chiara).

Delega a seed_dev_complete.py: 30 clienti con contratti, rate, anamnesi,
misurazioni, obiettivi, schede allenamento, eventi e log.

Uso: python -m tools.admin_scripts.seed_dev
"""

import os
import sys
from pathlib import Path

# ── Forza DATABASE_URL su crm_dev.db PRIMA di qualsiasi import ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
os.environ["DATABASE_URL"] = f"sqlite:///{DATA_DIR / 'crm_dev.db'}"

print(f"\n=== SEED DEV MODE ===")
print(f"Database target: data/crm_dev.db")
print(f"crm.db (produzione) NON viene toccato.\n")

# ── Import e esecuzione ──
sys.path.insert(0, str(PROJECT_ROOT))
from tools.admin_scripts.seed_dev_complete import (  # noqa: E402
    reset_database,
    _copy_exercises_from_prod,
    seed_complete,
)

engine = reset_database()
_copy_exercises_from_prod()  # Copia esercizi PRIMA di aprire session SQLAlchemy
seed_complete(engine)
