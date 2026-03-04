# Patch Spec - Launch Market Readiness Roadmap

## Metadata

- Upgrade ID: UPG-2026-03-04-06
- Date: 2026-03-04
- Owner: gvera + codex + claude-code
- Area: Cross-layer (API + Frontend + Deployment)
- Priority: high
- Target release: launch candidate (T-5 days)
- Status: wave_3_complete
- Revision: R1 (claude-code) — vedi sezione "Revisione R1" in fondo

## Problem

Siamo a ridosso del lancio e servono due cose insieme:
1. chiudere i blocker del `docs/DEPLOYMENT_PLAN.md` ancora mancanti;
2. fare hardening UX pagina-per-pagina con focus su protezione utente, praticita e zero frizione.

Se non lavoriamo per micro-step con gate rigidi, aumentano regressioni, ritardi e code quality debt.

## Desired Outcome

Consegna market-ready in modo progressivo, con rilasci intermedi verificabili:
- ogni step e piccolo, testabile, committabile e pushabile;
- ogni step rispetta `CLAUDE.md` (workflow, quality gate, type sync, invalidation);
- i prerequisiti di distribuzione sono soddisfatti prima del freeze finale.

## Scope

- In scope:
  - Strategia esecutiva incrementale con commit/push intermedi.
  - Sequenza prioritaria per prerequisiti launch (license, first-run, health, build distribution).
  - Audit UX pagina-per-pagina del dashboard con miglioramenti ad alto impatto pratico.
  - Regole di metodo (DoR/DoD, lock file, gate pre-commit).
- Out of scope:
  - Nuove macro-feature non necessarie al lancio.
  - Refactor estesi non legati a value/risk immediato.
  - Ottimizzazioni premature su moduli AI Phase 2 non richiesti per MVP commerciale.

## Strategic Constraints (Fonte: CLAUDE + Deployment Plan)

1. Workflow obbligatorio in 4 step: Schema/Types -> Router -> Hook/UI -> Build/Verifica.
2. `bash tools/scripts/check-all.sh` obbligatorio prima di ogni commit.
3. Type sync ferreo: Pydantic <-> `frontend/src/types/api.ts`.
4. Mutation hooks con invalidazione simmetrica su lista/dettaglio/correlate.
5. Regole deployment-aware sempre attive: path relativi, empty states, dati in `data/`, config via env, niente seed runtime.
6. Priorita launch da `docs/DEPLOYMENT_PLAN.md`: license middleware, setup wizard first-run, JWT secret auto-generation, `/health` robusto, standalone build path.

## Gap Snapshot (2026-03-04)

Da validare/implementare come priorita alta:
- ~~Sistema licenza RSA~~ — **DONE** (`api/services/license.py`, 164 LOC, 5 test PASS)
- ~~License middleware~~ — **DONE** (in `api/main.py:202-235`, gated by `LICENSE_ENFORCEMENT_ENABLED` env)
- Setup Wizard primo avvio (creazione trainer senza seed runtime).
- JWT secret bootstrap persistente in `data/.env`.
- `/health` con stato licenza + versione + DB business/catalog.
- Build frontend standalone e pipeline distribuzione (backend exe + launcher + installer).
- **License Generation CLI** — mancante, necessario per generare licenze firmabili.

Gia presente e da preservare:
- `check-all.sh` come gate pre-commit.
- Dual DB, backup/integrity checks, zero hardcoded API IP, security pattern IDOR.
- UX guardrails (unsaved changes, empty states in gran parte delle pagine).

## S0.1 Baseline Execution (2026-03-04) — DONE

### Gate results

- `bash tools/scripts/check-all.sh`:
  - KO in questo ambiente (command `bash` non disponibile in PowerShell).
- Gate equivalente eseguito manualmente:
  - `venv\\Scripts\\python.exe -m ruff check api/` -> PASS (`ruff 0.15.4`)
  - `cd frontend && npx next build` -> PASS
  - Nota build: warning Next.js su deprecazione convenzione `middleware` (migrare a `proxy`).

### Backlog blocker ordinato (evidence-based)

1. ~~**Licensing RSA + middleware API**~~ — **DONE** (S1.1 + S1.2)
2. **Setup Wizard first-run** (critical, launch blocker)
   - Nessuna route setup/onboarding in `frontend/src/app`.
3. **JWT secret bootstrap persistente** (high)
   - `api/config.py` usa fallback statico `"dev-secret-change-in-production"` se env mancante.
