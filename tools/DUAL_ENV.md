# Dual Environment — Runbook Operativo

> Procedura blindata per gestire PROD (Chiara) e DEV (sviluppo) in parallelo.
> Questo documento e' la legge operativa. Seguilo alla lettera.
> **Tutti i comandi sono PowerShell** — copia-incollabili nel terminale VS Code.

---

## Mappa Ambienti

```
╔══════════════════════════════════════════════════════════════════╗
║                         PRODUZIONE                              ║
║  Utente:    Chiara                                              ║
║  Backend:   porta 8000  →  data/crm.db (dati REALI)            ║
║  Frontend:  porta 3000  →  next start (production mode)         ║
║  Accesso:   LAN  → http://192.168.1.23:3000 (casa, stesso WiFi)║
║             VPN  → http://100.127.28.16:3000 (Tailscale, ovunque)
║  API URL:   DINAMICO — dedotto da window.location (zero .env)   ║
║  DB:        13 clienti reali — MAI toccare con seed/reset       ║
╠══════════════════════════════════════════════════════════════════╣
║                          SVILUPPO                               ║
║  Utente:    gvera (http://localhost:3001)                       ║
║  Backend:   porta 8001  →  data/crm_dev.db (dati test)         ║
║  Frontend:  porta 3001  →  next dev (hot reload)                ║
║  API URL:   DINAMICO — localhost:3001 → localhost:8001          ║
║  DB:        ~50 clienti test — libero per seed/reset/esperimenti║
╚══════════════════════════════════════════════════════════════════╝

Rete Tailscale (VPN P2P — WireGuard):
  PC gvera:     100.127.28.16
  iPad Chiara:  connessa allo stesso account Tailscale
  Chiara accede da QUALSIASI rete (lavoro, 4G, ecc.)
```

---

## Regola #0 — Le Tre Regole d'Oro

> **1. PROD usa `next start`. DEV usa `next dev`. Mai il contrario.**

Perche':
- `next dev` carica `.env.development.local` (priorita' > `.env.local`) → punta a 8001
- `next start` ignora `.env.development.local` → usa `.env.local` → punta a 8000
- Se usi `next dev` su porta 3000, Chiara vedra' i dati di crm_dev.db

> **2. Backend SEMPRE con `--host 0.0.0.0`. Mai senza.**

Perche':
- Senza `--host 0.0.0.0`, uvicorn ascolta SOLO su `127.0.0.1` (localhost)
- Il frontend di Chiara chiama `http://192.168.1.23:8000` (IP LAN)
- Se il backend non ascolta su LAN → **tutte le pagine danno errore da remoto**
- Da locale (`localhost:3000`) sembra funzionare, ma da remoto no → trappola insidiosa

```powershell
# SBAGLIATO — ascolta solo su localhost:
uvicorn api.main:app --reload --port 8000

# CORRETTO — ascolta su tutte le interfacce (localhost + LAN + Tailscale):
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

> **2b. Frontend PROD SEMPRE con `-H 0.0.0.0`. Mai senza.**

Stessa identica trappola del backend:
- Senza `-H 0.0.0.0`, `next start` ascolta SOLO su `127.0.0.1` (localhost)
- iPad/Tailscale (`100.x.x.x`) riceve "Application error: a client-side exception has occurred"
- Da locale (`localhost:3000`) sembra funzionare perfettamente → la trappola e' invisibile
- Il flag e' gia' nello script `npm run prod` (`next start -p 3000 -H 0.0.0.0`)

```powershell
# SBAGLIATO — ascolta solo su localhost:
next start -p 3000

# CORRETTO — ascolta su tutte le interfacce:
next start -p 3000 -H 0.0.0.0

# Oppure semplicemente:
npm run prod    # include gia' -H 0.0.0.0
```

> **3. MAI chiudere backend con Ctrl+C o chiusura terminale. Usare SEMPRE la procedura kill.**

Perche':
- Su Windows, chiudere il terminale uccide solo il master uvicorn
- I worker figli (multiprocessing.spawn) restano vivi sulla porta
- Servono **codice vecchio** → il frontend mostra dati corrotti (NaN, campi mancanti)
- `netstat` mostra il PID del padre (morto), ma il figlio zombie ha un PID diverso
- `taskkill /F /PID <padre>` dice "non trovato" → devi cercare i figli orfani

**Procedura kill completa (PowerShell):**
```powershell
# ──────────────────────────────────────────────
# KILL COMPLETO SU UNA PORTA (es. 8000)
# ──────────────────────────────────────────────

# 1. Trova PID sulla porta
netstat -ano | Select-String ":8000.*LISTEN"

# 2. Killa con tree-kill (padre + figli)
taskkill /T /F /PID <numero>

# 3. Se dice "non trovato" → il padre e' morto, ma i figli zombie sono vivi.
#    Cerca i figli orfani del PID morto:
Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq <numero> }

