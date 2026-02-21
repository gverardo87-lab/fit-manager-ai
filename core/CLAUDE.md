# Core — AI & Business Logic Layer

Moduli AI e workout in attesa di essere esposti via API endpoints.
I repository sono legacy (sqlite3 raw) — il backend API usa SQLModel ORM.

## Stato attuale

I moduli AI **funzionano** ma non hanno ancora endpoint API.
Saranno wrappati da `api/routers/` nella prossima fase di sviluppo.
NON modificare i repository legacy — il nuovo codice va in `api/`.

## Moduli AI (attivi, da esporre via API)

| Modulo | LOC | Funzione |
|--------|-----|----------|
| exercise_archive.py | 1,132 | Database 174+ esercizi, scoring, fuzzy match |
| workout_generator.py | 458 | Generazione programmi (3 modi: archive, dna, combined) |
| session_template.py | 341 | Struttura sessione (slot-based, max 8 esercizi) |
| periodization_models.py | 688 | 5 strategie periodizzazione (Linear, UL, PPL, Deload, Block) |
| card_parser.py | 1,092 | Parser Excel/Word → schede strutturate |
| pattern_extractor.py | 328 | LLM pattern extraction (Trainer DNA) |
| workout_ai_pipeline.py | 383 | Pipeline completa: assessment → DNA → generazione → LLM |
| knowledge_chain.py | 302 | Hybrid RAG (teoria + anatomia + fallback ExerciseArchive) |
| methodology_chain.py | 171 | RAG separato per pattern metodologici |
| document_manager.py | 82 | Scanner documenti knowledge_base/ |

## Fondamenta (usate da tutti i moduli)

| File | LOC | Funzione |
|------|-----|----------|
| config.py | 72 | Path, DB, modelli LLM, embedding model |
| constants.py | 79 | Enum (EventStatus, RateStatus, MovementType) |
| error_handler.py | 284 | Logger, @safe_operation, eccezioni custom |

## Repository (legacy — usati da moduli AI, NON dal backend API)

9 repository + BaseRepository + FinancialAnalytics.
Usano sqlite3 raw + Pydantic v2. Il backend API usa SQLModel ORM.
**Non creare nuovi metodi qui** — il nuovo codice va in `api/routers/`.

## Regole

- **Zero import streamlit** in tutta la cartella
- **Zero import da api/** — i due layer sono indipendenti
- Logger da error_handler.py, mai print()
- Config centralizzata in config.py, mai path hardcoded
