# Patch Spec - License Enforcement Negative Tests v1

## Metadata

- Upgrade ID: UPG-2026-03-10-14
- Date: 2026-03-10
- Owner: Codex
- Area: Licensing + Launch Hardening + Test Reliability
- Priority: high
- Status: done

## Problem

Il gate licenza era gia presente e coperto nei casi base, ma mancava ancora una matrice negativa
esplicita sui casi che contano davvero prima del pilot:

- enforcement disattivato -> il gate non deve interferire;
- stati licenza negativi diversi (`missing`, `invalid`, `expired`, `unconfigured`);
- route esenti (`/health`, auth routes) che non devono rompersi quando la licenza e' negativa.

Senza questa copertura il licensing resta "presente" ma non abbastanza difendibile come confine
operativo del prodotto.

## Desired Outcome

- Le route protette vengono bloccate in modo coerente per tutti gli stati licenza negativi.
- Quando `LICENSE_ENFORCEMENT_ENABLED=false`, il gate viene davvero bypassato.
- `/health` resta esente dal gate ma continua a riportare lo stato licenza reale.
- Le route auth esenti restano raggiungibili anche con licensing negativo.

## Scope

- In scope:
  - hardening test su `tests/test_license_middleware.py`
  - copertura dei casi `missing/invalid/expired/unconfigured`
  - verifica dell'esenzione di `/health`
  - verifica del bypass reale con enforcement disattivato
- Out of scope:
  - refactor del middleware licenza
  - UI `/licenza`
  - rehearsal manuale su installazione reale con rimozione fisica di `license.key`

## Implementation

- `tests/test_license_middleware.py`
  - il test `enforcement disabled` ora prova che `check_license()` non venga chiamato affatto;
  - introdotto test parametrico sulle route protette per:
    - `missing`
    - `invalid`
    - `expired`
    - `unconfigured`
  - aggiunta verifica che `/health` resti accessibile e rifletta `license_status`
    anche con enforcement attivo e licenza negativa;
  - aggiunta verifica che le route auth esenti restino raggiungibili.

## Verification

- `venv\Scripts\ruff.exe check tests\test_license_middleware.py`
- `python -m pytest tests/test_license_middleware.py -q -p no:cacheprovider` -> **passed**
  (`2026-03-11`, eseguito in venv locale reale dall'utente)

## Risks / Residuals

1. Questo microstep chiude la matrice negativa lato API/test, ma non sostituisce la prova manuale
   su build/installazione reale richiesta dalla release checklist (`rimuovere license.key` e
   verificare il percorso utente fino a `/licenza`).
2. Il contratto frontend del redirect a `/licenza` resta implicitamente coperto dall'interceptor
   Axios, ma non ha ancora un test dedicato.

## Next Smallest Step

Aprire il prossimo P0 del launch plan: runbook supporto/licenza/recovery v1, includendo anche la
procedura manuale per il test negativo su istanza installata.
