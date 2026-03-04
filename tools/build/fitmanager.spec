# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec per FitManager AI Studio — Backend API.

Produce: dist/fitmanager/ (directory mode, avvio rapido)
Entry:   tools/build/entry_point.py → uvicorn api.main:app

Uso:
    pyinstaller tools/build/fitmanager.spec

Output:
    dist/fitmanager/fitmanager.exe
"""

import os
from pathlib import Path

block_cipher = None

# Root del progetto (2 livelli sopra questo file spec)
ROOT = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(ROOT / 'tools' / 'build' / 'entry_point.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Alembic migrations (upgrade DB automatico)
        (str(ROOT / 'alembic'), 'alembic'),
        (str(ROOT / 'alembic.ini'), '.'),
        # Seed esercizi (caricato al primo avvio)
        (str(ROOT / 'data' / 'exercises' / 'seed_exercises.json'), 'data/exercises'),
    ],
    hiddenimports=[
        # ── SQLModel / SQLAlchemy ──
        'sqlmodel',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'sqlalchemy.ext.asyncio',

        # ── FastAPI / Starlette ──
        'fastapi',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.staticfiles',
        'starlette.responses',

        # ── Pydantic v2 ──
        'pydantic',
        'pydantic.json_schema',
        'pydantic_core',
        # 'pydantic_settings',  # non usato direttamente

        # ── Auth ──
        'jose',
        'jose.backends',
        'jose.backends.cryptography_backend',
        'bcrypt',
        'cryptography',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'cryptography.hazmat.primitives.asymmetric.padding',
        'cryptography.hazmat.primitives.hashes',

        # ── Upload / Multipart ──
        'multipart',
        'python_multipart',

        # ── Validation ──
        'email_validator',

        # ── Alembic ──
        'alembic',
        'alembic.migration',
        'alembic.operations',
        'alembic.script',

        # ── Data / Export ──
        'openpyxl',
        'openpyxl.styles',

        # ── Uvicorn ──
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',

        # ── API modules (router discovery) ──
        'api',
        'api.main',
        'api.config',
        'api.database',
        'api.auth',
        'api.auth.router',
        # 'api.auth.security',  # non esiste come modulo separato
        'api.models',
        'api.schemas',
        'api.routers',
        'api.services',
        'api.seed_exercises',

        # ── Misc ──
        'dotenv',
        'difflib',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ── AI libs (core/ only, ~1.8 GB risparmiati) ──
        'torch',
        'torchvision',
        'torchaudio',
        'transformers',
        'sentence_transformers',
        'chromadb',
        'langchain',
        'langchain_community',
        'langchain_core',
        'langchain_chroma',
        'langchain_ollama',
        'langchain_text_splitters',
        'scikit-learn',
        'sklearn',
        'joblib',
        'ollama',

        # ── GUI / Viz non necessari ──
        'streamlit',
        'plotly',
        'matplotlib',
        'PIL',
        'tkinter',

        # ── Dev tools ──
        'pytest',
        'IPython',
        'notebook',
        'jupyterlab',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Directory mode (non onefile) — avvio piu' rapido, ~50MB
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fitmanager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='fitmanager',
)