# 4. Se trova processi (tipicamente python3.12.exe con multiprocessing.spawn),
#    killa ogni figlio:
Stop-Process -Id <pid_figlio> -Force

# 5. Verifica che la porta sia libera:
netstat -ano | Select-String ":8000.*LISTEN"
# Se output vuoto → porta libera → puoi avviare
```

**Shortcut nucleare** — se non sai il PID e vuoi killare tutto:
```powershell
# Killa TUTTI i processi Python (ATTENZIONE: killa anche Jupyter, script, ecc.)
Get-Process python* | Stop-Process -Force

# Killa TUTTI i processi Node (ATTENZIONE: killa anche VS Code extensions)
Get-Process node* | Stop-Process -Force
```

---

## Procedura 1 — Avvio Completo da Zero

Esegui in 4 terminali PowerShell separati (ordine: backend prima, frontend dopo).

### Terminale 1: Backend PROD
```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
> Usa crm.db (default da config.py). NO `--reload` in prod (opzionale).

### Terminale 2: Backend DEV
```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```
> `--reload` per hot reload codice. `$env:DATABASE_URL` override per crm_dev.db.

### Terminale 3: Frontend PROD
```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run build
npm run prod
```
> `npm run prod` = `next start -p 3000 -H 0.0.0.0`. Richiede build preventivo.
> Il flag `-H 0.0.0.0` e' CRITICO: senza, iPad/Tailscale non funzionano.

### Terminale 4: Frontend DEV
```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run dev
```
> `npm run dev` = `next dev -p 3001`. Hot reload automatico.

### Verifica (dopo avvio) — TUTTI i check devono passare
```powershell
# Backend PROD (localhost)
curl.exe http://localhost:8000/health

# Backend PROD (LAN — CRITICO! Se fallisce, Chiara non funziona)
curl.exe http://192.168.1.23:8000/health

# Backend DEV
curl.exe http://localhost:8001/health

# Frontend PROD (da browser)
# → http://192.168.1.23:3000 (Chiara) o http://localhost:3000 (locale)

# Frontend DEV (da browser)
# → http://localhost:3001
```
> Se il check LAN fallisce ma localhost funziona → hai dimenticato `--host 0.0.0.0`

---

## Procedura 2 — Sviluppo Normale (Ciclo Quotidiano)

### Scenario: ho modificato codice Python (backend)

```
1. Backend DEV (porta 8001): --reload attivo → ricarica automatico ✓
2. Backend PROD (porta 8000):
   - Se ha --reload → ricarica automatico ✓
   - Se NO --reload → restart manuale (vedi sotto)
3. Testa su http://localhost:3001 (DEV)
4. Se OK, verifica anche http://localhost:3000 (PROD)
```

**Restart manuale backend PROD:**
```powershell
# Kill vecchio processo sulla 8000
netstat -ano | Select-String ":8000.*LISTEN"
taskkill /T /F /PID <numero>

# Riavvia
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Restart manuale backend DEV:**
```powershell
# Kill vecchio processo sulla 8001
netstat -ano | Select-String ":8001.*LISTEN"
taskkill /T /F /PID <numero>

# Riavvia con DB dev
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

### Scenario: ho modificato codice frontend (React/TypeScript)

```
1. Frontend DEV (porta 3001): next dev → hot reload automatico ✓
2. Frontend PROD (porta 3000): next start → serve build pre-compilato
   → Le modifiche NON appaiono finche' non fai rebuild (vedi sotto)
3. Testa su http://localhost:3001 (DEV) — immediato
4. Dopo build, verifica http://localhost:3000 (PROD)
```

**Rebuild + restart frontend PROD:**
```powershell
# 1. Build nuova versione
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run build

# 2. Trova e killa il processo sulla porta 3000
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>

# 3. Riavvia frontend PROD
npm run prod
```

### Scenario: ho creato una migrazione Alembic (schema DB)

```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio

# 1. Crea la migrazione
alembic revision -m "descrizione_migrazione"

# 2. Applica a PROD (crm.db)
$env:DATABASE_URL = "sqlite:///data/crm.db"
alembic upgrade head

# 3. Applica a DEV (crm_dev.db)
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"
alembic upgrade head

# 4. Verifica allineamento
$env:DATABASE_URL = "sqlite:///data/crm.db"; alembic current
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"; alembic current
# Le versioni devono essere identiche!

# 5. Restart entrambi i backend (se necessario — se hanno --reload, basta)
```
> MAI fare `alembic upgrade head` da solo senza specificare il DB — applica solo al default!

