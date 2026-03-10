# Patch Spec - Installer Preflight Runtime/Build v1

## Metadata

- Upgrade ID: UPG-2026-03-10-18
- Date: 2026-03-10
- Owner: Codex
- Area: Installer + Build Pipeline + Distribution Readiness
- Priority: high
- Status: done

## Context

Dopo il preflight docs-first (`UPG-2026-03-10-17`) il repository aveva ancora drift operativo
nei file reali di build:

1. frontend ancora a `0.1.0` mentre backend e installer dichiaravano `1.0.0`;
2. `installer/fitmanager.iss` produceva ancora `FitManager_Setup.exe`;
3. `tools/build/build-media.sh` leggeva gli esercizi attivi da `data/crm.db`, incompatibile con
   la policy release candidate (`crm.db` vuoto nel bundle);
4. mancava uno script unico che orchestrasse `check-all -> frontend -> backend -> media -> ISCC`;
5. la `license.key` cliente era ancora presente nel perimetro repository `installer/assets`.

## Objective

Chiudere il microstep runtime/build del preflight prima di rigenerare l'installer candidato,
cosi che naming artefatti, fonte dati del bundle e perimetro licenza siano univoci e ripetibili.

## Decisions Implemented

1. **Version sync**:
   - `api/__init__.py` resta `1.0.0`
   - `frontend/package.json` -> `1.0.0`
   - `frontend/package-lock.json` root metadata -> `1.0.0`
   - `installer/fitmanager.iss` usa `MyAppVersion = 1.0.0`
2. **Installer naming**:
   - output tracciabile `FitManager_Setup_1.0.0.exe`
   - rehearsal e documenti attivi aggiornati al naming versionato
3. **Bundle media source of truth**:
   - `build-media.sh` legge gli esercizi attivi da `data/catalog.db`
   - query canonica = `UNION` delle junction tables catalog
   - guard esplicito su `391` esercizi attivi attesi
4. **License perimeter hardening**:
   - `installer/assets/license.key` rimosso dal repository
   - `.gitignore` aggiornato per prevenire reintroduzione accidentale
   - la sola destinazione runtime resta `data/license.key`
5. **Build orchestration**:
   - nuovo `tools/build/build-installer.sh`
   - opzioni: `--skip-checks`, `--iscc /path/to/ISCC.exe`

## Files Changed

- `frontend/package.json`
- `frontend/package-lock.json`
- `installer/fitmanager.iss`
- `.gitignore`
- `tools/build/build-media.sh`
- `tools/build/build-installer.sh`
- `tools/admin_scripts/e2e_distribution_rehearsal.py`
- `CLAUDE.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Non-Goals

- nessun rebuild reale dell'installer in questo microstep
- nessuna compilazione Inno Setup eseguita
- nessun restore del backup reale di Chiara
- nessuna validazione macchina pulita / LAN / Tailscale / Funnel

## Verification

- `git diff --check`
- `venv\\Scripts\\ruff.exe check tools\\admin_scripts\\e2e_distribution_rehearsal.py`
- grep mirato su:
  - `installer/assets/license.key`
  - `FitManager_Setup.exe`
  - `"version": "0.1.0"`
- review manuale di `installer/fitmanager.iss`, `build-media.sh`, `build-installer.sh`

## Residual Risks

1. Il microstep non prova ancora il rebuild reale: la catena `build-installer.sh -> ISCC` resta da eseguire.
2. La validazione di sintassi `bash -n` non e' stata eseguibile nel terminale corrente:
   Git Bash presente ma bloccato da errore ambientale Win32 `couldn't create signal pipe`.
3. La verifica `catalog.db -> 391 attivi -> media staged` resta logica/statica finche' lo script non viene eseguito.

## Next Smallest Step

Eseguire il rebuild candidato e la rehearsal distributiva:

1. `bash tools/build/build-installer.sh`
2. verificare artefatti in `dist/`
3. installazione su macchina Windows pulita
4. restore del backup reale di Chiara
5. test negativo licenza e validazione rete reale
