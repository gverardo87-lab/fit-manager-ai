# FitManager AI Studio

CRM gestionale per personal trainer e liberi professionisti del fitness.
Stack: Python 3.9+ / Streamlit / SQLite / Ollama (LLM locale) / LangChain + ChromaDB (RAG).

L'utente NON e' un programmatore esperto. Sta imparando il coding con l'aiuto dell'AI.
Questo significa:
- Spiega brevemente il "perche'" delle scelte tecniche quando rilevante
- Non dare per scontata la conoscenza di pattern o concetti avanzati
- Proponi soluzioni ambiziose ma implementale tu in modo completo, non lasciare "esercizi al lettore"
- Se qualcosa puo' rompersi, previenilo nel codice invece di documentarlo e basta
- Quando crei codice, assicurati che funzioni end-to-end: modello, repository, UI

## Architettura

```
server/pages/*.py  (UI Streamlit - solo presentazione)
       |
core/repositories/  (CRUD, validazione, accesso DB)
       |
core/models.py  (Pydantic v2 - validazione input)
       |
SQLite  (data/crm.db)
```

Pattern attivo: Repository Pattern (completo).
6 repository: ClientRepository, ContractRepository, AgendaRepository, FinancialRepository, AssessmentRepository, WorkoutRepository.
Tutti ereditano da BaseRepository (core/repositories/base_repository.py).

FinancialAnalytics (core/financial_analytics.py) eredita da BaseRepository per metriche avanzate (LTV, CAC, Churn, MRR, Cohort).

## Stato migrazione pagine

| Pagina | Repository | Note |
|--------|-----------|------|
| 01_Agenda | SI | ClientRepo + AgendaRepo |
| 02_Assistente_Esperto | SI | |
| 03_Clienti | SI | ClientRepo + ContractRepo + AgendaRepo |
| 04_Cassa | SI | FinancialRepo |
| 05_Analisi_Margine | SI | FinancialRepo |
| 06_Assessment | SI | AssessmentRepo + ClientRepo |
| 07_Programma_Allenamento | SI | WorkoutRepo + ClientRepo |
| 08_Document_Explorer | SI | RAG, poco DB |

## Come aggiungere una feature

1. Modello Pydantic in core/models.py (Create + entita' completa)
2. Metodo nel repository appropriato con @safe_operation
3. UI in server/pages/ che importa solo dal repository
4. Mai importare sqlite3 nelle pages. Mai mettere st.* nel core.

## Regole DB

- Sempre query parametrizzate: `cursor.execute("... WHERE id = ?", (id,))`
- Sempre context manager: `with self._connect() as conn:`
- Foreign keys attive (PRAGMA foreign_keys = ON)
- I repository restituiscono oggetti Pydantic, non dict raw

## Problemi noti (debito tecnico)

- Logica crediti/lezioni_residue: non gestisce contratti multipli attivi (LIMIT 1)
- Consumo crediti: avviene alla conferma evento, non alla creazione - ma non tutto il codice e' allineato
- @safe_operation usato nei repository ma le pages non gestiscono il caso fallback (return None silenzioso)
- core/services/dashboard_service.py esiste ma non e' usato da nessuna page

## Convenzioni

- UI in italiano, codice e commenti in inglese o italiano
- Testo UI: usare emoji nei titoli pagina (st.title), non nel codice
- Validazione: sempre Pydantic prima di toccare il DB
- Error handling: @safe_operation decorator (core/error_handler.py)
- Config centralizzata in core/config.py (paths, modelli AI, env vars)

## AI / RAG

- LLM locale via Ollama (default: llama3:8b-instruct-q4_K_M)
- Embedding: nomic-embed-text
- Vector store: ChromaDB in knowledge_base/vectorstore/
- Il RAG funziona anche senza documenti utente (fallback su exercise_database.py con 200+ esercizi)
- Mai inviare PII (nomi, email, dati salute) nei prompt LLM

## Comandi utili

```bash
# Avvia app
streamlit run server/app.py

# Controlla Ollama
ollama list

# Ispeziona DB
sqlite3 data/crm.db ".tables"
sqlite3 data/crm.db ".schema clienti"
```

## Direzione di sviluppo

Il progetto ha completato il consolidamento architetturale (Repository Pattern).
CrmDBManager e' stato eliminato. Tutte le pagine usano i repository.

Prossimi passi naturali:
- Rendere il service layer operativo (dashboard_service.py)
- Strutturare test con pytest
- Risolvere la logica crediti in modo univoco
- Aggiungere nuove feature (dashboard, report, notifiche)

Non ci sono limiti allo sviluppo. Nuove feature, integrazioni, refactoring ambiziosi sono tutti benvenuti.
