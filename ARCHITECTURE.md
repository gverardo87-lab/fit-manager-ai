# FitManager AI Studio - Documento Architetturale

> Documento di riferimento per capire come e' fatto il prodotto oggi e cosa manca per dichiararlo pronto al lancio.
> Aggiornato: 10 Marzo 2026.

---

## 1. Executive Summary

FitManager AI Studio e' un CRM locale per chinesiologi, personal trainer e professionisti fitness a P.IVA con focus su:

- affidabilita operativa quotidiana
- privacy dei dati cliente
- integrita di contratti, rate e ledger
- estendibilita verso funzioni AI senza rendere il CRM dipendente dall'AI

La baseline architetturale attuale e solida nei principi, ma non ancora chiusa come prodotto launch-ready.
Il rischio principale non e la mancanza di feature: e il drift tra documentazione, quality gate e comportamento reale di alcuni percorsi critici frontend/backend.

---

## 2. Topologia ad Alto Livello

```text
Frontend (Next.js 16 + React 19)
  - App Router
  - route dashboard e CRM
  - workspace operativi
  - public portal anamnesi
  - dev: 3001 / prod: 3000
            |
            | JSON REST + JWT
            v
Backend API (FastAPI + SQLModel + Pydantic)
  - auth, clienti, contratti, rate
  - agenda, cassa, backup
  - exercises, workouts, workspace
  - monitoring, guide support, licensing
  - dev: 8001 / prod: 8000
            |
            v
SQLite local-first
  - data/crm.db
  - data/crm_dev.db
  - data/catalog.db

Layer laterali:
  - core/: moduli AI e legacy non necessari al CRM core
  - tools/: seed, smoke test, build, migrazioni, script operativi
  - installer/: packaging e launcher Windows
```

---

## 3. Snapshot Reale del Repository (2026-03-10)

| Area | Stato attuale |
|---|---|
| `api/` | 123 file Python |
| `api/routers/` | 21 router module |
| `api/models/` | 21 model module |
| Handler REST annotati | 115 |
| `frontend/src/` | 250 file TS/TSX |
| Page route | 24 |
| Componenti React | 151 |
| Hook file | 22 |
| `tests/` | 27 file pytest |
| `core/` | 27 file Python |
| `tools/` | 63 script |
| `tools/admin_scripts/` | 48 script |

Questa tabella e una fotografia verificata via `rg`, non una stima storica.

---

## 4. Superfici Prodotto Attive

### 4.1 Frontend

Le route attive oggi coprono:

- dashboard principale `/`
- workspace `/oggi` e `/rinnovi-incassi`
- clienti, profilo cliente, anamnesi e misurazioni
- contratti e dettaglio contratto
- agenda
- cassa
- esercizi e dettaglio esercizio
- schede e builder
- monitoraggio
- guida
- impostazioni
- setup
- licenza
- portale pubblico anamnesi

### 4.2 Backend

I domini backend principali sono:

- autenticazione JWT
- clienti
- contratti
- rate
- agenda
- movimenti di cassa
- spese ricorrenti
- dashboard/readiness/workspace
- workout ed exercise library
- backup e restore
- licensing e public portal
- training science additivo

---

## 5. Confini Architetturali

| Layer | Puo importare | Non deve importare |
|---|---|---|
| `api/` | FastAPI, SQLModel, Pydantic, servizi backend | `frontend/`, componenti UI |
| `frontend/` | React, Next.js, hook e type mirror API | `api/` Python modules |
| `core/` | stdlib, moduli AI/legacy locali | `frontend/`, endpoint API diretti |
| `tools/` | script operativi e QA | logica business UI-specific |

Regola pratica: il CRM core deve restare utilizzabile anche se `core/` non viene eseguito.

---

## 6. Dati e Runtime

### 6.1 Database

Database principali:

- `data/crm.db`: produzione
- `data/crm_dev.db`: sviluppo
- `data/catalog.db`: catalogo dedicato

Il progetto e' local-first: dati, backup e asset sensibili vivono nel filesystem locale.

### 6.2 Porte e ambienti

| Ambiente | Frontend | Backend | DB |
|---|---|---|---|
| Dev | `3001` | `8001` | `crm_dev.db` |
| Prod | `3000` | `8000` | `crm.db` |

### 6.3 Licenza

Il middleware licenza e attivato solo quando `LICENSE_ENFORCEMENT_ENABLED=true`.

Conseguenza importante:

- `installer/launcher.bat` abilita il gate correttamente
- un avvio manuale del backend senza env dedicata bypassa il controllo licenza

Per questo la documentazione operativa deve sempre distinguere tra:

- avvio manuale per sviluppo
- avvio produzione reale con gate licenza attivo

---

## 7. Invarianti di Sicurezza e Integrita

### 7.1 Backend

- Multi-tenancy via `trainer_id` da JWT, mai accettato dal client come dato fidato.
- Deep relational IDOR check per entita collegate.
- Bouncer pattern per precondizioni e early return.
- Operazioni multi-entita chiuse in transazioni atomiche.
- Soft delete sui dati business dove richiesto.
- Audit log per operazioni critiche.
- Mass assignment prevention nei payload input.

### 7.2 Frontend

- `frontend/src/types/api.ts` come mirror contrattuale delle shape API.
- Query invalidation simmetrica sulle operazioni opposte.
- overview privacy-safe sulle pagine esposte o mostrate davanti al cliente.
- loading, empty e error state espliciti.

### 7.3 Vincoli prodotto