### Scenario: ho modificato tipi TypeScript + schema Pydantic

```
1. Aggiorna api/schemas/ (Pydantic) — backend
2. Aggiorna frontend/src/types/api.ts (TypeScript) — frontend
3. Backend DEV ricarica da solo (--reload)
4. Frontend DEV ricarica da solo (next dev)
5. Per PROD: rebuild + restart frontend (vedi sotto)
```

**Rebuild frontend PROD:**
```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run build
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>
npm run prod
```

---

## Procedura 3 — Propagare Tutto a PROD (Deploy Completo)

Dopo una sessione di sviluppo, per allineare PROD:

```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio

# 1. Migrazioni DB (se ce ne sono)
$env:DATABASE_URL = "sqlite:///data/crm.db"; alembic upgrade head
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"; alembic upgrade head

# 2. Restart backend PROD (se hai modificato Python)
netstat -ano | Select-String ":8000.*LISTEN"
taskkill /T /F /PID <numero>
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 3. Rebuild + restart frontend PROD (se hai modificato React)
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run build
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>
npm run prod

# 4. Verifica
curl.exe http://localhost:8000/health              # backend risponde
curl.exe http://192.168.1.23:8000/health           # backend risponde da LAN
curl.exe http://localhost:3000                      # frontend risponde
# Browser: http://192.168.1.23:3000 → login → verifica pagina modificata
```

---

## Procedura 4 — Troubleshooting

### Problema: Backend non riflette le modifiche al codice

**Causa**: Zombie uvicorn worker (solo Windows).
`Ctrl+C` uccide il master ma i worker figli restano vivi con il socket aperto.

```powershell
# 1. Trova il PID sulla porta
netstat -ano | Select-String ":8000.*LISTEN"

# 2. Killa con tree-kill
taskkill /T /F /PID <numero>

# 3. Se "non trovato", cerca figli orfani
Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq <numero> }

# 4. Killa ogni figlio trovato
Stop-Process -Id <pid_figlio> -Force

# 5. Riavvia backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verifica**: il health check deve restituire `{"status":"ok"}`:
```powershell
curl.exe http://localhost:8000/health
```

### Problema: Frontend PROD non mostra le modifiche

**Causa**: `next start` serve la build pre-compilata. Non fa hot reload.

```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend

# Rebuild
npm run build

# Kill vecchio frontend
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>

# Riavvia
npm run prod
```

### Problema: Chiara vede dati sbagliati (crm_dev.db invece di crm.db)

**Causa**: Frontend PROD avviato con `next dev` invece di `next start`.
`next dev` carica `.env.development.local` → punta a porta 8001 → crm_dev.db.

```powershell
# Kill frontend errato
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>

# Riavvia correttamente con next start
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run build
npm run prod
```

**Verifica**: controlla quanti clienti vede Chiara.
- crm.db = ~13 clienti (dati reali)
- crm_dev.db = ~50 clienti (dati test)

### Problema: Due processi sulla stessa porta

**Causa**: Avviato un nuovo processo senza killare il vecchio.
`localhost:PORTA` puo' colpire un processo, `192.168.1.23:PORTA` l'altro.

```powershell
# Trova TUTTI i processi sulla porta
netstat -ano | Select-String ":8000.*LISTEN"

# Killa ognuno (possono essere piu' PID)
taskkill /T /F /PID <pid1>
taskkill /T /F /PID <pid2>

# Verifica che la porta sia libera (nessun output = OK):
netstat -ano | Select-String ":8000.*LISTEN"
```

### Problema: Tutte le pagine danno errore da remoto, ma da locale funziona

**Causa 1 — Backend**: avviato senza `--host 0.0.0.0`.
Senza questo flag, uvicorn ascolta SOLO su `127.0.0.1` (localhost).
Il frontend PROD chiama `http://192.168.1.23:8000` (IP LAN) → connessione rifiutata.

