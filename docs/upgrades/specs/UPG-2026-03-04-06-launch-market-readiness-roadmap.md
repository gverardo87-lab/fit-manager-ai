# Patch Spec - Launch Market Readiness Roadmap

## Metadata

- Upgrade ID: UPG-2026-03-04-06
- Date: 2026-03-04
- Owner: gvera + codex
- Area: Cross-layer (API + Frontend + Deployment)
- Priority: high
- Target release: launch candidate (T-5 days)
- Status: planned

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
- Sistema licenza RSA e middleware license-aware su API.
- Setup Wizard primo avvio (creazione trainer senza seed runtime).
- JWT secret bootstrap persistente in `data/.env`.
- `/health` con stato licenza + versione + DB business/catalog.
- Build frontend standalone e pipeline distribuzione (backend exe + launcher + installer).

Gia presente e da preservare:
- `check-all.sh` come gate pre-commit.
- Dual DB, backup/integrity checks, zero hardcoded API IP, security pattern IDOR.
- UX guardrails (unsaved changes, empty states in gran parte delle pagine).

## S0.1 Baseline Execution (2026-03-04)

### Gate results

- `bash tools/scripts/check-all.sh`:
  - KO in questo ambiente (command `bash` non disponibile in PowerShell).
- Gate equivalente eseguito manualmente:
  - `venv\\Scripts\\python.exe -m ruff check api/` -> PASS (`ruff 0.15.4`)
  - `cd frontend && npx next build` -> PASS
  - Nota build: warning Next.js su deprecazione convenzione `middleware` (migrare a `proxy`).

### Backlog blocker ordinato (evidence-based)

1. **Licensing RSA + middleware API** (critical, launch blocker)
   - `api/services/license.py` assente (`license_service=missing`).
   - Nessun riferimento licensing enforcement nei router principali.
2. **Setup Wizard first-run** (critical, launch blocker)
   - Nessuna route setup/onboarding in `frontend/src/app` (`rg --files ... setup|onboarding|wizard` senza match).
3. **JWT secret bootstrap persistente** (high)
   - `api/config.py` usa fallback statico `"dev-secret-change-in-production"` se env mancante.
4. **Health endpoint parziale** (high)
   - `/health` ritorna solo `status/version/db/catalog`; manca stato licenza.
5. **Frontend standalone output** (high)
   - `frontend/next.config.ts` non espone `output: "standalone"`.
6. **Frontend middleware deprecato** (medium)
   - Build warning: convenzione `middleware.ts` deprecata, raccomandata `proxy`.

## Gradual Implementation Strategy (Micro-step + Commit/Push)

### Wave 0 - Baseline e controllo rischio (Day 0)

**S0.1 Baseline tecnico**
- Output: fotografia stato corrente (build, lint, test core) + backlog launch blockers ordinato.
- Gate: `bash tools/scripts/check-all.sh`.
- Commit: `chore(launch): baseline snapshot and launch backlog [UPG-2026-03-04-06-S0.1]`.
- Push: immediato dopo gate green.

### Wave 1 - Launch blockers obbligatori (Day 1-2)

**S1.1 License core backend**
- Output: `api/services/license.py` + verifica JWT RSA + load license da `data/license.key`.
- Gate: test unit parser/licenza + `check-all.sh`.
- Commit/push dedicato.

**S1.2 License middleware**
- Output: enforcement su request API (con allowlist endpoint pubblici).
- Gate: test integrazione auth + `check-all.sh`.
- Commit/push dedicato.

**S1.3 JWT secret bootstrap**
- Output: generazione sicura al primo avvio + persistenza in `data/.env` se mancante.
- Gate: startup test (fresh env) + `check-all.sh`.
- Commit/push dedicato.

**S1.4 Health endpoint hardening**
- Output: `/health` include versione, db business/catalog, stato licenza.
- Gate: endpoint test + `check-all.sh`.
- Commit/push dedicato.

**S1.5 Frontend license UX**
- Output: pagina/flow "Licenza scaduta o non valida" con CTA supporto.
- Gate: next build + smoke navigation + `check-all.sh`.
- Commit/push dedicato.

### Wave 2 - First-run e onboarding (Day 2-3)

**S2.1 Setup Wizard primo avvio**
- Output: percorso guidato da DB vuoto -> creazione trainer -> ingresso dashboard.
- Gate: scenario E2E fresh install + `check-all.sh`.
- Commit/push dedicato.

**S2.2 Empty states hardening mirato**
- Output: pagine critiche senza dati mostrano CTA chiare (no schermo bianco).
- Gate: checklist manuale su tutte le route dashboard + `check-all.sh`.
- Commit/push dedicato.

### Wave 3 - UX hardening pagina-per-pagina (Day 3-4)

Ordine di impatto commerciale:
1. `login` + `dashboard`
2. `clienti` + `clienti/[id]` (+ anamnesi/misurazioni/progressi)
3. `contratti` + `contratti/[id]`
4. `cassa`
5. `schede` + `schede/[id]` + `allenamenti`
6. `agenda`
7. `esercizi` + `esercizi/[id]`
8. `impostazioni`

Per ogni pagina:
- micro-batch da max 1 area UX per volta (copy, CTA, feedback, error states, guard, mobile responsiveness);
- 1 commit/push per batch;
- gate obbligatorio: check manuale desktop/mobile + `check-all.sh`.

### Wave 4 - Build distribuzione e release candidate (Day 4-5)

**S4.1 Frontend standalone**
- Output: configurazione output standalone e verifica bundle.
- Commit/push dedicato.

**S4.2 Backend packaging skeleton**
- Output: spec/script base per build backend distribuibile.
- Commit/push dedicato.

**S4.3 Launcher + installer prep**
- Output: script launcher + bozza installer testabile su macchina pulita.
- Commit/push dedicato.

**S4.4 Go-live smoke test**
- Output: flusso completo install -> licenza -> setup -> cliente -> contratto -> pagamento -> agenda.
- Gate finale: `check-all.sh` + smoke E2E + checklist pre-distribuzione completa.

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
  - Audit pagina-per-pagina con ordine di priorita commerciale.
  - Focus esplicito su protezione utente e praticita operativa.
- Tecnico:
  - Strategia allineata a workflow/DoD in `CLAUDE.md`.
  - Metodo compatibile con dual-env e quality gates correnti.

## Test Plan

- Unit/Integration:
  - test puntuali per licensing, startup bootstrap, middleware, health.
- Manual checks:
  - smoke test first-run + percorsi principali dashboard.
  - verifica responsive e empty states su tutte le pagine dashboard.
- Build/Lint gates:
  - `bash tools/scripts/check-all.sh` prima di ogni commit.

## Risks and Mitigation

- Rischio 1: scope creep vicino al lancio.
  - Mitigazione: wave sequencing + freeze policy Day 4.
- Rischio 2: regressioni da patch cross-layer.
  - Mitigazione: commit atomici, push frequenti, gate obbligatori.
- Rischio 3: blocker distribuzione scoperti tardi.
  - Mitigazione: Wave 1-2 dedicata ai prerequisiti deployment.

## Rollback Plan

- Rollback per micro-step via `git revert <commit>` (mai reset distruttivi).
- In caso regressione critica: rollback ultimo step, riapertura task con fix minimale.
- Dati utente protetti: nessun reset DB, solo migrazioni/patch backward-safe.

## Notes

- Riferimenti:
  - `CLAUDE.md`
  - `docs/DEPLOYMENT_PLAN.md`
  - `docs/upgrades/checklists/DOR_DOD_CHECKLIST.md`
  - `docs/ai-sync/MULTI_AGENT_SYNC.md`