- Nessuna dipendenza cloud obbligatoria per il CRM core.
- Nessun path assoluto hardcoded.
- Dati business persistiti in `data/`.
- Feature AI additiva, non necessaria per la gestione base del gestionale.

---

## 8. Aree Critiche del Sistema

### 8.1 Finance path

Percorso critico:

`Contratti -> Rate -> Movimenti -> Dashboard/Workspace finance`

Qui devono restare sempre veri:

- importi coerenti
- pay/unpay reversibile
- chiusura/riapertura contratto simmetrica
- ledger e stato contratto non divergenti

### 8.2 Agenda path

Percorso critico:

`Agenda -> consumo crediti -> stato contratto -> workspace giornaliero`

Bug temporali o side effect frontend qui diventano subito problemi operativi reali.

### 8.3 Builder path

Percorso critico:

`Schede -> builder state -> save/duplicate/export`

La priorita non e' aggiungere UI, ma eliminare render-phase mutation, hook order violations e dirty-state intermittente.

---

## 9. Testing e Verifiche

### 9.1 Gate previsti

```powershell
venv\Scripts\ruff.exe check api tests
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- src
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build
python -m pytest -q tests
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run test
```

### 9.2 Baseline realmente verificata il 2026-03-10

- `ruff check api tests`: verde
- lint frontend globale: rosso (`29` errori, `57` warning)
- build frontend: compile OK, poi ambiente bloccato da `spawn EPERM`
- `pytest`: non affidabile per virtualenv locale misconfigurato

Conclusione: il repo non ha oggi un quality gate end-to-end ripetibile.

---

## 10. Debito Tecnico che puo bloccare il lancio

| Priorita | Tema | Rischio operativo |
|---|---|---|
| Critica | Hook order violations e side effect in render | comportamento React non deterministico sui flussi principali |
| Critica | Virtualenv locale rotto | suite backend non eseguibile in modo affidabile |
| Alta | Gate licenza disattivabile con avvio manuale | rischio commerciale e di supporto |
| Alta | Documentazione storicamente stale | runbook errati e perdita di tempo in pre-lancio |
| Media | Middleware Next deprecato | hardening auth meno robusto nel medio termine |
| Media | CORS limitato a subset di reti private | possibile fallimento LAN su reti `10.x` o `172.16-31.x` |
| Media | `core/` e repository legacy non critici ma presenti | superficie cognitiva troppo ampia durante hotfix |

---

## 11. Strategia Pre-Lancio a Microstep

Questa e' la sequenza raccomandata per arrivare a un prodotto "a prova di bomba" senza allargare scope inutilmente.

### Step 1 - Ripristino toolchain

Obiettivo:

- ricreare un virtualenv valido
- rendere eseguibili pytest e smoke script minimi
- fissare comandi ufficiali per PowerShell e per launcher prod

Exit criteria:

- `python -m pytest -q tests` eseguibile
- runbook README e CLAUDE coerenti con ambiente reale

### Step 2 - Chiusura errori frontend bloccanti

Obiettivo:

- portare `eslint src` a zero errori
- partire dai file con hook order e render-phase mutation

Priorita di attacco:

1. chart e widget shared
2. builder schede
3. guard/auth e route-sensitive component
4. warning ad alto rischio su stato/query

Exit criteria:

- nessun error-level lint in `frontend/src`
- nessun side effect nel render path dei flussi core

### Step 3 - Suite backend critica

Obiettivo:

- congelare una smoke suite minima ma autorevole sui domini che possono rompere il business

Target minimi:

- `tests/test_pay_rate.py`
- `tests/test_unpay_rate.py`
- `tests/test_workspace_today.py`
- `tests/test_dashboard_clinical_readiness.py`

Exit criteria:

- suite minima verde su ambiente locale ripetibile

### Step 4 - Regressione end-to-end dei flussi commerciali

Obiettivo:

- verificare i percorsi che l'utente pagante usa davvero

Checklist minima:

1. login -> dashboard -> workspace
2. crea cliente -> contratto -> rata -> pay/unpay
3. crea evento -> consumo crediti -> update contratto
4. backup -> mutate -> restore
5. apertura public portal anamnesi da rete esterna

Exit criteria:

- nessun blocco funzionale sui flussi core

### Step 5 - Rehearsal di distribuzione

Obiettivo:

- provare il prodotto come se fosse gia del cliente

Include:

- installer/launcher
- licenza
- DB reali e seed minimi
- LAN/Tailscale
- backup pre-update
- first run e setup

Exit criteria:

- installazione e avvio puliti su macchina "fredda"

### Step 6 - Freeze e rollback pack

Obiettivo:

- rendere il rilascio reversibile e governato

Deliverable:

- checklist release
- commit/branch di freeze
- backup di riferimento
- istruzioni rollback
- issue list post-launch classificata per severita

---

## 12. Verdetto Architetturale

Il progetto non richiede un big-bang rewrite.
Richiede disciplina da prodotto:

- meno numeri decorativi e piu runbook veri
- meno nuove feature e piu chiusura dei quality gate
- meno coupling implicito e piu determinismo su finance, agenda e builder

La direzione giusta non e' "costruire ancora".
La direzione giusta e' "ridurre le sorprese prima del go-live".

---

## 13. Riferimenti

- `README.md`: onboarding rapido e quality gate
- `CLAUDE.md`: regole, runbook e contesto di progetto esteso
- `AGENTS.md`: workflow microstep e doc sync policy
- `docs/upgrades/specs/UPG-2026-03-10-05-documentation-baseline-and-launch-readiness-plan.md`: piano operativo di hardening

*Questo documento sostituisce la vecchia fotografia basata su conteggi e LOC ormai obsoleti.*
