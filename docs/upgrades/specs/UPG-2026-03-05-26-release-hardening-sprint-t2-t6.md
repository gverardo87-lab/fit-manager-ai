# UPG-2026-03-05-26 - Release Hardening Sprint (T2-T6)

## Metadata

- Upgrade ID: UPG-2026-03-05-26
- Date: 2026-03-05
- Owner: Codex
- Area: Launch Hardening (Frontend + Installer + Lint)
- Priority: high
- Target release: codex_02

## Problem

Pre-lancio con rischi ancora attivi su quality gate:

- errori ESLint bloccanti lato frontend (`setState-in-effect`, `refs during render`, `no-unescaped-entities`);
- drift lint minori su hook/lib/test attivi;
- rumore Ruff su `tests/legacy` non attivi;
- rischio licensing per distribuzione incontrollata (`license.key` pre-bundled in installer).

## Desired Outcome

Portare il ramo in stato piu' vicino a release-grade senza alterare logica business:

- ESLint frontend: 0 errori;
- Ruff `api/` + `tests/`: 0 errori con esclusione legacy;
- installer: nessuna copia di `assets/license.key` nel pacchetto installato.

## Scope

- In scope:
  - T2: hardening hook patterns in file critici frontend (init state, mount-keyed dialog/panel, rimozione setState sync in effect hotspot).
  - T3: escape apostrofi JSX (`react/no-unescaped-entities`).
  - T4: fix minori lint (prefer-const, unused import/vars, deps memo, parametro non usato).
  - T5: configurazione Ruff con `extend-exclude = ["tests/legacy/"]`.
  - T6: rimozione riga `Source: "assets\\license.key"` da `installer/fitmanager.iss`.
- Out of scope:
  - redesign UX globale;
  - refactor architetturali backend;
  - riduzione warning ESLint residui non bloccanti.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/clienti/page.tsx`
  - `frontend/src/app/(dashboard)/contratti/page.tsx`
  - `frontend/src/app/(dashboard)/impostazioni/page.tsx`
  - `frontend/src/app/(dashboard)/clienti/[id]/misurazioni/page.tsx`
  - `frontend/src/components/*` (agenda/auth/clienti/contracts/exercises/layout/ui/workouts)
  - `frontend/src/hooks/useContracts.ts`
  - `frontend/src/hooks/useRates.ts`
  - `frontend/src/hooks/useSmartProgramming.ts`
  - `frontend/src/lib/{export-workout.ts,smart-programming.ts,workout-monitoring.ts}`
  - `frontend/src/__tests__/data-protection/edge-cases.test.ts`
  - `tests/test_jwt_bootstrap.py`
  - `pyproject.toml`
  - `installer/fitmanager.iss`
  - docs upgrade/workboard sync files
- Layers coinvolti: `frontend`, `tests`, `installer`, `tooling-config`, `docs`
- Invarianti da preservare:
  - nessuna modifica semantica ai flussi business (contratti/rate/anamnesi/agenda);
  - sicurezza multi-tenant backend invariata;
  - licensing runtime post-install demandato alla pagina/flow di attivazione.

## Acceptance Criteria

- Technical:
  - `npm --prefix frontend run -s lint -- "src/"` senza errori.
  - `venv\Scripts\python.exe -m ruff check api/ tests/` senza errori.
  - `installer/fitmanager.iss` non contiene `license.key`.
- Process:
  - commit separati per microtask T2..T6;
  - doc sync su `UPGRADE_LOG.md`, `README.md`, `WORKBOARD.md`.

## Test Plan

- `npm --prefix frontend run -s lint -- "src/"`
- `venv\Scripts\python.exe -m ruff check api/ tests/`
- `rg -n "license\\.key" installer/fitmanager.iss`
- equivalenza gate Windows per `check-all.sh`:
  - `venv\Scripts\python.exe -m ruff check api/`
  - `npm --prefix frontend run build`

## Risks and Mitigation

- Risk 1: refactor di inizializzazione dialog/page puo' alterare reset stato in edge-case.
- Mitigation 1: mount keyed e init lazy per preservare bootstrap deterministico senza side-effect in render/effect.
- Risk 2: warning ESLint residui possono generare debito tecnico.
- Mitigation 2: backlog warning separato, mantenendo gate bloccante sugli errori a zero.

## Rollback Plan

- Revert selettivo dei commit del blocco T2-T6 (+ fix build emerso al gate finale):
  - `df8ab38` (hooks hardening),
  - `01534b7` (apostrofi JSX),
  - `b2a99e7` (fix minori),
  - `ddb4994` (Ruff scope),
  - `2db1bad` (installer licensing),
  - `f074c41` (fix duplicazione handler in `CommandPalette` per build production).
