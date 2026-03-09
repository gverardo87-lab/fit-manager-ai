# UPG-2026-03-09-10 - Shared Client Freshness Policy Runtime

## Metadata

- Upgrade ID: `UPG-2026-03-09-10`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Clinical Readiness + Portal UX + Client Profile + Shared Policy`
- Priority: `high`
- Target release: `codex_02`

## Problem

Prima di questo microstep, la logica warning/timeline di `misurazioni` e `schede` era divisa:

- backend readiness:
  - `measurement_review` a `+30 giorni`
  - `workout_review` a `+21 giorni`
- frontend locale:
  - `measurement_gap` warning/critical a `25/35 giorni`
  - `scheda_age` warning/critical a `21/35 giorni`

Questo produceva drift reale:

- stesse entita giudicate in modo diverso tra dashboard/worklist, portale cliente e profilo cliente;
- warning UI calcolati localmente, fuori dal contratto API;
- impossibilita di riusare la stessa policy dentro `Oggi` e nel resto del CRM.

## Desired Outcome

Rendere il backend l'unica fonte di verita per `misurazioni` e `schede`:

- una policy condivisa di freshness;
- un contratto readiness esteso con segnali strutturati;
- frontend che consuma il payload readiness invece di ricreare soglie locali.

## Scope

- In scope:
  - nuovo service backend condiviso per freshness `misurazioni` e `schede`;
  - estensione schema `ClinicalReadinessClientItem`;
  - riallineamento delle superfici:
    - portale cliente
    - worklist readiness
    - profilo cliente `Panoramica`
  - rimozione del calcolo locale threshold-based da `client-alerts.ts`.
- Out of scope:
  - nuova mutation workspace (`snooze`, `seen`);
  - refactor di `Oggi` per usare subito i nuovi segnali;
  - anamnesi freshness come oggetto dedicato nel payload;
  - nuovi endpoint API.

## Impact Map

- Files/modules touched:
  - `api/schemas/clinical.py`
  - `api/services/client_freshness.py`
  - `api/services/clinical_readiness.py`
  - `tests/test_dashboard_clinical_readiness.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/lib/client-alerts.ts`
  - `frontend/src/app/(dashboard)/monitoraggio/[id]/page.tsx`
  - `frontend/src/components/portal/CompositionSection.tsx`
  - `frontend/src/components/portal/ProgramSection.tsx`
  - `frontend/src/components/portal/ReadinessClientCard.tsx`
  - `frontend/src/components/clients/profile/PanoramicaTab.tsx`
  - `docs/upgrades/specs/UPG-2026-03-09-10-shared-client-freshness-policy-runtime.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api` | `frontend` | `tests` | `docs`
- Invarianti da preservare:
  - nessun dato anamnestico sensibile in overview surfaces;
  - nessun importo economico introdotto in pagine neutre;
  - nessuna query frontend aggiuntiva solo per warning locali;
  - readiness resta trainer-scoped e read-only.

## What Changed

### Backend

- introdotto `api/services/client_freshness.py` come policy unica di freshness;
- formalizzate soglie runtime:
  - `misurazioni`: warning `25d`, critical `35d`
  - `scheda`: warning `21d`, critical `35d`
- `ClinicalReadinessClientItem` ora espone:
  - `timeline_label`
  - `measurement_freshness`
  - `workout_freshness`
- `clinical_readiness.py` ora:
  - costruisce i segnali freshness via service condiviso;
  - usa quei segnali anche per scegliere `next_due_date`, `timeline_status`, `timeline_reason`, `timeline_label`;
  - mantiene readiness/onboarding invariati, ma con timeline coerente.

### Frontend

- `frontend/src/lib/client-alerts.ts` non calcola piu soglie:
  - mappa solo i segnali readiness backend in alert UI;
- `PanoramicaTab` non usa piu hook locali `workouts/measurements` per generare banner freshness;
- `CompositionSection` usa `measurementFreshness` dal payload readiness;
- `ProgramSection` usa `workoutFreshness` dal payload readiness;
- `ReadinessClientCard` usa i nuovi stati freshness per i dot `Mis` / `Sch` e mostra `timeline_label` human-friendly;
- `monitoraggio/[id]` passa i segnali readiness alle sezioni senza query extra.

## API Contract

Nuovi campi su `ClinicalReadinessClientItem`:

- `timeline_label: string | null`
- `measurement_freshness: ClinicalFreshnessSignal`
- `workout_freshness: ClinicalFreshnessSignal`

Nuovo oggetto:

- `ClinicalFreshnessSignal`
  - `domain`
  - `status`
  - `label`
  - `cta_label`
  - `cta_href`
  - `timeline_status`
  - `reason_code`
  - `due_date`
  - `last_recorded_date`
  - `days_to_due`
  - `days_since_last`

## Acceptance Criteria

- readiness backend e warning frontend non usano piu soglie divergenti per `misurazioni` e `schede`;
- profilo cliente e portale clinico leggono il payload readiness come fonte di verita;
- il worklist readiness mostra stato `Mis` / `Sch` coerente con freshness, non solo con la semplice presenza;
- `timeline_label` e leggibile per l'utente finale;
- nessuna nuova query frontend introdotta solo per i banner freshness.

## Test Plan

- backend lint:
  - `venv\Scripts\ruff.exe check api\schemas\clinical.py api\services\client_freshness.py api\services\clinical_readiness.py tests\test_dashboard_clinical_readiness.py`
- frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/types/api.ts" "src/lib/client-alerts.ts" "src/app/(dashboard)/monitoraggio/[id]/page.tsx" "src/components/portal/ProgramSection.tsx" "src/components/portal/CompositionSection.tsx" "src/components/portal/ReadinessClientCard.tsx" "src/components/clients/profile/PanoramicaTab.tsx"`
- backend pytest mirato:
  - `venv\Scripts\python.exe -m pytest -q tests\test_dashboard_clinical_readiness.py -p no:cacheprovider`

## Verification Outcome

- `ruff` sui file backend toccati: `PASS`
- `eslint` sui file frontend toccati: `PASS`
- `pytest` mirato readiness: `BLOCKED`
  - motivo: il `venv` locale continua a risolvere verso il launcher Microsoft Store, quindi `venv\Scripts\python.exe` non e eseguibile in questo ambiente

## Risks and Mitigation

- Rischio 1: la workspace UI `Oggi` non consuma ancora direttamente i nuovi segnali nested.
  - Mitigazione 1: il contratto readiness ora e pronto e puo essere usato nel prossimo microstep workspace senza reintrodurre soglie locali.
- Rischio 2: l'anamnesi review non e ancora un oggetto freshness separato.
  - Mitigazione 2: `timeline_label` gia copre il caso lato UI; un oggetto dedicato si puo aggiungere dopo senza rompere questa base.
- Rischio 3: alcuni test readiness storici restano data-sensitive.
  - Mitigazione 3: le nuove assertion usano in parte calcoli relativi a `date.today()` dove possibile.

## Rollback Plan

- revert del service `client_freshness.py`;
- revert dell'estensione schema readiness e dei consumer frontend;
- il sistema torna al comportamento precedente con warning locali in `client-alerts.ts`.

## Notes

- Questo microstep chiude il drift architetturale piu pericoloso del filone workspace: la stessa entita non viene piu giudicata con soglie diverse tra backend e frontend.
- Prossimo step consigliato:
  - usare `measurement_freshness` e `workout_freshness` anche nel case engine di `Oggi`, cosi` le famiglie `Cliente da Rivalutare` e `Programma da Rivedere` nascono gia sulla policy unificata.
