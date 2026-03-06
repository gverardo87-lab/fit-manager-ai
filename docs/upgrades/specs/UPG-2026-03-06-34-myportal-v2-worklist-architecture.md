# UPG-2026-03-06-34 - MyPortal v2 Worklist Architecture

## Metadata

- Upgrade ID: UPG-2026-03-06-34
- Date: 2026-03-06
- Owner: Codex
- Area: MyPortal Architecture + Dashboard API + Client Operations
- Priority: high
- Target release: codex_02

## Problem

La board attuale MyPortal/readiness funziona bene con volumi piccoli, ma con 50+ clienti diventa difficile da gestire:

- payload full-list senza paginazione;
- filtri e ricerca in memoria lato frontend;
- timeline troncata, non gestita come coda operativa completa;
- polling fisso ogni 60s su dataset intero;
- modello orientato a "stato del cliente", non a "task operativi con scadenza".

Questo blocca l'obiettivo prodotto: portale unico per chinesiologo su allenamento, anamnesi, misure, progressi e (in seguito) alimentazione.

## Desired Outcome

Trasformare MyPortal in un sistema worklist-first:

- singola coda task operativa (non medica) con priorita, scadenza, owner e stato;
- timeline completa e filtrabile server-side;
- reminder deterministici su finestre temporali (D-14, D-7, D-1, overdue);
- onboarding legacy a attrito minimo tramite bootstrap automatico da dati gia presenti;
- dashboard usata come overview, MyPortal come cockpit operativo principale.

## Scope

- In scope:
  - blueprint architetturale dominio task MyPortal;
  - piano rollout in microstep con backward compatibility;
  - strategia migrazione legacy a basso sforzo;
  - definizione KPI operativi e quality gates.
- Out of scope:
  - prescrizioni mediche o workflow medical device;
  - invio notifiche esterne realtime (push/email) nel primo microstep;
  - redesign completo di tutte le pagine cliente nel primo rilascio.

## Impact Map

- Future files/modules expected:
  - `api/routers/dashboard.py` (decomposizione readiness legacy e compat layer)
  - `api/routers/myportal.py` (nuova worklist API paginata)
  - `api/services/myportal_task_engine.py` (regole deterministiche task/reminder)
  - `api/schemas/myportal.py` (nuovi response/request model)
  - `api/schemas/financial.py` (rimozione coupling readiness dal dominio finance)
  - `frontend/src/hooks/useMyPortal.ts` (query paginata + filtri server-side)
  - `frontend/src/app/(dashboard)/clienti/myportal/page.tsx` (worklist UI scalabile)
  - `tests/test_myportal_worklist.py` (integrazione API + isolation trainer)
  - `tests/test_dashboard_clinical_readiness.py` (compatibilita backward)
- Layers: api + frontend + tests + docs
- Invariants:
  - multi-tenant safety (ownership trainer) invariata;
  - endpoint critici read-only dove previsto;
  - nessun dato finanziario esposto in overview clinica;
  - comportamento dashboard esistente non regressivo durante rollout.

## Target Architecture

### 1) Domain Model: `portal_task`

Ogni cliente genera task operativi normalizzati:

- `task_type`: `anamnesi_update | baseline_measurement | workout_review | progress_review | nutrition_followup`
- `status`: `open | in_progress | snoozed | done | ignored_external`
- `priority`: `high | medium | low`
- `due_at`, `days_to_due`, `reason_code`
- `source`: `system_rule | manual | import_legacy`
- `client_id`, `trainer_id`, `owner_id` (default trainer)
- `payload_light` (metadati minimi per CTA)

Nota: dominio "tecnico-operativo", non medico.

### 2) Worklist API (server-side pagination/filtering)

Proposta contratti:

- `GET /api/myportal/worklist?page=1&page_size=25&status=open&priority=high&search=...`
- `GET /api/myportal/timeline?from=YYYY-MM-DD&to=YYYY-MM-DD&status=overdue,today,upcoming_7d`
- `POST /api/myportal/tasks/{task_id}/status` (`in_progress|done|snoozed|ignored_external`)
- `POST /api/myportal/tasks/bulk-status` (azioni massive sicure)
- `GET /api/myportal/summary` (KPI leggeri per header/cards)

Dashboard mantiene un pannello top-N come compat view verso la nuova sorgente.

### 3) Reminder Engine Deterministico

Regole iniziali:

- gap strutturali (anamnesi/baseline/scheda mancanti): task immediato (`today`);
- review periodiche:
  - misurazioni: 30 giorni
  - scheda: 21 giorni
  - anamnesi: 180 giorni
- finestre reminder:
  - D-14 (planning)
  - D-7 (prep)
  - D-1 (azione)
  - overdue (escalation)

### 4) Legacy Migration Zero-Friction

Bootstrap automatico al primo accesso MyPortal:

- se esiste anamnesi legacy -> task `anamnesi_update` (non blocca operativita);
- se scheda esterna non gestita in FitManager -> stato `ignored_external` con motivo "piano esterno";
- se dati storici assenti -> task minimi "operativamente tracciabili" senza data-entry completo;
- wizard rapido solo sui campi minimi necessari.