```powershell
# Verifica backend:
curl.exe http://localhost:8000/health          # OK (localhost)
curl.exe http://192.168.1.23:8000/health       # FAIL (LAN) ← problema qui

# Soluzione: kill + restart con --host 0.0.0.0
netstat -ano | Select-String ":8000.*LISTEN"
taskkill /T /F /PID <numero>
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Causa 2 — Frontend**: avviato senza `-H 0.0.0.0`.
Stessa identica trappola: `next start` ascolta solo su localhost.
iPad/Tailscale riceve "Application error: a client-side exception has occurred".

```powershell
# Verifica frontend (da browser):
# http://localhost:3000       → OK (funziona)
# http://100.127.28.16:3000   → FAIL ("Application error") ← problema qui

# Soluzione: kill + restart con -H 0.0.0.0
netstat -ano | Select-String ":3000.*LISTEN"
taskkill /T /F /PID <numero>
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend
npm run prod    # include gia' -H 0.0.0.0
```

**Trappola**: Questo errore e' invisibile da locale. Tutto sembra funzionare
su `localhost`, ma Chiara da LAN/Tailscale vede solo errori. Colpisce sia backend che frontend.

### Problema: KPI mostrano NaN

**Causa**: Worker zombie uvicorn che serve codice vecchio (senza campi KPI).
Il frontend riceve una risposta senza `kpi_attivi`, `kpi_fatturato`, ecc.
`formatCurrency(undefined)` → NaN.

```powershell
# Kill zombie + restart con codice aggiornato
netstat -ano | Select-String ":8000.*LISTEN"
taskkill /T /F /PID <numero>

# Se "non trovato":
Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq <numero> }
Stop-Process -Id <pid_figlio> -Force

# Riavvia
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Nota**: Il codice ha ora il guard `?? 0` su tutti i KPI, ma il vero fix
e' sempre eliminare lo zombie e riavviare con codice aggiornato.

### Problema: `alembic upgrade head` applicato a un solo DB

**Causa**: Hai usato `alembic upgrade head` senza specificare il DB (applica solo al default).

```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio

# Verifica disallineamento:
$env:DATABASE_URL = "sqlite:///data/crm.db"; alembic current
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"; alembic current

# Se versioni diverse → riallinea:
$env:DATABASE_URL = "sqlite:///data/crm.db"; alembic upgrade head
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"; alembic upgrade head
```

### Problema: Build frontend fallisce (errori TypeScript)

**Causa**: Tipo TypeScript non allineato con schema Pydantic.

```powershell
cd C:\Users\gvera\Projects\FitManager_AI_Studio\frontend

# 1. Identifica l'errore
npx next build

# 2. Fix: allinea types/api.ts con api/schemas/
# 3. Rebuild
npm run build
```

---

## Ricetta Rapida — Kill Zombie (copia-incolla)

Questa e' la sequenza completa per quando un processo non muore:

```powershell
# ═══════════════════════════════════════════════════
# RICETTA: KILL ZOMBIE UVICORN (porta 8000 o 8001)
# ═══════════════════════════════════════════════════

# Sostituisci 8000 con la porta desiderata
$porta = 8000

# Step 1: Trova PID
netstat -ano | Select-String ":${porta}.*LISTEN"

# Step 2: Prova tree-kill (copia il numero dal risultato sopra)
# taskkill /T /F /PID <numero>

# Step 3: Se "non trovato", cerca orfani
# Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq <numero> }

# Step 4: Killa i figli trovati
# Stop-Process -Id <pid_figlio> -Force

# Step 5: Verifica porta libera
netstat -ano | Select-String ":${porta}.*LISTEN"

# ═══════════════════════════════════════════════════
# OPZIONE NUCLEARE: se niente funziona
# ═══════════════════════════════════════════════════
# Killa TUTTI i Python sulla macchina:
# Get-Process python* | Stop-Process -Force
```

---

## Checklist Pre-Commit

Prima di ogni commit, verifica:

```
[ ] npx next build — zero errori TypeScript
[ ] Backend DEV risponde: curl.exe http://localhost:8001/health
[ ] Frontend DEV funziona: http://localhost:3001 (login + pagina modificata)
[ ] Se migrazione: alembic upgrade head su ENTRAMBI i DB
[ ] Se modifica backend: PROD testato su http://localhost:8000/health
[ ] Se modifica frontend: PROD rebuild + test su http://localhost:3000
```

---

## Checklist Fine Sessione (Deploy a Chiara)

Prima di chiudere la sessione di sviluppo:

