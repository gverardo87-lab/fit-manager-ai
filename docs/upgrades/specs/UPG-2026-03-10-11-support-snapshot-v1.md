# Patch Spec - Support Snapshot v1

## Metadata

- Upgrade ID: UPG-2026-03-10-11
- Date: 2026-03-10
- Owner: Codex
- Area: Settings + Runtime Reliability + Supportability
- Priority: high
- Status: done

## Problem

La nuova surface `Stato installazione` rende visibile la salute runtime, ma non esiste ancora un
artefatto leggero e read-only da scaricare quando serve supporto tecnico. In questa fase pre-pilot
FitManager deve distinguersi come software locale governabile: il supporto non puo dipendere da
terminali, screenshot parziali o accesso diretto ai sorgenti.

## Desired Outcome

- Il trainer puo scaricare da `Impostazioni` uno snapshot diagnostico JSON read-only.
- Lo snapshot contiene solo metadati tecnici e operativi dell'istanza:
  - health runtime
  - versione
  - modalita `source/installer`
  - modalita `development/production`
  - stato licenza ed enforcement
  - stato portale pubblico e `PUBLIC_BASE_URL`
  - ultimi backup locali con checksum
- Nessun dato business, nessun token e nessuna PII vengono esportati.

## Scope

- In scope:
  - nuovo endpoint protetto `GET /api/system/support-snapshot`
  - schema Pydantic dedicato
  - type sync frontend
  - nuova sezione `Snapshot diagnostico` in `Impostazioni`
  - download client-side del JSON
  - test backend focused sul payload
- Out of scope:
  - logging locale
  - `middleware -> proxy`
  - backup/restore
  - export dati business

## Implementation

### Backend

- `api/services/system_runtime.py`
  - estratti helper condivisi per health/support snapshot;
  - centralizzati `APP_STARTED_AT`, rilevazione `dev/prod`, `source/installer`,
    enforcement licenza, portale pubblico e lista backup recenti.
- `api/schemas/system.py`
  - aggiunti `SupportSnapshotBackupItem` e `SupportSnapshotResponse`.
- `api/routers/system.py`
  - introdotto router protetto `/system` con endpoint read-only `support-snapshot`.
- `api/main.py`
  - `/health` continua a esistere come endpoint pubblico, ma ora riusa il service runtime;
  - registrato il nuovo router `/api/system/*`.

### Frontend

- `frontend/src/types/api.ts`
  - aggiunto mirror `InstallationSupportSnapshotResponse`.
- `frontend/src/hooks/useSystemSupport.ts`
  - nuova mutation read-only per scaricare il JSON diagnostico via `apiClient`.
- `frontend/src/components/settings/SupportSnapshotSection.tsx`
  - nuova card dedicata con CTA `Scarica diagnostica` e disclosure chiara su cosa entra
    e cosa resta intenzionalmente escluso.
- `frontend/src/app/(dashboard)/impostazioni/page.tsx`
  - inserita la nuova sezione subito dopo `Stato installazione`, mantenendo separata
    `SystemStatusSection` e senza riportarla oltre il limite LOC.

### Test

- `tests/test_health_endpoint.py`
  - riallineato al nuovo service condiviso (`api.services.system_runtime`).
- `tests/test_support_snapshot_endpoint.py`
  - nuovo test focused sul payload read-only del support snapshot, inclusi backup recenti
    e assenza di dati business.

## Verification

- `venv\Scripts\ruff.exe check api/main.py api/schemas/system.py api/services/system_runtime.py api/routers/system.py tests/test_health_endpoint.py tests/test_support_snapshot_endpoint.py`
- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/impostazioni/page.tsx" "src/components/settings/SystemStatusSection.tsx" "src/components/settings/SupportSnapshotSection.tsx" "src/hooks/useSystemSupport.ts" "src/types/api.ts"`
- `venv\Scripts\pytest.exe -q tests/test_health_endpoint.py tests/test_support_snapshot_endpoint.py -p no:cacheprovider` -> **blocked**
  dal launcher Python della venv che continua a puntare al runtime Microsoft Store.

## Risks / Residuals

1. La diagnostica e ora scaricabile, ma il prossimo collo di bottiglia resta la migrazione Next
   `middleware -> proxy`: warning noto della shell distributiva ancora aperto.
2. I test pytest focused esistono ma non sono eseguibili localmente in questo ambiente per un
   limite della venv Windows, non per un failure del codice.

## Next Smallest Step

Aprire il prossimo P0 del launch plan: migrazione Next `middleware -> proxy`, cosi la shell
frontend di distribuzione smette di portarsi dietro il warning deprecato e il boundary auth/proxy
resta pulito prima del pilot.
