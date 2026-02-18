# Core - Business Logic Layer

Questa cartella contiene TUTTA la logica di business. Nessun import di Streamlit (st.*) qui.

## Repository (core/repositories/)

Ogni repository eredita da BaseRepository e gestisce un dominio:
- ClientRepository: clienti + misurazioni
- ContractRepository: contratti + rate programmate
- AgendaRepository: sessioni/eventi + consumo crediti
- FinancialRepository: movimenti cassa + spese ricorrenti

Ogni metodo pubblico deve avere @safe_operation con operation_name e severity.

## Models (core/models.py)

Pydantic v2. Pattern: EntityCreate (input) + Entity (completo con id).
Usare field_validator per logica custom (email, telefono, date).
Modelli coprono: clienti, contratti, rate, eventi, movimenti cassa, spese ricorrenti, assessment, workout, progress.

## Financial Analytics (core/financial_analytics.py)

Metriche avanzate (LTV, CAC, Churn, MRR, Cohort).
Eredita da BaseRepository per accesso diretto al DB.

## Error Handler (core/error_handler.py)

Decoratori disponibili:
- @safe_operation(operation_name, severity, fallback_return) - USARE SEMPRE nei repository
- @handle_streamlit_errors - disponibile ma non ancora adottato nelle pages
