# Dual Environment — Runbook Operativo

> Procedura blindata per gestire PROD (Chiara) e DEV (sviluppo) in parallelo.
> Questo documento e' la legge operativa. Seguilo alla lettera.

---

## Mappa Ambienti

```
╔══════════════════════════════════════════════════════════════════╗
║                         PRODUZIONE                              ║
║  Utente:    Chiara (http://192.168.1.23:3000)                   ║
║  Backend:   porta 8000  →  data/crm.db (dati REALI)            ║
║  Frontend:  porta 3000  →  next start (production mode)         ║
║  Env:       .env.local  →  API_URL = http://192.168.1.23:8000   ║
║  DB:        13 clienti reali — MAI toccare con seed/reset       ║
╠══════════════════════════════════════════════════════════════════╣
║                          SVILUPPO                               ║
║  Utente:    gvera (http://localhost:3001)                       ║
║  Backend:   porta 8001  →  data/crm_dev.db (dati test)         ║
║  Frontend:  porta 3001  →  next dev (hot reload)                ║
║  Env:       .env.development.local → API_URL = localhost:8001   ║
║  DB:        ~50 clienti test — libero per seed/reset/esperimenti║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Regola #0 — Il Principio Fondamentale

> **PROD usa `next start`. DEV usa `next dev`. Mai il contrario.**

Perche':
- `next dev` carica `.env.development.local` (priorita' > `.env.local`) → punta a 8001
- `next start` ignora `.env.development.local` → usa `.env.local` → punta a 8000
- Se usi `next dev` su porta 3000, Chiara vedra' i dati di crm_dev.db

---

## Procedura 1 — Avvio Completo da Zero

Esegui in 4 terminali separati (ordine: backend prima, frontend dopo).

### Terminale 1: Backend PROD
```bash
cd /c/Users/gvera/Projects/FitManager_AI_Studio
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
> Usa crm.db (default da config.py). NO `--reload` in prod (opzionale).

### Terminale 2: Backend DEV
```bash
cd /c/Users/gvera/Projects/FitManager_AI_Studio
DATABASE_URL=sqlite:///data/crm_dev.db uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```
> `--reload` per hot reload codice. `DATABASE_URL` override per crm_dev.db.

### Terminale 3: Frontend PROD
```bash
cd /c/Users/gvera/Projects/FitManager_AI_Studio/frontend
npm run build && npm run prod
```
> `npm run prod` = `next start -p 3000`. Richiede build preventivo.

### Terminale 4: Frontend DEV
```bash
cd /c/Users/gvera/Projects/FitManager_AI_Studio/frontend
npm run dev
```
> `npm run dev` = `next dev -p 3001`. Hot reload automatico.

### Verifica (dopo avvio)
```bash
# Backend PROD
curl http://localhost:8000/health
# Backend DEV
curl http://localhost:8001/health
# Frontend PROD (da browser)
# → http://192.168.1.23:3000 (Chiara) o http://localhost:3000 (locale)
# Frontend DEV (da browser)
# → http://localhost:3001
```

---

## Procedura 2 — Sviluppo Normale (Ciclo Quotidiano)

### Scenario: ho modificato codice Python (backend)

```
1. Backend DEV (porta 8001): --reload attivo → ricarica automatico ✓
2. Backend PROD (porta 8000):
   - Se ha --reload → ricarica automatico ✓
   - Se NO --reload → restart manuale:
     bash tools/scripts/restart-backend.sh prod
3. Testa su http://localhost:3001 (DEV)
4. Se OK, verifica anche http://localhost:3000 (PROD)
```

### Scenario: ho modificato codice frontend (React/TypeScript)

```
1. Frontend DEV (porta 3001): next dev → hot reload automatico ✓
2. Frontend PROD (porta 3000): next start → serve build pre-compilato
   → Le modifiche NON appaiono finche' non fai:
     cd frontend && npm run build
   → Poi restart frontend prod:
     # Kill il processo su porta 3000
     bash tools/scripts/kill-port.sh 3000
     # Avvia next start
     cd frontend && npm run prod
3. Testa su http://localhost:3001 (DEV) — immediato
4. Dopo build, verifica http://localhost:3000 (PROD)
```

### Scenario: ho creato una migrazione Alembic (schema DB)

```
1. Crea la migrazione:
   alembic revision -m "descrizione_migrazione"

2. Applica a ENTRAMBI i DB:
   bash tools/scripts/migrate-all.sh

3. MAI fare `alembic upgrade head` da solo — applica solo a un DB!

4. Restart entrambi i backend:
   bash tools/scripts/restart-backend.sh dev
   bash tools/scripts/restart-backend.sh prod
```

### Scenario: ho modificato tipi TypeScript + schema Pydantic

```
1. Aggiorna api/schemas/ (Pydantic) — backend
2. Aggiorna frontend/src/types/api.ts (TypeScript) — frontend
3. Backend DEV ricarica da solo (--reload)
4. Frontend DEV ricarica da solo (next dev)
5. Per PROD: build + restart frontend
   cd frontend && npm run build
   bash tools/scripts/kill-port.sh 3000
   cd frontend && npm run prod
```

---

## Procedura 3 — Propagare Tutto a PROD (Deploy Completo)

Dopo una sessione di sviluppo, per allineare PROD:

```bash
# 1. Migrazioni DB (se ce ne sono)
bash tools/scripts/migrate-all.sh

# 2. Restart backend PROD (se hai modificato Python)
bash tools/scripts/restart-backend.sh prod

# 3. Rebuild + restart frontend PROD (se hai modificato React)
cd frontend && npm run build
bash tools/scripts/kill-port.sh 3000
cd frontend && npm run prod

# 4. Verifica
curl http://localhost:8000/health              # backend risponde
curl http://localhost:3000                      # frontend risponde
# Browser: http://192.168.1.23:3000 → login → verifica pagina modificata
```

---

## Procedura 4 — Troubleshooting

### Problema: Backend non riflette le modifiche al codice

**Causa**: Zombie uvicorn worker (solo Windows).
`Ctrl+C` uccide il master ma i worker figli restano vivi con il socket aperto.

```bash
# Soluzione: kill pulito + restart
bash tools/scripts/kill-port.sh 8000   # o 8001
bash tools/scripts/restart-backend.sh prod  # o dev
```

**Verifica**: il health check deve restituire `{"status":"ok"}`:
```bash
curl http://localhost:8000/health
```

### Problema: Frontend PROD non mostra le modifiche

**Causa**: `next start` serve la build pre-compilata. Non fa hot reload.

```bash
# Soluzione: rebuild
cd frontend && npm run build
bash tools/scripts/kill-port.sh 3000
cd frontend && npm run prod
```

### Problema: Chiara vede dati sbagliati (crm_dev.db invece di crm.db)

**Causa**: Frontend PROD avviato con `next dev` invece di `next start`.
`next dev` carica `.env.development.local` → punta a porta 8001 → crm_dev.db.

```bash
# Soluzione: kill e riavvia con next start
bash tools/scripts/kill-port.sh 3000
cd frontend && npm run build && npm run prod
```

**Verifica**: controlla quanti clienti vede Chiara.
- crm.db = ~13 clienti (dati reali)
- crm_dev.db = ~50 clienti (dati test)

### Problema: Due processi sulla stessa porta

**Causa**: Avviato un nuovo processo senza killare il vecchio.
`localhost:PORTA` puo' colpire un processo, `192.168.1.23:PORTA` l'altro.

```bash
# Soluzione: kill totale + restart pulito
bash tools/scripts/kill-port.sh 8000
# Verifica che la porta sia libera:
netstat -ano | grep ":8000.*LISTEN"
# Se output vuoto → porta libera → avvia
```

### Problema: `alembic upgrade head` applicato a un solo DB

**Causa**: Hai usato `alembic upgrade head` senza script (applica solo al DB di default).

```bash
# Verifica disallineamento:
DATABASE_URL=sqlite:///data/crm.db alembic current
DATABASE_URL=sqlite:///data/crm_dev.db alembic current
# Se versioni diverse → riallinea:
bash tools/scripts/migrate-all.sh
```

### Problema: Build frontend fallisce (errori TypeScript)

**Causa**: Tipo TypeScript non allineato con schema Pydantic.

```bash
# 1. Identifica l'errore
cd frontend && npx next build 2>&1 | head -50

# 2. Fix: allinea types/api.ts con api/schemas/
# 3. Rebuild
cd frontend && npm run build
```

---

## Checklist Pre-Commit

Prima di ogni commit, verifica:

```
[ ] npx next build — zero errori TypeScript
[ ] Backend DEV risponde: curl http://localhost:8001/health
[ ] Frontend DEV funziona: http://localhost:3001 (login + pagina modificata)
[ ] Se migrazione: bash tools/scripts/migrate-all.sh eseguito
[ ] Se modifica backend: PROD testato su http://localhost:8000/health
[ ] Se modifica frontend: PROD rebuild + test su http://localhost:3000
```

---

## Checklist Fine Sessione (Deploy a Chiara)

Prima di chiudere la sessione di sviluppo:

```
[ ] Commit + push effettuato
[ ] Migrazioni applicate a entrambi i DB
[ ] Backend PROD (8000) attivo con codice aggiornato
[ ] Frontend PROD (3000) attivo con build aggiornato (next start, NON next dev!)
[ ] Chiara puo' accedere a http://192.168.1.23:3000 e lavorare
[ ] Verifica: numero clienti corretto (~13, non ~50)
```

---

## File di Configurazione — Riferimento Rapido

| File | Scopo | Toccare? |
|------|-------|----------|
| `frontend/.env.local` | API URL per PROD (`192.168.1.23:8000`) | MAI (gia' corretto) |
| `frontend/.env.development.local` | API URL per DEV (`localhost:8001`) | MAI (gia' corretto) |
| `frontend/package.json` | Script: `dev`→3001, `prod`→3000 | MAI (gia' corretto) |
| `frontend/next.config.ts` | `distDir` configurabile via env | Solo se serve cache separata |
| `api/config.py` | `DATABASE_URL` default = crm.db | MAI (override via env var) |
| `tools/scripts/kill-port.sh` | Kill tree di processi su porta | Solo se bug Windows |
| `tools/scripts/restart-backend.sh` | Kill + restart backend | Solo se bug |
| `tools/scripts/migrate-all.sh` | Alembic su entrambi i DB | Solo se bug |

---

## Credenziali

| Ambiente | Email | Password |
|----------|-------|----------|
| PROD (crm.db) | chiarabassani96@gmail.com | chiarabassani |
| DEV (crm_dev.db) | chiarabassani96@gmail.com | Fitness2026! |

---

*Ultimo aggiornamento: 24 Febbraio 2026*
*Segui questo runbook. Se qualcosa non funziona, leggi la sezione Troubleshooting prima di improvvisare.*
