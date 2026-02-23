#!/usr/bin/env python3
"""
Seed Dev — Popola crm_dev.db con dati di test realistici.

Setta DATABASE_URL a crm_dev.db PRIMA di importare i moduli,
cosi' il seed NON tocca mai crm.db (dati reali di Chiara).

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
from tools.admin_scripts.seed_realistic import reset_database_safe, seed_realistic  # noqa: E402

print("[1/2] Reset database dev...")
engine = reset_database_safe()
print()

print("[2/2] Seed dati realistici...")
seed_realistic(engine)
print()

print("=== DEV DB PRONTO ===")
print("Avvia con: DATABASE_URL=sqlite:///data/crm_dev.db uvicorn api.main:app --reload --port 8001")