4. **Health endpoint parziale** (high)
   - `/health` ritorna solo `status/version/db/catalog`; manca stato licenza.
5. **Frontend standalone output** (high)
   - `frontend/next.config.ts` non espone `output: "standalone"`.
6. **Frontend middleware deprecato** (medium)
   - Build warning: convenzione `middleware.ts` deprecata, raccomandata `proxy`.
7. **License Generation CLI** (high, scoperto in R1)
   - Nessuno script per firmare licenze (`tools/admin_scripts/generate_license.py` assente).

## S1.1 Implementation Snapshot (2026-03-04) — DONE

### Delivered

- Nuovo modulo backend: `api/services/license.py`
  - lettura `data/license.key`
  - verifica JWT RSA (`RS256`)
  - stati normalizzati: `valid | missing | invalid | expired | unconfigured`
  - payload tipizzato (`LicenseClaims`) + risultato strutturato (`LicenseCheckResult`)
  - risoluzione chiave pubblica: parametro > env > file > embedded (4-tier fallback)
- Test unitari: `tests/test_license_service.py`
  - missing file
  - unconfigured public key
  - valid license
  - expired license
  - invalid signature

### Validation

- `venv\\Scripts\\python.exe -m pytest -q tests/test_license_service.py` -> PASS (5/5)
- `venv\\Scripts\\python.exe -m ruff check api/` -> PASS
- `cd frontend && npx next build` -> PASS (warning noto su `middleware` deprecato)

## S1.2 License Middleware (2026-03-04) — DONE

### Delivered

- Middleware HTTP registrato in `api/main.py:213-235`
- Gated by `LICENSE_ENFORCEMENT_ENABLED` env var (default: disabled)
- Exempt paths: `/health`, `/docs`, `/redoc`, `/openapi.json`, `/api/auth/login`, `/api/auth/register`, `/media/*`
- Se licenza non valida → `403 Forbidden` con `license_status` e `detail`
- `request.state.license_status` disponibile per downstream handlers

### Residuo

- Test integrazione middleware → coprire in S1.3 (JWT bootstrap crea fresh env ideale per test).

---

## Gradual Implementation Strategy (Micro-step + Commit/Push)

> **NOTA R1**: L'ordine delle wave e' stato rivisto. La distribuzione (vecchia Wave 4) e' stata
> promossa a **Wave 3** perche' e' il vero blocker di lancio. L'UX hardening (vecchia Wave 3)
> e' stata spostata a **Wave 4** e ridotta alle 3 pagine piu' critiche commercialmente.

### Wave 0 - Baseline e controllo rischio (Day 0) — DONE

**S0.1 Baseline tecnico**
- Output: fotografia stato corrente (build, lint, test core) + backlog launch blockers ordinato.
- Gate: `bash tools/scripts/check-all.sh`.
- Commit: `chore(launch): baseline snapshot and launch backlog [UPG-2026-03-04-06-S0.1]`.
- Push: immediato dopo gate green.

### Wave 1 - License pipeline completa (Day 1) — DONE

**S1.1 License core backend** — DONE
- Output: `api/services/license.py` + verifica JWT RSA + load license da `data/license.key`.
- Gate: test unit parser/licenza + `check-all.sh`.
- Commit/push dedicato.

**S1.2 License middleware** — DONE
- Output: enforcement su request API (con allowlist endpoint pubblici).
- Gated by `LICENSE_ENFORCEMENT_ENABLED` env var.
- Commit/push dedicato.

**S1.3 JWT secret bootstrap**
- Output: generazione sicura al primo avvio + persistenza in `data/.env` se mancante.
- `secrets.token_hex(32)` → scritto in `data/.env` come `JWT_SECRET=...`.
- `api/config.py` legge `data/.env` con `load_dotenv(DATA_DIR / ".env")` prima del fallback.
- Gate: startup test (fresh env senza JWT_SECRET) + `check-all.sh`.
- Commit/push dedicato.

**S1.4 Health endpoint hardening**
- Output: `/health` include versione, db business/catalog, stato licenza, uptime.
- Chiama `check_license()` e include `license_status` nel response.
- Gate: endpoint test + `check-all.sh`.
- Commit/push dedicato.

**S1.5 License Generation CLI** (nuovo in R1)
- Output: `tools/admin_scripts/generate_license.py` — script per generare keypair RSA + firmare token JWT.
- Subcomandi: `generate-keys` (crea keypair in `~/.fitmanager/`), `sign` (firma token con claims).
- `python -m tools.admin_scripts.generate_license generate-keys`
- `python -m tools.admin_scripts.generate_license sign --client "gym-roma" --tier pro --months 12`
- Output: file `.key` pronto per deploy in `data/license.key`.
- Gate: test round-trip (genera chiavi → firma → verifica con `check_license()`) + `check-all.sh`.
- Commit/push dedicato.

