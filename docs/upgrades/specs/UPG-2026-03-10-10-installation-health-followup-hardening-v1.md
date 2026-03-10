# Patch Spec - Installation Health Follow-up Hardening v1

## Metadata

- Upgrade ID: UPG-2026-03-10-10
- Date: 2026-03-10
- Owner: Codex
- Area: Settings UX + Runtime Reliability + Testability
- Priority: medium
- Status: done

## Problem

La prima versione della surface `Stato installazione` era utile ma aveva tre punti da chiudere subito:

1. gerarchia visiva invertita in `Impostazioni` (`SystemStatusSection` sopra l'header pagina);
2. bottone `Riprova` nello stato errore non sincronizzato con il fetch in corso;
3. nessun test backend dedicato al payload `/health` arricchito.

Non erano bug bloccanti, ma lasciarli aperti avrebbe indebolito la credibilita della nuova base
di affidabilita installativa.

## Desired Outcome

- `Impostazioni` torna ad avere una gerarchia chiara: header pagina prima, stato installazione subito dopo.
- Il retry dello stato installazione non e piu ambiguo durante il refetch.
- Il contratto `/health` ha almeno un test backend focused che copre i nuovi campi runtime.

## Scope

- In scope:
  - riordino visuale della pagina `Impostazioni`
  - hardening dello stato errore di `SystemStatusSection`
  - nuovo test backend sul payload `/health`
- Out of scope:
  - `support snapshot`
  - logging locale
  - migrazione `middleware -> proxy`
  - nuove card o nuove capability in `Impostazioni`

## Implementation

### Frontend

- `frontend/src/app/(dashboard)/impostazioni/page.tsx`
  - rimossa la gerarchia invertita;
  - `SystemStatusSection` ora segue l'header di pagina.
- `frontend/src/components/settings/SystemStatusSection.tsx`
  - `ErrorState` riceve `isRetrying`;
  - il bottone `Riprova` si disabilita durante il fetch;
  - spinner coerente con lo stato di retry.

### Backend / Tests

- `tests/test_health_endpoint.py`
  - aggiunto test focused sul payload `/health`;
  - coperti i campi runtime introdotti da `UPG-2026-03-10-08`:
    `license_enforcement_enabled`, `app_mode`, `distribution_mode`,
    `public_portal_enabled`, `public_base_url_configured`, `started_at`, `uptime_seconds`.

## Verification

- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/impostazioni/page.tsx" "src/components/settings/SystemStatusSection.tsx"`
- `venv\Scripts\ruff.exe check tests/test_health_endpoint.py api/main.py api/schemas/system.py`
- `python -m pytest tests/test_health_endpoint.py -q -p no:cacheprovider` -> **passed**
  (`2026-03-11`, eseguito in venv locale reale dall'utente)

## Risks / Residuals

1. `SystemStatusSection.tsx` e ora a **300 LOC esatti**: il prossimo step che aggiunge contenuto
   deve spezzare il componente prima di crescere.
2. Il test backend e ora eseguito con successo in venv reale; il rischio residuo non e piu
   la toolchain pytest ma la crescita del componente UI.

## Next Smallest Step

Aprire il microstep `support snapshot` read-only da `Impostazioni`, ma solo dopo aver estratto
almeno una parte strutturale di `SystemStatusSection` per non sforare il limite file del progetto.
