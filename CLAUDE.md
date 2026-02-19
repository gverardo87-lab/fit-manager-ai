# FitManager AI Studio

CRM gestionale per personal trainer e liberi professionisti del fitness.
Stack: Python 3.9+ / Streamlit / SQLite / Ollama (LLM locale) / LangChain + ChromaDB (RAG).
Privacy-first: tutto gira in locale, zero cloud, zero dati verso terzi.

L'utente NON e' un programmatore esperto. Sta imparando il coding con l'aiuto dell'AI.
Questo significa:
- Spiega brevemente il "perche'" delle scelte tecniche quando rilevante
- Non dare per scontata la conoscenza di pattern o concetti avanzati
- Proponi soluzioni ambiziose ma implementale tu in modo completo, non lasciare "esercizi al lettore"
- Se qualcosa puo' rompersi, previenilo nel codice invece di documentarlo e basta
- Quando crei codice, assicurati che funzioni end-to-end: modello, repository, UI

## Architettura

```
server/pages/*.py       (UI Streamlit - SOLO presentazione)
       |
core/ui_components.py   (componenti UI riusabili - badge, card, conferme)
       |
core/repositories/      (CRUD, validazione, accesso DB)
       |
core/models.py          (Pydantic v2 - validazione input)
       |
SQLite                  (data/crm.db - 16 tabelle attive)
```

Pattern: Repository Pattern (completo, tutte le 8 pagine migrate).
9 repository + 1 analytics class, tutti ereditano da BaseRepository.

### Repository

| Repository | Dominio | Metodi | Tabelle |
|------------|---------|--------|---------|
| ClientRepository | Clienti + misurazioni | 11 | clienti, misurazioni |
| ContractRepository | Contratti + rate pagamento | 13 | contratti, rate_programmate |
| AgendaRepository | Sessioni/eventi + crediti | 16 | agenda |
| FinancialRepository | Cassa + spese ricorrenti | 20 | movimenti_cassa, spese_ricorrenti, hourly_tracking |
| AssessmentRepository | Assessment iniziale + followup | 8 | client_assessment_initial, client_assessment_followup |
| WorkoutRepository | Programmi + progressi | 7 | workout_plans, workout_exercise_edits |
| CardImportRepository | Schede importate | 6 | imported_workout_cards |
| TrainerDNARepository | Pattern metodologici | 8 | trainer_dna_patterns |
| FinancialAnalytics | Metriche avanzate (LTV, CAC, Churn, MRR) | ~15 | Legge da contratti, movimenti |

### Trainer DNA System (AI-Augmented Programming)

```
Schede Excel/Word --> CardParser --> CardImportRepo (DB)
                                          |
                                    PatternExtractor (LLM) --> TrainerDNARepo (DB)
                                                                     |
                                                               MethodologyChain (ChromaDB)
                                                                     |
Assessment + DNA + WorkoutGeneratorV2 --> WorkoutAIPipeline --> Programma AI-Enhanced
```

Componenti:
- core/card_parser.py (1087 LOC): parser Excel/Word con fuzzy matching esercizi
- core/pattern_extractor.py (328 LOC): estrae pattern con LLM (fallback algoritmico)
- core/methodology_chain.py: RAG per metodologie (ChromaDB in knowledge_base/methodology_vectorstore/)
- core/workout_ai_pipeline.py (957 LOC): pipeline completa assessment + DNA + AI
- core/workout_generator_v2.py (1363 LOC): generazione algoritmica (5 modelli periodizzazione)
- core/exercise_database.py (2147 LOC): 500+ esercizi + template periodizzazione
- core/db_migrations.py: migrazioni idempotenti per tabelle DNA

## Regole fondamentali

### Separazione UI / Core (CRITICA)
- Mai importare `sqlite3` nelle pages
- Mai mettere `st.*` nel core (NOTA: error_handler.py e document_manager.py violano questa regola - debito tecnico da risolvere)
- Le pages importano SOLO da core/repositories/, core/models.py, core/ui_components.py
- I repository restituiscono oggetti Pydantic, mai dict raw

### DB
- Sempre query parametrizzate: `cursor.execute("... WHERE id = ?", (id,))`
- Sempre context manager: `with self._connect() as conn:`
- Foreign keys attive (PRAGMA foreign_keys = ON in BaseRepository)
- Ogni metodo pubblico del repository: `@safe_operation(operation_name, severity, fallback_return)`

### Validazione
- Sempre Pydantic prima di toccare il DB
- Pattern modelli: EntityCreate (input) + Entity (completo con id)
- Cross-field validation con `@field_validator` e `info.data`

### Azioni distruttive
- Ogni delete/cancel nell'UI DEVE avere conferma esplicita
- Azioni CRITICHE (delete contract CASCADE): checkbox + bottone disabilitato
- Azioni MEDIE (cancel event, delete rate): warning + 2 bottoni (Conferma/Annulla)
- Componenti riutilizzabili: `render_confirm_delete()`, `render_confirm_action()` in ui_components.py

## Come aggiungere una feature

