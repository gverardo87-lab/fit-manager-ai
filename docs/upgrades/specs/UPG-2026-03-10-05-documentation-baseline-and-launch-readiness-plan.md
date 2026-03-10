# UPG-2026-03-10-05 - Documentation Baseline and Launch Readiness Plan

## Meta

- ID: `UPG-2026-03-10-05`
- Date: `2026-03-10`
- Area: `Documentation + Launch Readiness`
- Type: `Docs + Process`
- Owner: `Codex`
- Branch: `codex_02`

---

## Problem

La documentazione autorevole del progetto non descriveva piu il repository reale.
In particolare:

- `README.md` riportava route, componenti, hook e porte obsolete
- `ARCHITECTURE.md` era ancora basato su conteggi storici e sezioni non piu coerenti con il repo
- `CLAUDE.md` esponeva un comando di avvio produzione che non attivava in modo esplicito il gate licenza
- non esisteva un piano di hardening pre-lancio sintetico ma eseguibile, ordinato per microstep

Effetto pratico: runbook non affidabili, support debt immediato e rischio di concentrare il team su nuove feature invece che sulla chiusura dei gate di rilascio.

---

## Desired Outcome

1. Documentazione top-level allineata al repository reale e ai runbook correnti.
2. Conteggi "decorativi" sostituiti con snapshot verificati o con descrizioni meno fragili.
3. Comandi di avvio produzione resi esplicitamente compatibili con il gate licenza.
4. Strategia pre-lancio formalizzata in una sequenza di microstep con criteri di uscita.

---

## Scope

In scope:

- `README.md`
- `ARCHITECTURE.md`
- `CLAUDE.md`
- `docs/upgrades/README.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/ai-sync/WORKBOARD.md`
- questa spec

Out of scope:

- fix runtime frontend/backend
- ricostruzione del virtualenv
- chiusura effettiva dei lint/test rossi
- refactor architetturali del codice

---

## Repository Snapshot Used

Snapshot verificato via `rg` il `2026-03-10`:

- `api/`: 123 file Python
- `api/routers/`: 21 file
- `api/models/`: 21 file
- handler REST annotati: 115
- `frontend/src/`: 250 file TS/TSX
- page route: 24
- componenti React: 151
- hook file: 22
- `tests/`: 27 file pytest
- `core/`: 27 file Python
- `tools/`: 63 script
- `tools/admin_scripts/`: 48 script

---

## Implementation

### Microstep 1 - README autorevole

- riallineare comandi dev/prod
- correggere porta frontend dev a `3001`
- esplicitare la differenza tra avvio sviluppo e avvio produzione con licenza
- sostituire numeri storici con snapshot corrente

### Microstep 2 - Documento architetturale affidabile

- rimuovere sezioni basate su LOC e conteggi ormai falsi
- introdurre una fotografia chiara di topologia, domini, invarianti e debt pre-lancio
- aggiungere una strategia di hardening in 6 step con exit criteria

### Microstep 3 - CLAUDE operativo

- chiarire che il runbook di produzione da sorgente deve attivare `LICENSE_ENFORCEMENT_ENABLED=true`
- aggiungere uno snapshot autorevole del repository per disinnescare metriche stale

### Microstep 4 - Governance sync

- registrare il change in `UPGRADE_LOG`
- aggiornare `docs/upgrades/README.md`
- chiudere la task nel `WORKBOARD`

---

## Verification Plan

Documentale:

- review manuale dei file aggiornati
- cross-check numeri con comandi `rg`

Quality baseline riportata nella documentazione:

- `venv\Scripts\ruff.exe check api tests`
- `npm --prefix frontend run lint -- src`
- `npm --prefix frontend run build`
- `python -m pytest -q tests`

Nota: questa patch documenta anche lo stato reale dei gate dove l'ambiente locale non consente una verifica completa.

---

## Launch Hardening Strategy

### Step 1 - Toolchain recovery

Obiettivo:

- ripristinare virtualenv, pytest e runbook eseguibili

Exit criteria:

- backend test command ufficiale funzionante
- ambiente dev/prod documentato senza ambiguita

### Step 2 - Frontend critical error closure

Obiettivo:

- zero errori lint su `frontend/src`

Focus:

- hook order violation
- side effect in render
- auth/middleware path fragili

Exit criteria:

- `eslint src` a zero errori

### Step 3 - Backend critical regression suite

Obiettivo:

- proteggere finance, workspace e readiness con una suite minima ma autorevole

Exit criteria:

- test critici verdi in locale in modo ripetibile

### Step 4 - End-to-end business rehearsal

Obiettivo:

- validare i flussi che generano ricavo e fiducia

Exit criteria:

- cliente -> contratto -> rata -> pay/unpay -> ledger
- agenda -> consumo crediti -> stato contratto
- backup -> mutate -> restore

### Step 5 - Distribution and network rehearsal

Obiettivo:

- provare installer, licenza, rete locale, Tailscale e public portal come farebbe il cliente

Exit criteria:

- installazione pulita su macchina fredda
- licenza enforced
- accesso remoto e backup verificati

### Step 6 - Freeze and rollback

Obiettivo:

- rendere il rilascio governato e reversibile

Exit criteria:

- release checklist
- baseline commit
- rollback pack
- issue register post-launch

---

## Risks

- La documentazione ora e' piu vera, ma mette in luce che il prodotto non ha ancora gate verdi end-to-end.
- Se il team usa la nuova chiarezza per continuare ad aggiungere feature, il beneficio si perde.
- Il punto singolo piu urgente resta il virtualenv rotto: senza quello la strategia si ferma allo step 1.

---

## Done When

- i file top-level non riportano piu porte e conteggi palesemente superati
- il percorso di avvio produzione da sorgente non e piu documentato in modo insicuro
- esiste un piano pre-lancio corto, leggibile e ordinato per microstep
- il change e tracciato in spec, log upgrade e workboard
