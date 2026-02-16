# core/config.py
"""
Configurazione centralizzata per FitManager AI Studio

Gestisce:
- Path del progetto (root, data, knowledge base)
- Database (CRM, Schedule, Workout)
- Modelli AI (Ollama LLM, Embeddings)
- Knowledge Base (RAG system)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente da .env (se presente)
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# 1. PERCORSI FONDAMENTALI
# ═══════════════════════════════════════════════════════════════════════════

# Root del progetto (contiene core/, server/, data/, etc.)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directory per dati persistenti (database SQLite)
DATA_DIR = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# 2. CONFIGURAZIONE DATABASE (SQLite)
# ═══════════════════════════════════════════════════════════════════════════

# Database CRM: clienti, misurazioni, contratti, transazioni
DB_CRM_PATH = DATA_DIR / "crm.db"

# Database Schedule: agenda, turni, appuntamenti
DB_SCHEDULE_PATH = DATA_DIR / "schedule.db"


# ═══════════════════════════════════════════════════════════════════════════
# 3. KNOWLEDGE BASE & RAG SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

# Directory principale knowledge base
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

# Documents: PDF, TXT, DOCX (metodologie allenamento, anatomia, nutrizione)
DOCUMENTS_DIR = KNOWLEDGE_BASE_DIR / "documents"

# Vector Store: ChromaDB embeddings persistenti
VECTORSTORE_DIR = KNOWLEDGE_BASE_DIR / "vectorstore"


# ═══════════════════════════════════════════════════════════════════════════
# 4. MODELLI AI (Ollama)
# ═══════════════════════════════════════════════════════════════════════════

# Ollama server address (local by default)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Main LLM: workout generation, client assessment, chat
MAIN_LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")

# Embedding model: document vectorization (RAG)
EMBEDDING_MODEL = "nomic-embed-text"

# Cross-Encoder: re-ranking for RAG precision
CROSS_ENCODER_MODEL = 'cross-encoder/ms-marco-MiniLM-L-6-v2'