1. Modello Pydantic in core/models.py (Create + entita' completa)
2. Metodo nel repository appropriato con @safe_operation
3. UI in server/pages/ che importa solo dal repository
4. Usare componenti da core/ui_components.py per elementi comuni
5. Gestire il caso `None` dal repository (fallback di @safe_operation)

## Sistema Crediti

Formula a 3 livelli (CreditSummary model, calcolato su contratti non chiusi):
- crediti_totali = SUM(crediti_totali) da contratti con chiuso=0
- crediti_completati = SUM(crediti_usati) da contratti con chiuso=0
- crediti_prenotati = COUNT(agenda) con stato='Programmato' e contratto attivo
- crediti_disponibili = totali - completati - prenotati

Selezione contratto FIFO: il piu' vecchio con disponibilita' viene usato per primo.
Macchina a stati eventi: Programmato -> Completato | Cancellato | Rinviato.
lezioni_residue sul modello Cliente e' backward compat (= crediti_disponibili).

**Problema noto**: logica crediti distribuita in 3 file (ClientRepository.get_by_id, AgendaRepository.get_credit_summary, AgendaRepository.create_event). Da unificare in un CreditService.

## Error Handling

Gerarchia eccezioni custom: FitManagerException -> ValidationError, ClienteNotFound, ContratoInvalido, DatabaseError, ConflictError, PermissionDenied.

Decoratori:
- `@safe_operation(operation_name, severity, fallback_return)` - USARE SEMPRE nei repository (76 metodi decorati)
- `@handle_streamlit_errors(page_name)` - disponibile ma NON ancora adottato nelle pages
- Severity: LOW, MEDIUM, HIGH, CRITICAL

**Problema noto**: le pages non gestiscono sempre il caso `fallback_return=None`. Aggiungere check espliciti.

## AI / RAG

- LLM locale via Ollama (default: llama3:8b-instruct-q4_K_M)
- Embedding: nomic-embed-text
- Cross-encoder: ms-marco-MiniLM-L-6-v2 (re-ranking)
- Dual RAG architecture:
  - knowledge_base/vectorstore/ -> teoria, anatomia, nutrizione (Assistente Esperto)
  - knowledge_base/methodology_vectorstore/ -> pattern metodologici trainer (WorkoutAIPipeline)
- Fallback: se KB vuota, usa exercise_database.py (500+ esercizi built-in)
- Mai inviare PII (nomi, email, dati salute) nei prompt LLM
- Trainer DNA confidence: min(0.95, 0.3 + evidence_count * 0.15)

## Debito tecnico (stato attuale)

### Da risolvere (alta priorita')
- `core/error_handler.py` importa `streamlit` (st.error, st.write) - viola regola "no st.* nel core"
- Pages non gestiscono il `None` restituito da @safe_operation (crash silenzioso possibile)
- Logica crediti distribuita in 3 file senza source of truth unica
- `core/knowledge_chain.py` usa `print()` invece di `logger` (10 istanze)

### Codice morto / inutilizzato
- `core/schedule_db.py` (92 LOC) - mai importato da nessuno, da eliminare
- `core/services/dashboard_service.py` (115 LOC) - esiste ma non usato da app.py
- Tabella `slot_disponibili` - creata ma mai letta/scritta
- `@handle_streamlit_errors` - definito ma non adottato in nessuna page
- `data/schedule.db`, `data/fit_manager.db`, `data/fit_manager_ai.db` - DB vuoti legacy

### Da migliorare (media priorita')
- Nessuna infrastruttura pytest (7 test file esistono ma senza conftest/runner)
- Nessun CI/CD (no GitHub Actions)
- `knowledge_base/methodology_vectorstore/` non in .gitignore (dati generati)
- Paginazione mancante su get_all_active() (problema con 10k+ clienti)
- 04_Cassa.py ha 1117 LOC - candidato per split in sotto-componenti

## Comandi utili

```bash
# Avvia app
streamlit run server/app.py

# Controlla Ollama
ollama list

# Ispeziona DB
sqlite3 data/crm.db ".tables"
sqlite3 data/crm.db ".schema clienti"

# Run tests (quando configurato)
pytest tests/ -v
```

## Metriche progetto

- ~18.400 LOC di codice produzione (core + server)
- 16 tabelle DB attive, FK enforced
- 9 repository con 86 metodi totali (76 decorati con @safe_operation)
- 21 modelli Pydantic con cross-field validation
- 8 pagine Streamlit + dashboard, tutte su Repository Pattern
- 7 file test (copertura stimata 10-15%, da strutturare)
- 0 dipendenze cloud, 0 dati verso terzi

## Direzione di sviluppo

Il progetto ha completato:
- Repository Pattern (tutte le 8 pagine migrate, CrmDBManager eliminato)
- Sistema Trainer DNA (import schede, estrazione pattern, dual RAG, pipeline AI)
- Conferme su azioni distruttive (7 azioni protette)

Prossimi passi:
- Consistenza UI: unificare componenti (st.metric vs HTML custom KPI), palette colori
- Responsivita' mobile: media queries CSS, layout adattivo
- Notifiche proattive: alert crediti, rate scadute, contratti in scadenza
- Service layer: CreditService, integrare dashboard_service.py
- Test infrastructure: pytest + conftest + coverage
- Pulizia debito tecnico: rimuovere st.* da core, eliminare codice morto

Non ci sono limiti allo sviluppo. Nuove feature, integrazioni, refactoring ambiziosi sono tutti benvenuti.
