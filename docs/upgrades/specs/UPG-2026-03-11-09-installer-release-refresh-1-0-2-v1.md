# Patch Spec - Installer Release Refresh 1.0.2

## Metadata

- Upgrade ID: UPG-2026-03-11-09
- Date: 2026-03-11
- Owner: Codex
- Area: Installer + Release Engineering + Launch Readiness
- Priority: high
- Status: done

## Objective

Produrre un nuovo installer distinguibile e distribuibile dopo il fix
`UPG-2026-03-11-08`, senza riusare la RC `1.0.1` ormai invalida.

La nuova release candidate deve:

1. riallineare la versione reale del prodotto a `1.0.2`;
2. ricostruire davvero il setup con rewrite standalone loopback-safe;
3. congelare nuovo artefatto, dimensione e SHA-256;
4. diventare la baseline corretta per l'upgrade in-place sul PC di Chiara.

## Scope

### Runtime / packaging

- `api/__init__.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `installer/fitmanager.iss`
- `tools/build/build-installer.sh`
- `tools/admin_scripts/e2e_distribution_rehearsal.py`

### Release docs correnti

- `CLAUDE.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `docs/UPGRADE_PROCEDURE.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`

### Governance

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Implementation

1. Bump versione `1.0.1 -> 1.0.2`.
2. Aggiornare i documenti di rilascio correnti al nuovo target.
3. Eseguire rebuild reale di frontend, backend, media e installer.
4. Congelare hash e dimensione del nuovo artefatto.

## Verification

- `venv\\Scripts\\ruff.exe check api/`
- `C:\\Program Files\\nodejs\\npm.cmd run build` (workdir `frontend`)
- rebuild reale packaging
- `Get-Item dist\\FitManager_Setup_1.0.2.exe`
- `Get-FileHash dist\\FitManager_Setup_1.0.2.exe -Algorithm SHA256`
- `git diff --check`

## Result

- Artefatto: `dist/FitManager_Setup_1.0.2.exe`
- Dimensione: `98,510,802` bytes
- SHA-256: `9D9EF9FF22053C37EEE8B66EA41C58FA5D467395120EFE37B2AB613FFC6B51C6`

## Residual Risks

1. La correzione packaging e' chiusa solo per i nuovi artefatti: la RC `1.0.1` resta invalida e non va redistribuita.
2. Dopo il rebuild serve comunque l'upgrade in-place reale sul PC di Chiara.

## Next Smallest Step

Usare `docs/UPGRADE_PROCEDURE.md` per aggiornare di nuovo il PC di Chiara con la RC `1.0.2`
e verificare subito `Stato installazione`, dati reali e wizard `Connettivita`.