```
[ ] Commit + push effettuato
[ ] Migrazioni applicate a entrambi i DB
[ ] Backend PROD (8000) attivo CON --host 0.0.0.0
[ ] curl.exe http://192.168.1.23:8000/health → OK (check LAN)
[ ] curl.exe http://100.127.28.16:8000/health → OK (check Tailscale)
[ ] Frontend PROD (3000) attivo CON -H 0.0.0.0 (npm run prod, NON next dev!)
[ ] http://192.168.1.23:3000 → login (check LAN — se fallisce: manca -H 0.0.0.0)
[ ] http://100.127.28.16:3000 → login (check Tailscale — se fallisce: manca -H 0.0.0.0)
[ ] Verifica: numero clienti corretto (~13, non ~50)
[ ] Tailscale attivo sul PC (icona tray connessa)
```

---

## Accesso Remoto — Tailscale

Chiara accede all'app da **qualsiasi rete** (lavoro, 4G, casa) tramite Tailscale VPN.

```
PC gvera (server):    100.127.28.16     — Tailscale sempre attivo
iPad Chiara (client): stesso account Tailscale

Chiara apre: http://100.127.28.16:3000
```

**Come funziona**:
- Tailscale crea una rete P2P crittografata (WireGuard) tra PC e iPad
- I dati NON passano per server terzi — solo coordinamento iniziale
- L'app e' accessibile come se fossero sulla stessa LAN
- Il frontend deduce l'API URL dinamicamente (`100.127.28.16:3000 → 100.127.28.16:8000`)

**Prerequisiti**:
- Tailscale installato e connesso sul PC (icona tray verde)
- Tailscale installato e connesso sull'iPad (stesso account)
- Backend avviato con `--host 0.0.0.0` (ascolta su tutte le interfacce)
- Frontend avviato con `-H 0.0.0.0` (`npm run prod` lo include gia')

**Troubleshooting**:
- Chiara non vede la pagina → verificare che Tailscale sia attivo su ENTRAMBI i dispositivi
- "Connessione non riuscita" → l'iPad non ha Tailscale connesso, oppure il backend non ha `--host 0.0.0.0`
- "Application error: client-side exception" → frontend avviato senza `-H 0.0.0.0` (usare `npm run prod`)
- Pagina si vede ma dati non caricano → CORS non accetta l'IP Tailscale (verificare regex in `api/main.py`)

---

## API URL Dinamico

Il frontend **NON** ha piu' un API URL hardcodato. Lo deduce dal browser:

```
Browser apre                    →  API chiama
http://192.168.1.23:3000       →  http://192.168.1.23:8000/api   (LAN)
http://100.127.28.16:3000      →  http://100.127.28.16:8000/api  (Tailscale)
http://localhost:3001           →  http://localhost:8001/api       (dev)
```

Logica in `frontend/src/lib/api-client.ts` → `getApiBaseUrl()`:
- Porta 3001 → backend 8001 (dev)
- Qualsiasi altra porta → backend 8000 (prod)

**I file `.env.local` e `.env.development.local` restano come fallback SSR ma non sono piu' critici.**

---

## File di Configurazione — Riferimento Rapido

| File | Scopo | Toccare? |
|------|-------|----------|
| `frontend/src/lib/api-client.ts` | API URL dinamico (`getApiBaseUrl()`) | Solo se cambia mapping porte |
| `api/main.py` | CORS regex (localhost + LAN + Tailscale) | Solo se nuova rete |
| `frontend/.env.local` | Fallback SSR PROD | Non piu' critico (URL dinamico) |
| `frontend/.env.development.local` | Fallback SSR DEV | Non piu' critico (URL dinamico) |
| `frontend/package.json` | Script: `dev`→3001, `prod`→3000 `-H 0.0.0.0` | MAI (gia' corretto) |
| `api/config.py` | `DATABASE_URL` default = crm.db | MAI (override via env var) |
| `tools/scripts/kill-port.sh` | Kill tree (usato da Claude Code bash) | Solo se bug Windows |
| `tools/scripts/restart-backend.sh` | Kill + restart (usato da Claude Code bash) | Solo se bug |
| `tools/scripts/migrate-all.sh` | Alembic su entrambi i DB (usato da Claude Code bash) | Solo se bug |

> **Nota**: Gli script `.sh` nella cartella `tools/scripts/` sono usati da Claude Code
> (che ha una shell bash interna). Per operazioni manuali dal terminale VS Code,
> usa i comandi PowerShell documentati sopra.

---

## Credenziali

| Ambiente | Email | Password |
|----------|-------|----------|
| PROD (crm.db) | chiarabassani96@gmail.com | chiarabassani |
| DEV (crm_dev.db) | chiarabassani96@gmail.com | Fitness2026! |

---

*Ultimo aggiornamento: 24 Febbraio 2026*
*Segui questo runbook. Se qualcosa non funziona, leggi la sezione Troubleshooting prima di improvvisare.*