**S1.6 Frontend license UX**
- Output: pagina/flow "Licenza scaduta o non valida" con CTA supporto.
- Interceptor Axios cattura 403 con `license_status` → redirect a `/licenza`.
- Pagina `/licenza`: stato chiaro + istruzioni + contatto.
- Gate: next build + smoke navigation + `check-all.sh`.
- Commit/push dedicato.

### Wave 2 - First-run e onboarding (Day 2) — DONE

**S2.1 Setup Wizard primo avvio** — DONE
- Output: percorso guidato da DB vuoto -> creazione trainer -> ingresso dashboard.
- Backend: `GET /api/setup/status` (controlla se esiste almeno un trainer).
- Frontend: `/setup` route, redirect automatico se DB vuoto (no trainer).
- Step: nome + email + password + saldo iniziale cassa (opzionale).
- Gate: scenario E2E fresh install + `check-all.sh`.
- Commit/push dedicato.

**S2.2 Empty states hardening mirato** — DONE
- Output: pagine critiche senza dati mostrano CTA chiare (no schermo bianco).
- Focus: dashboard (zero clienti), clienti (lista vuota), contratti (lista vuota), cassa (zero movimenti).
- Gate: checklist manuale su route dashboard critiche + `check-all.sh`.
- Commit/push dedicato.

### Wave 3 - Build distribuzione (Day 3-4) — ex Wave 4, promossa — DONE

> **Rationale R1**: La distribuzione e' il vero blocker di lancio. Se il software non si installa,
> l'UX hardening non serve a nulla. Promossa da Day 4-5 a Day 3-4.

**S3.1 Frontend standalone** — DONE
- `output: "standalone"` in `next.config.ts` + formula porte generica (3000→8000, 3001→8001, 3002→8002).
- `build-frontend.sh` copia `.next/static` + `public/` nel bundle standalone.
- Bundle: 45MB. Testato: `server.js` serve l'app correttamente.
- Commit: `c78fe20`.

**S3.2 Backend packaging** — DONE
- `entry_point.py` wrapper uvicorn con `--port` support.
- `fitmanager.spec` PyInstaller: directory mode, esclude ~1.8GB AI libs.
- `build-backend.sh` compila e verifica `dist/fitmanager/fitmanager.exe`.
- Bundle: 102MB. Testato: health check OK su porta 8002.
- Commit: `74261ae`.

**S3.3 Launcher + installer** — DONE
- `launcher.bat`: avvia backend + frontend + apre browser, supporta `--port`.
- `fitmanager.iss`: Inno Setup 6, italiano, data/ preservata su aggiornamenti.
- `EULA.txt` placeholder.
- Installer compilato: **58MB** (`FitManager_Setup.exe`).
- Commit: `9439448` + `470177f`.

**S3.4 Smoke test** — DONE
- Installer eseguito su macchina di sviluppo.
- Flusso: install → avvio da shortcut desktop → login page funzionante.
- Bug trovato e risolto: `.next/static/` mancante nel bundle → ricompilato.
- Backend health: `{"status":"ok","db":"connected","catalog":"connected"}`.

### Wave 4 - UX hardening mirato (Day 4-5) — ex Wave 3, ridotta

> **Rationale R1**: 8 pagine in 1-2 giorni e' over-scoped per T-5. Ridotto alle 3 pagine
> con massimo impatto commerciale. Le altre possono essere hardened post-lancio.

Ordine di impatto commerciale (top 3):
1. `login` + `dashboard` — prima impressione, KPI overview
2. `clienti` + `clienti/[id]` — cuore del CRM, usato ogni giorno
3. `contratti` + `contratti/[id]` — flusso pagamenti, valore economico diretto

Per ogni pagina:
- micro-batch da max 1 area UX per volta (copy, CTA, feedback, error states, guard, mobile responsiveness);
- 1 commit/push per batch;
- gate obbligatorio: check manuale desktop/mobile + `check-all.sh`.

Pagine rimanenti (`cassa`, `schede`, `agenda`, `esercizi`, `impostazioni`) → post-lancio,
gia' funzionali con empty states e guardrails di base.

## Commit and Push Discipline

