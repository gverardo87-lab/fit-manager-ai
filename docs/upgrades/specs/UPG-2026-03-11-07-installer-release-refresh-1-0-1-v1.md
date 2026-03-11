# Patch Spec - Installer Release Refresh 1.0.1

## Metadata

- Upgrade ID: UPG-2026-03-11-07
- Date: 2026-03-11
- Owner: Codex
- Area: Installer + Release Engineering + Launch Readiness
- Priority: high
- Status: done

## Objective

Produrre un nuovo installer tracciabile dopo il completamento del blocco
`Connectivity Setup Wizard`, evitando di riutilizzare la vecchia RC `1.0.0`
su un contenuto runtime ormai diverso.

La nuova release candidate deve:

1. riallineare la versione reale del prodotto a `1.0.1`;
2. produrre un artefatto nuovo e distinguibile;
3. aggiornare i documenti di rilascio correnti al nuovo hash/size;
4. restare compatibile con la procedura di upgrade in-place sul PC di Chiara.

## Scope

### Runtime / packaging

- `api/__init__.py`
- `api/main.py`
- `frontend/package.json`
- `frontend/package-lock.json` (solo metadata root)
- `installer/fitmanager.iss`
- `tools/build/build-installer.sh`
- `tools/admin_scripts/e2e_distribution_rehearsal.py`

### Release docs correnti

- `CLAUDE.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `docs/UPGRADE_PROCEDURE.md`

### Governance

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`

## Implementation

1. Bump versione `1.0.0 -> 1.0.1` su backend, frontend e installer.
2. Eliminato il drift su OpenAPI leggendo `version=api.__version__` in `api/main.py`.
3. Rebuild reale del packaging `1.0.1`.
4. Aggiornate le guide correnti che dichiarano il candidato attivo.

## Build Execution

La pipeline standard `bash tools/build/build-installer.sh` non era eseguibile nel terminale
Codex per due limiti ambientali:

1. `bash` assente dal `PATH` PowerShell sandboxato;
2. Git Bash falliva con `couldn't create signal pipe, Win32 error 5`;
3. la `venv\\Scripts\\python.exe` non partiva nel sandbox Codex ma funzionava
   fuori sandbox e nel terminale utente reale.

Per chiudere il microstep senza modificare la pipeline del repo, e' stato eseguito
lo stesso ordine di `build-installer.sh` tramite PowerShell:

1. `ruff check api/`
2. `npm run build` nel frontend fuori sandbox
3. copy di `.next/static` e `public` nello standalone
4. `python -m PyInstaller tools/build/fitmanager.spec --noconfirm`
5. staging media da `catalog.db`
6. staging `dist/release-data`
7. compilazione `ISCC installer/fitmanager.iss`

## Verification

- `venv\\Scripts\\ruff.exe check api/`
- `C:\\Program Files\\nodejs\\npm.cmd run build` (workdir `frontend`, fuori sandbox) -> build green
- packaging backend/media/installer eseguito fuori sandbox con venv reale
- `Get-Item dist\\FitManager_Setup_1.0.1.exe | Select-Object Name,Length,LastWriteTime`
- `Get-FileHash dist\\FitManager_Setup_1.0.1.exe -Algorithm SHA256 | Select-Object Hash,Path`

## Result

- Artefatto: `dist/FitManager_Setup_1.0.1.exe`
- Dimensione: `98,505,675` bytes
- SHA-256: `F2099C2F7B0FE8F357C9D7A3C4268EB7E7E48B833380DAF649F85B181C8FDFE5`

## Residual Risks

1. La pipeline Bash resta il percorso canonico del repo, ma nel terminale Codex locale
   continua a essere affetta da limiti ambientali (`bash` / `signal pipe` / launcher Python).
2. Il nuovo RC non chiude ancora i test manuali su macchina Chiara:
   - upgrade in-place reale
   - validazione wizard `Connettivita`
   - test smartphone/Tailscale/Funnel
3. `docs/COMPETITIVE_ANALYSIS.md` e `node_modules/` restano volutamente fuori da questo microstep.

## Next Smallest Step

Usare `docs/UPGRADE_PROCEDURE.md` come checklist live per aggiornare il PC di Chiara
alla release candidate `1.0.1`, poi verificare sul campo il wizard di connettivita
e la validazione reale del link anamnesi pubblico.
