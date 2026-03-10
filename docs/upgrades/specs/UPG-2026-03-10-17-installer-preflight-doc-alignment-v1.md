# Patch Spec - Installer Preflight Doc Alignment v1

## Metadata

- Upgrade ID: UPG-2026-03-10-17
- Date: 2026-03-10
- Owner: Codex
- Area: Documentation + Launch Readiness + Distribution Governance
- Priority: high
- Status: done

## Historical Note

Questa spec ha congelato il contratto documentale iniziale del rebuild. Il freeze reale poi
accettato dal rebuild `UPG-2026-03-10-19` ha mantenuto la stessa policy `catalog.db canonico / crm.db vuoto nel bundle`,
ma ha documentato esplicitamente la realta' osservata senza modificare i DB:

- `catalog.db` bundle = 400 ID esercizio
- `crm.db` locale = 396 record `in_subset=True`

## Context

Prima di rigenerare il setup installabile serve un contratto unico e autorevole su:

1. commit sorgente congelato;
2. versione candidata da riallineare su tutti i layer;
3. policy bundle dati (`catalog.db` canonico, `crm.db` vuoto);
4. reintroduzione dei dati reali trainer solo tramite restore verificato;
5. gestione corretta della `license.key` cliente fuori dal repository.

Il repository conteneva ancora drift documentale:

- riferimento a `build-installer.sh` non presente nel repo;
- architetture che implicavano `crm.db` gia popolato nel bundle;
- riferimento a `license.key` dentro `installer/assets`;
- checklist release che non distingueva ancora bene tra bundle prodotto e restore dei dati reali.

## Objective

Allineare i documenti autorevoli prima del microstep runtime/build, cosi che il rebuild
dell'installer parta da regole chiare e non da assunzioni locali.

## Decisions To Encode

1. **Source freeze docs-first**: commit `4a19bf2`
2. **Versione candidata**: `1.0.0`
3. **Bundle dati**:
   - `catalog.db` canonico congelato al conteggio reale del bundle release candidate
   - `crm.db` vuoto, first-run-safe
4. **Dati reali Chiara**: ripristinati solo tramite restore verificato del backup reale
5. **Licenza cliente**:
   - destinazione runtime: `data/license.key`
   - non deve vivere nel repository o in `installer/assets`

## Files To Align

- `CLAUDE.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/SUPPORT_RUNBOOK.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Non-Goals

- nessun cambio ancora a `installer/fitmanager.iss`
- nessuna relocation runtime della `license.key` implementata nel codice
- nessun version bump applicato ai file sorgente
- nessun rebuild artefatti o compilazione Inno Setup

## Verification

- grep mirato su `license.key`, `catalog.db`, `crm.db`, `FitManager_Setup`, `build-installer`
- review manuale dei documenti autorevoli toccati
- coerenza tra spec, upgrade log e workboard

## Next Smallest Step

Aprire il microstep runtime/build del preflight:

1. riallineamento versione `1.0.0` su backend/frontend/installer
2. rimozione della `license.key` cliente dal perimetro repository/assets
3. chiarimento o script unico della pipeline `frontend -> backend -> media -> ISCC`
4. rebuild release candidate