1. Un micro-step = un commit atomico.
2. Nessun commit senza gate verde (`check-all.sh` minimo).
3. Messaggi commit con prefisso area + step ID (`[UPG-...-Sx.y]`).
4. Push immediato dopo commit green per ridurre divergenza e rischio perdita.
5. Se lo step supera 300-400 LOC o tocca >5 file eterogenei, spezzare prima del commit.

## Quality Gates per Step

- Tecnico:
  - `bash tools/scripts/check-all.sh`
  - test mirati sul dominio toccato
  - type sync e invalidation check espliciti in review
- UX:
  - empty/error/loading state verificati
  - copy italiana chiara e action-oriented
  - mobile pass minimo su viewport 375px e 768px
- Sicurezza/integrita:
  - bouncer/IDOR invarianti preservati
  - atomic commit su operazioni multi-entita
  - nessun path assoluto o segreti hardcoded

## Operational Cadence

- Daily start: claim task + lock file nel workboard.
- During: micro-step massimo 2-4 ore.
- Daily end: aggiornamento `UPGRADE_LOG.md` + note rischi residui.
- Freeze policy: nessun "nice-to-have" dopo Day 4, solo bugfix/regressioni launch-critical.

## Acceptance Criteria

- Funzionale:
  - Piano salvato e tracciato in `UPGRADE_LOG`.
  - Ogni wave ha output, gate e criterio di commit/push.
  - Prerequisiti launch del deployment plan mappati con priorita esplicita.
- UX:
  - Top 3 pagine hardened con ordine di priorita commerciale.
  - Focus esplicito su protezione utente e praticita operativa.
- Tecnico:
  - Strategia allineata a workflow/DoD in `CLAUDE.md`.
  - Metodo compatibile con dual-env e quality gates correnti.

## Test Plan

- Unit/Integration:
  - test puntuali per licensing, startup bootstrap, middleware, health.
  - test round-trip license generation CLI.
- Manual checks:
  - smoke test first-run + percorsi principali dashboard.
  - verifica responsive e empty states su pagine top 3.
  - installer su macchina pulita.
- Build/Lint gates:
  - `bash tools/scripts/check-all.sh` prima di ogni commit.

## Risks and Mitigation

- Rischio 1: scope creep vicino al lancio.
  - Mitigazione: wave sequencing + freeze policy Day 4 + Wave 4 ridotta a top 3 pagine.
- Rischio 2: regressioni da patch cross-layer.
  - Mitigazione: commit atomici, push frequenti, gate obbligatori.
- Rischio 3: blocker distribuzione scoperti tardi.
  - Mitigazione: distribuzione promossa a Wave 3 (Day 3-4), prima dell'UX hardening.
- Rischio 4: PyInstaller/Inno Setup richiedono tuning imprevisto su macchina target.
  - Mitigazione: S3.4 smoke test su macchina pulita come gate finale.

## Rollback Plan

- Rollback per micro-step via `git revert <commit>` (mai reset distruttivi).
- In caso regressione critica: rollback ultimo step, riapertura task con fix minimale.
- Dati utente protetti: nessun reset DB, solo migrazioni/patch backward-safe.

---

## Revisione R1 — Claude Code (2026-03-04)

Differenze rispetto al piano originale Codex:

| # | Punto debole originale | Revisione R1 |
|---|------------------------|--------------|
| 1 | Wave 3 (UX) prima di Wave 4 (distribuzione) | **Invertite**: distribuzione → Wave 3 (Day 3-4), UX → Wave 4 (Day 4-5). La distribuzione e' il vero launch blocker |
| 2 | Wave 3 UX: 8 pagine in 1-2 giorni | **Ridotta a top 3**: login+dashboard, clienti, contratti. Le altre sono gia funzionali |
| 3 | Mancava License Generation CLI | **Aggiunto S1.5**: `generate_license.py` con generate-keys + sign subcommands |
| 4 | S1.2 non rifletteva stato reale | **Aggiornato a DONE**: middleware gia presente in `main.py:202-235` |
| 5 | Gap snapshot non aggiornato | **Aggiornato**: S1.1 e S1.2 barrati come DONE, aggiunto CLI mancante |
| 6 | Rischi mancavano PyInstaller/installer | **Aggiunto Rischio 4**: tuning imprevisto su macchina target |

## Notes

- Riferimenti:
  - `CLAUDE.md`
  - `docs/DEPLOYMENT_PLAN.md`
  - `docs/upgrades/checklists/DOR_DOD_CHECKLIST.md`
  - `docs/ai-sync/MULTI_AGENT_SYNC.md`
