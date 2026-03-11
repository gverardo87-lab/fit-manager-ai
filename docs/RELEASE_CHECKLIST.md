# FitManager AI Studio - Release Checklist v1.0

> Checklist operativa pre-lancio. Ogni item deve essere verificato prima del go-live.

---

## 1. Quality Gates

- [x] `bash tools/scripts/check-all.sh` - ruff (0 errori) + next build (0 errori TS)
- [x] `bash tools/build/build-installer.sh` - quality gate + frontend + backend + media + Inno Setup
- [x] ESLint: 0 errori, 5 warning residui (non-actionable `react-hooks/incompatible-library`)
- [x] `pytest tests/ -v` - 269 test verdi, 0 falliti
- [x] Frontend vitest: 69 test data protection verdi
- [x] E2E business rehearsal: 36/36 PASS (client, contract, rate, pay/unpay, ledger, agenda, credits, backup, restore)
- [x] E2E distribution rehearsal: 62/62 PASS (artifacts, license, enforcement, network, backup, portal, config)

## 2. Build Artifacts

- [x] PyInstaller backend exe: `dist/fitmanager/fitmanager.exe` (bundle ~100 MB)
- [x] Next.js standalone: `frontend/.next/standalone/server.js`
- [x] Inno Setup installer: `dist/FitManager_Setup_1.0.0.exe` (`98,480,252` bytes)
- [x] SHA-256 release candidate: `05B2AF87FD01CF1A3DC5BB3DDFCAD3785C798CFA9DE3D93480B33359F2E3DC58`
- [x] Launcher: `installer/launcher.bat` con `LICENSE_ENFORCEMENT_ENABLED=true`
- [x] Node runtime: `installer/node/node.exe`
- [x] Seed data in bundle: esercizi JSON + relazioni + media
- [x] Versione `1.0.0` riallineata in `api/__init__.py`, `frontend/package.json` e `installer/fitmanager.iss`
- [x] Nome output installer versionato e tracciabile, non solo `FitManager_Setup.exe`
- [x] Packaging di `catalog.db` e `license_public.pem` tramite snapshot immutabili in `dist/release-data`

## 3. License System

- [x] RSA keypair generata (`~/.fitmanager/`)
- [x] Chiave pubblica in `data/license_public.pem`
- [x] `license.key` cliente tenuta fuori dal repository e fuori da `installer/assets`, con copia solo verso `data/license.key` sulla macchina target
- [x] Health endpoint riporta `license_status: valid`
- [x] Launcher impone `LICENSE_ENFORCEMENT_ENABLED=true` in produzione
- [ ] Test enforcement negativo manuale: rimuovere `license.key` su installazione reale e verificare pagina `/licenza`

## 4. Dati e Configurazione

- [ ] `data/crm.db` nel bundle release candidate vuoto e first-run-safe
- [x] `data/catalog.db` congelato al catalogo canonico corrente con 400 ID esercizio per il bundle release candidate
- [x] `data/.env` - JWT_SECRET (52 char), PUBLIC_PORTAL_ENABLED, PUBLIC_BASE_URL
- [x] `data/media/exercises/` - 1788 foto esercizi
- [x] `data/exercises/` - 3 seed JSON (esercizi + relazioni + media)
- [x] Freeze reality 2026-03-10: `catalog.db` canonico = 400 ID esercizio, `crm.db` locale = 396 attivi; il bundle usa il catalogo come sola fonte per media e tassonomia
- [ ] Restore del backup reale di Chiara verificato sulla release candidate
- [ ] Backup/restore ricontrollato con dati sensibili reali: clienti, contratti, schede, agenda, cassa e media

## 5. Rete e Accesso

- [x] Backend binding: `--host 0.0.0.0` (LAN + Tailscale)
- [x] Frontend binding: `-H 0.0.0.0` (LAN + Tailscale)
- [x] CORS configurato per localhost, LAN (192.168.x.x), Tailscale (100.x.x.x)
- [x] Tailscale Funnel: `https://giacomo.tail8a3bc3.ts.net/`
- [x] Public portal attivo: token generazione + validazione funzionante
- [x] Validazione guidata in-app del portale pubblico: link anamnesi di prova generato da `Impostazioni -> Connettivita` e verifica funzionale pagina pubblica + token (`21 passed` suite connectivity completa)
- [ ] Test LAN da tablet/smartphone (stesso WiFi)
- [ ] Test Tailscale VPN da rete esterna
- [ ] Test anamnesi self-service da smartphone via Funnel

## 6. Backup & Restore

- [x] Create backup: atomico + SHA-256 checksum + integrity check
- [x] Verify backup: checksum match + integrity OK
- [x] Download backup: funzionante
- [x] Restore backup: WAL checkpoint + schema sync + cookie clear + redirect login
- [x] Export JSON v2.0: 17 entita business in ordine FK-safe
- [x] Auto-backup al startup (max 5)
- [x] Retention: max 30 backup manuali

## 7. Test Manuali (Non Automatizzabili)

- [ ] Installazione pulita su macchina Windows senza sviluppo
- [ ] Launcher avvia backend + frontend + apre browser
- [ ] Login con credenziali produzione
- [ ] Flusso completo: cliente -> contratto -> rata -> pagamento -> cassa
- [ ] Flusso scheda allenamento: crea -> esercizi -> salva -> export
- [ ] Agenda: crea evento PT -> verifica crediti scalati
- [ ] Impostazioni: saldo iniziale cassa configurabile

## 8. Operativita e Supporto

- [x] `docs/SUPPORT_RUNBOOK.md` disponibile come runbook unico per supporto, licenza, backup/restore e recovery post-update
- [x] `Impostazioni` espone `Stato installazione` + `Snapshot diagnostico`
- [x] Logging locale attivo in `data/logs/fitmanager.log`

---

## Baseline

- **Branch**: `codex_02`
- **Preflight anchor commit**: `4a19bf2` (docs-first)
- **Release candidate artifact**: `dist/FitManager_Setup_1.0.0.exe`
- **Release candidate SHA-256**: `05B2AF87FD01CF1A3DC5BB3DDFCAD3785C798CFA9DE3D93480B33359F2E3DC58`
- **Versione candidata**: `1.0.0`
- **Data**: 2026-03-10

## Rollback

In caso di problema critico post-lancio:
1. Fermare launcher.bat (chiudere finestra)
2. Ripristinare backup pre-lancio: `data/backups/pre_update_*.sqlite`
3. Reinstallare versione precedente da installer salvato
4. Se necessario, restore DB via endpoint `/api/backup/restore`

---

*Generata il 2026-03-10 durante Step 6 Launch Hardening.*
