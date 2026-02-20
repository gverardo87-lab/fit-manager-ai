# Core - Business Logic Layer

Questa cartella contiene TUTTA la logica di business. ~13.500 LOC.

## Regola fondamentale

**Nessun import di Streamlit (st.\*) in questa cartella.**
Unica eccezione consentita: `ui_components.py` (bridge UI per design).
Violazioni risolte: error_handler.py, knowledge_chain.py, document_manager.py.

## Repository (core/repositories/)

~4.000 LOC, 9 repository. Tutti ereditano da BaseRepository.

### BaseRepository (base_repository.py, 230 LOC)
Metodi chiave:
- `_connect()` - context manager con PRAGMA foreign_keys = ON, auto commit/rollback
- `_row_to_dict()` - conversione row -> dict con gestione None
- `_serialize_json()` / `_deserialize_json()` - JSON encoder custom per date/datetime
- `_execute_query(sql, params, fetch_mode)` - query executor riutilizzabile ('one', 'all', 'none')
- `get_connection()` - escape hatch per query dinamiche (marcato come workaround temporaneo)

### Convenzioni repository
```python
@safe_operation(
    operation_name="Create Client",
    severity=ErrorSeverity.HIGH,
    fallback_return=None
)
def create(self, cliente: ClienteCreate) -> Optional[Cliente]:
    """Docstring."""
    with self._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ... VALUES (?)", (param,))
        return Cliente(id=cursor.lastrowid, ...)
```

- Ogni metodo pubblico: `@safe_operation` con severity appropriata
- Severity: CRITICAL (delete batch), HIGH (C/U/D), MEDIUM (read), LOW (count/metrics)
- Return type: `Optional[Model]` o `Optional[List[Model]]`
- Fallback return: `None` per singoli, `[]` per liste, `{}` per dict

### Mappa dominio -> repository

| Dominio | Repository | Tabelle |
|---------|-----------|---------|
| Clienti | ClientRepository (483 LOC, 11 metodi) | clienti, misurazioni |
| Contratti | ContractRepository (664 LOC, 13 metodi) | contratti, rate_programmate |
| Agenda | AgendaRepository (540 LOC, 16 metodi) | agenda |
| Finanza | FinancialRepository (850 LOC, 20 metodi) | movimenti_cassa, spese_ricorrenti, hourly_tracking |
| Assessment | AssessmentRepository (266 LOC, 8 metodi) | client_assessment_initial, client_assessment_followup |
| Workout | WorkoutRepository (238 LOC, 7 metodi) | workout_plans, workout_exercise_edits |
| Import | CardImportRepository (180 LOC, 6 metodi) | imported_workout_cards |
| DNA | TrainerDNARepository (257 LOC, 8 metodi) | trainer_dna_patterns |

## Models (core/models.py, 620 LOC)

Pydantic v2. Pattern: EntityCreate (input) -> Entity (completo con id).

21 modelli organizzati per dominio:
- Cliente: ClienteBase, ClienteCreate, ClienteUpdate, Cliente, CreditSummary
- Misurazione: MisurazioneBase, MisurazioneCreate, Misurazione (cross-field: massa_magra + massa_grassa <= peso + 5kg)
- Contratto: ContratoBase, ContratoCreate, Contratto, RataProgrammata (acconto <= prezzo_totale, scadenza > inizio)
- Finanza: MovimentoCassaCreate, MovimentoCassa, SpesaRicorrenteCreate, SpesaRicorrente
- Sessione: SessioneBase, SessioneCreate, Sessione, SessioneUpdate (durata max 4h, categoria normalizzata uppercase)
- Assessment: AssessmentInitialCreate, AssessmentInitial, AssessmentFollowupCreate, AssessmentFollowup
- Workout: WorkoutPlanCreate, WorkoutPlan, ProgressRecordCreate, ProgressRecord
- DNA: ImportedCardCreate, ImportedCard, TrainerDNAPatternCreate, TrainerDNASummary

## Error Handler (core/error_handler.py, ~310 LOC)

Gerarchia eccezioni:
```
FitManagerException (base)
  ├── ValidationError
  ├── ClienteNotFound
  ├── ContratoInvalido
  ├── DatabaseError
  ├── ConflictError
  └── PermissionDenied
```

Decoratori:
- `@safe_operation` - USARE SEMPRE nei repository (76 metodi decorati). Rilancia FitManagerException, cattura errori infrastruttura.
- `@safe_db_operation` - DEPRECATO (sostituito da @safe_operation)

ErrorHandler singleton: log_error(), get_error_history(), clear_history().
Zero import Streamlit. Funzioni dead code (`handle_streamlit_errors`, `safe_streamlit_dialog`, `show_error_details`) rimosse.

## Financial Analytics (core/financial_analytics.py, 698 LOC)

Eredita da BaseRepository. Metriche avanzate:
- LTV (Lifetime Value) per cliente
- CAC (Customer Acquisition Cost) - basato su categorie marketing in movimenti_cassa
- Churn Rate - retention analysis
- MRR/ARR (Monthly/Annual Recurring Revenue)
- Cohort Analysis

**NOTA**: Non completamente integrato nelle pages. Dashboard potrebbe usare LTV/CAC/MRR.

## AI / RAG Layer (~6.500 LOC)

| File | LOC | Responsabilita' |
|------|-----|-----------------|
| exercise_database.py | 2147 | 500+ esercizi, template periodizzazione, strategie progressione |
| workout_generator_v2.py | 1363 | Generazione algoritmica (5 modelli: Linear, Undulating, Block, Hybrid, DUP) |
| card_parser.py | 1087 | Parser Excel/Word, fuzzy matching esercizi, supporto italiano |
| workout_ai_pipeline.py | 957 | Orchestrazione: assessment + DNA + generazione + LLM enhancement |
| periodization_models.py | 688 | Fasi training, progressive overload (+5% pesi, +2 reps, +1 set) |
| pattern_extractor.py | 328 | Estrazione pattern con LLM, fallback algoritmico, confidence scoring |
| knowledge_chain.py | 300 | RAG teoria/anatomia, hybrid mode (built-in + user PDFs), cross-encoder re-ranking |
| methodology_chain.py | ~100 | RAG separato per metodologie trainer |

## Config (core/config.py, 73 LOC)

Centralizzato con env vars:
- PROJECT_ROOT, DATA_DIR, DB_CRM_PATH
- OLLAMA_HOST (default localhost:11434)
- MAIN_LLM_MODEL (default llama3:8b-instruct-q4_K_M)
- EMBEDDING_MODEL, CROSS_ENCODER_MODEL
- VECTORSTORE_DIR, DOCUMENTS_DIR

## Codice morto da eliminare

- `core/schedule_db.py` (92 LOC) - mai importato, gestisce schedule.db vuoto
- `core/services/dashboard_service.py` (115 LOC) - preparato ma non integrato
