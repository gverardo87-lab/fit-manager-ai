# Patch Spec - Installer Release Candidate Build v1

## Metadata

- Upgrade ID: UPG-2026-03-10-19
- Date: 2026-03-10
- Owner: Codex
- Area: Installer + Build Pipeline + Release Candidate
- Priority: high
- Status: done

## Context

Dopo `UPG-2026-03-10-18` la pipeline era formalmente pronta al rebuild reale, ma il primo
tentativo di compilazione Inno Setup falliva durante il packaging del `catalog.db`.

Il problema non era nei dati canonici da modificare, ma nel fatto che il file live
`data/catalog.db` risultava aperto da un altro processo locale. Il rebuild release candidate
andava quindi chiuso senza toccare i DB, congelando la realta' esistente:

- `catalog.db` canonico del bundle = 400 ID esercizio
- `crm.db` locale = 396 record `in_subset=True`
- nessuna alterazione del contenuto dei database

## Objective

Produrre davvero la release candidate `1.0.0` e trasformare il rebuild in un processo
tracciabile e ripetibile anche quando i file live in `data/` sono lockati.

## Decisions Implemented

1. **Reality freeze accettato senza cambiare i DB**
   - il bundle mantiene `catalog.db` come fonte canonica da 400 ID esercizio
   - il mismatch con il `crm.db` locale (396 attivi) viene trattato come dato di realta'
     documentato, non come trigger per un nuovo intervento sul database
2. **Snapshot immutabili per il packaging**
   - `build-installer.sh` stagea `catalog.db` e `license_public.pem` in `dist/release-data`
   - `fitmanager.iss` non legge piu' questi file dai path live in `data/`
3. **Fix del lock root cause**
   - Inno Setup packagea ora snapshot copiati localmente, evitando il fallimento su file lockati
4. **EULA semplificata**
   - la EULA viene mostrata via `LicenseFile`
   - non viene piu' installata come file separato nel target
5. **RC artifact congelato**
   - file: `dist/FitManager_Setup_1.0.0.exe`
   - size: `98,480,252` bytes
   - SHA-256: `05B2AF87FD01CF1A3DC5BB3DDFCAD3785C798CFA9DE3D93480B33359F2E3DC58`

## Files Changed

- `installer/fitmanager.iss`
- `tools/build/build-installer.sh`
- `tools/build/build-media.sh`
- `tools/build/build-backend.sh`
- `tools/scripts/check-all.sh`
- `CLAUDE.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`
- `docs/upgrades/specs/UPG-2026-03-10-17-installer-preflight-doc-alignment-v1.md`
- `docs/upgrades/specs/UPG-2026-03-10-18-installer-preflight-runtime-build-v1.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Verification

- `bash tools/build/build-installer.sh`
- `Get-Item dist\\FitManager_Setup_1.0.0.exe | Select-Object Name,Length,LastWriteTime`
- `Get-FileHash dist\\FitManager_Setup_1.0.0.exe -Algorithm SHA256 | Select-Object Hash,Path`
- `git diff --check`
- review manuale di `fitmanager.iss`, `build-installer.sh`, `build-media.sh`

## Residual Risks

1. La release candidate e' stata costruita, ma non ancora provata su macchina Windows pulita.
2. Il restore del backup reale di Chiara sulla release candidate resta ancora da eseguire.
3. Il test manuale negativo `rimuovi license.key -> redirect a /licenza` resta ancora aperto.
4. La validazione reale LAN / Tailscale / Funnel resta ancora operativa, non documentale.

## Next Smallest Step

Eseguire la rehearsal manuale della release candidate:

1. installazione pulita su macchina Windows non-dev
2. verifica `Stato installazione` e `Snapshot diagnostico`
3. restore del backup reale di Chiara
4. test negativo licenza installata
5. validazione rete reale (LAN, Tailscale, Funnel)
