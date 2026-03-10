# Patch Spec - Local Logging Runtime v1

## Metadata

- Upgrade ID: UPG-2026-03-10-13
- Date: 2026-03-10
- Owner: Codex
- Area: Backend Runtime + Supportability
- Priority: high
- Status: done

## Problem

FitManager aveva gia health surface e support snapshot, ma mancava ancora il livello minimo di
supportabilita operativa per un software locale vendibile: log applicativi persistenti in
`data/logs/`, con rotazione, policy esplicita e bootstrap runtime coerente.

Senza questo livello il supporto resta troppo dipendente dal terminale o da riproduzioni manuali.
Per un prodotto che vuole distinguersi dal cloud sulla affidabilita locale, il logging governato e'
parte della base, non un extra.

## Desired Outcome

- L'app scrive log applicativi locali in `data/logs/fitmanager.log`.
- I log ruotano automaticamente con policy configurabile via env.
- Il bootstrap e idempotente: nessun handler duplicato su reload/import multipli.
- I messaggi standard introdotti dal microstep non includono PII o token.
- La policy di logging e leggibile gia dai log di startup.

## Scope

- In scope:
  - modulo dedicato di bootstrap logging
  - configurazione runtime via env in `api/config.py`
  - aggancio a `api/main.py`
  - test focused sulla configurazione logging
  - sync documentale launch plan
- Out of scope:
  - UI impostazioni
  - export/download dei log
  - logging access HTTP dettagliato
  - sanitizzazione retroattiva di tutti i logger dominio gia esistenti

## Implementation

### Backend

- `api/logging_config.py`
  - nuovo modulo con `configure_app_logging()`, `get_log_dir()` e `get_log_path()`;
  - usa `RotatingFileHandler`;
  - aggiunge il file handler al root logger;
  - aggiunge il file handler anche a `uvicorn.error` solo se non propaga al root;
  - evita duplicazioni di handler sullo stesso file.
- `api/config.py`
  - introdotti:
    - `LOG_DIR`
    - `APP_LOG_LEVEL`
    - `APP_LOG_MAX_BYTES`
    - `APP_LOG_BACKUP_COUNT`
- `api/main.py`
  - bootstrap del logging prima dell'uso del logger applicativo;
  - startup log con file path e policy runtime (`level`, `max_bytes`, `backup_count`).

### Test

- `tests/test_logging_config.py`
  - verifica path canonico `tmp_path/logs/fitmanager.log`;
  - verifica idempotenza (nessun doppio handler sullo stesso file);
  - verifica scrittura reale su file.

## Verification

- `venv\Scripts\ruff.exe check api\config.py api\main.py api\logging_config.py tests\test_logging_config.py`
- `venv\Scripts\pytest.exe -q tests\test_logging_config.py -p no:cacheprovider` -> **blocked**
  dal launcher Python locale della venv che continua a puntare al runtime Microsoft Store.

## Risks / Residuals

1. Il microstep introduce il bootstrap e la persistenza file, ma non cambia ancora la policy
   di contenuto dei logger dominio gia esistenti. Alcuni log storici continuano a includere ID
   tecnici trainer/client senza token o dati business estesi.
2. La UI non mostra ancora metadata dei log. Se serve support snapshot piu ricco, il prossimo pass
   dovra aggiungere solo metadati dei file, non il contenuto.

## Next Smallest Step

Aprire il P0 successivo del piano di lancio: test negativo dell'enforcement licenza, per verificare
in modo esplicito che una build/source instance senza gate attivo o con licenza invalida reagisca
come previsto prima del pilot.