Obiettivo: evitare migrazione massiva manuale iniziale.

## Rollout Plan (Microsteps)

1. M0 - Arch Foundation
   - separare schema readiness da `financial.py` in modulo dedicato;
   - introdurre endpoint paginato worklist read-only;
   - mantenere endpoint legacy `clinical-readiness` come compat layer.
2. M1 - MyPortal UI Scalability
   - tabella paginata server-side;
   - filtri persistenti (status, priority, due bucket, assignee);
   - timeline completa virtualizzata.
3. M2 - Task Actions
   - transizioni stato singole + bulk;
   - audit trail minimale (`who/when/from/to`).
4. M3 - Reminder Orchestration
   - digest giornaliero in-app;
   - metriche SLA task (due/completed/overdue age).
5. M4 - Scientific Portal Expansion
   - trend panel misure + compliance allenamento;
   - slot dominio nutrizione (senza bloccare core CRM).

## Implementation Status (2026-03-06)

- Completed now (M0a + M0b + M0c + M1 frontend):
  - spec architetturale MyPortal v2 definita;
  - endpoint read-only paginato `GET /api/dashboard/clinical-readiness/worklist`;
  - filtri server-side disponibili: `view`, `priority`, `timeline_status`, `search`;
  - ordinamento server-side opzionale `sort_by=priority|due_date` per timeline/worklist;
  - hook frontend `useClinicalReadinessWorklist` + type sync;
  - pagina MyPortal collegata al worklist paginato con controlli pagina (`Precedente/Successiva`);
  - rimozione filtro/search full-list in memoria nella pagina MyPortal;
  - UI MyPortal M1 con filtri avanzati completi (priorita/scadenza/ordinamento/page-size) e reset filtri;
  - timeline MyPortal paginata con controllo densita card e stato filtri coerente alla worklist;
  - test backend su paginazione/filtri/sort/isolation multi-tenant;
  - schema readiness estratto in modulo dedicato `api/schemas/clinical.py` con compat re-export in `financial.py`.
- Next smallest step (M1 backend optimization):
  - ridurre full-scan nel calcolo summary/worklist con pre-aggregazioni/query path piu selettivi;
  - introdurre metriche tecniche (latenza endpoint, cardinalita filtri) per verificare la tenuta 100+ clienti.

## Acceptance Criteria

- Functional:
  - MyPortal gestisce fluentemente 50+ clienti con paginazione e filtri server-side;
  - timeline mostra tutte le scadenze rilevanti, non solo top subset;
  - task legacy bootstrap creati automaticamente senza import massivo manuale.
- UX:
  - pianificazione giornaliera possibile in <10 minuti su 50 clienti;
  - azioni principali completabili in <=3 click.
- Technical:
  - ownership checks invariati su tutte le nuove API;
  - query state/frontend invalidation simmetrica post update task;
  - nessuna regressione su dashboard readiness esistente durante fase compat.

## KPI di Successo (SMART)

- >=95% task ad alta priorita completati entro scadenza.
- <5% task in overdue da oltre 7 giorni.
- >=80% clienti legacy "operativamente tracciati" senza data-entry storico completo.
- tempo medio triage giornaliero trainer <10 minuti (campione reale).

## Test Plan

- API:
  - test ownership multi-tenant (`trainer A` non legge/modifica task `trainer B`);
  - test paginazione/filter deterministici;
  - test transizioni stato ammesse/non ammesse.
- Frontend:
  - lint file toccati;
  - loading/error/empty states su worklist/timeline;
  - verifica query invalidation dopo azioni task.
- Performance:
  - smoke test con dataset seed 100 clienti attivi;
  - controllo latenza worklist p95 su filtri standard.

## Risks and Mitigation

- Risk 1: coupling attuale readiness-financial aumenta debito tecnico.
- Mitigation 1: estrazione schema in modulo dedicato entro M0, con shim temporaneo.
- Risk 2: duplicazione logica tra dashboard e MyPortal.
- Mitigation 2: task engine unico lato API, dashboard solo consumer top-N.
- Risk 3: attrito migrazione legacy su schede esterne.
- Mitigation 3: stato esplicito `ignored_external` + revisit periodica configurabile.
- Risk 4: overload UX con troppe card/sezioni.
- Mitigation 4: layout worklist-first con metriche sintetiche e progressive disclosure.

## Rollback Plan

- Mantenere endpoint legacy `clinical-readiness` fino a completamento M2.
- Feature flag MyPortal v2 (`MYPORTAL_V2_ENABLED`) per rollback rapido su UI attuale.
- Revert mirato di router/hook/pagina myportal senza toccare dati core CRM.

## External Benchmark Anchors

- Epic interoperability/scheduling (care gaps + reminder flows): `open.epic.com`
- Oracle Health reminder windows + inbox volume controls: `docs.oracle.com`
- HL7 FHIR pattern references: `Task`, `CarePlan`, `Subscription`
- athenahealth patient engagement automation references: `athenahealth.com`
