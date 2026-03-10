# FitManager AI Studio — Release Checklist v1.0

> Checklist operativa pre-lancio. Ogni item deve essere verificato prima del go-live.

---

## 1. Quality Gates

- [x] `bash tools/scripts/check-all.sh` — ruff (0 errori) + next build (0 errori TS)
- [x] ESLint: 0 errori, 5 warning residui (non-actionable `react-hooks/incompatible-library`)
- [x] `pytest tests/ -v` — 269 test verdi, 0 falliti
- [x] Frontend vitest: 69 test data protection verdi
- [x] E2E business rehearsal: 36/36 PASS (client, contract, rate, pay/unpay, ledger, agenda, credits, backup, restore)
- [x] E2E distribution rehearsal: 62/62 PASS (artifacts, license, enforcement, network, backup, portal, config)

## 2. Build Artifacts

- [x] PyInstaller backend exe: `dist/fitmanager/fitmanager.exe` (bundle ~100 MB)
- [x] Next.js standalone: `frontend/.next/standalone/server.js`
- [x] Inno Setup installer: `dist/FitManager_Setup.exe` (~83 MB)
- [x] Launcher: `installer/launcher.bat` con `LICENSE_ENFORCEMENT_ENABLED=true`
- [x] Node runtime: `installer/node/node.exe`
- [x] Seed data in bundle: esercizi JSON + relazioni + media

## 3. License System

- [x] RSA keypair generata (`~/.fitmanager/`)
- [x] Chiave pubblica in `data/license_public.pem`
- [x] License.key firmata: client `chiara-bassani`, tier `pro`, scade 2027-02-27
- [x] Health endpoint riporta `license_status: valid`
- [x] Launcher impone `LICENSE_ENFORCEMENT_ENABLED=true` in produzione
- [ ] Test enforcement negativo: rimuovere license.key e verificare /licenza page

## 4. Dati e Configurazione

- [x] `data/crm.db` — database produzione con dati reali
- [x] `data/catalog.db` — catalogo scientifico (53 muscoli, 15 articolazioni, 47 condizioni)
- [x] `data/.env` — JWT_SECRET (52 char), PUBLIC_PORTAL_ENABLED, PUBLIC_BASE_URL
- [x] `data/media/exercises/` — 1788 foto esercizi
- [x] `data/exercises/` — 3 seed JSON (esercizi + relazioni + media)
- [x] 391 esercizi attivi (102 compound, 101 isolation, 54 stretching, 50 bodyweight, 35 cardio, 30 mobilita, 19 avviamento)

## 5. Rete e Accesso

- [x] Backend binding: `--host 0.0.0.0` (LAN + Tailscale)
- [x] Frontend binding: `-H 0.0.0.0` (LAN + Tailscale)
- [x] CORS configurato per localhost, LAN (192.168.x.x), Tailscale (100.x.x.x)
- [x] Tailscale Funnel: `https://giacomo.tail8a3bc3.ts.net/`
- [x] Public portal attivo: token generazione + validazione funzionante
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

---

## Baseline

- **Branch**: `codex_02`
- **Baseline commit**: vedi tag `v1.0.0-rc1` (se applicato)
- **Data**: 2026-03-10

## Rollback

In caso di problema critico post-lancio:
1. Fermare launcher.bat (chiudere finestra)
2. Ripristinare backup pre-lancio: `data/backups/pre_update_*.sqlite`
3. Reinstallare versione precedente da installer salvato
4. Se necessario, restore DB via endpoint `/api/backup/restore`

---

*Generata il 2026-03-10 durante Step 6 Launch Hardening.*
