# FitManager AI Studio — Piano di Distribuzione

> Piano approvato il 2026-03-01. Da eseguire quando il prodotto e' pronto per la vendita.
> Runbook operativo di supporto e recovery: `docs/SUPPORT_RUNBOOK.md`.

---

## Strategia Scelta: Installer Nativo Windows + Licenza RSA

### Perche' NON Git
- Una volta clonato, il cliente ha tutto il sorgente — revocare accesso non cancella il clone
- Installazione da sorgente impossibile per un personal trainer
- "Blocco il Git" = minaccia vuota (il codice funziona gia' in locale)
- Immagine non professionale

### Perche' NON Docker
- Docker Desktop su Windows: WSL2, Hyper-V, 4GB RAM overhead
- Target = personal trainer, non sviluppatore
- Ollama GPU passthrough in Docker su Windows = problematico
- Revocare registry access non ferma immagini gia' pullate

### Perche' Installer Nativo
- Esperienza utente professionale (doppio click → installa)
- Zero dipendenze visibili (Python/Node embedded)
- Source code compilato (bytecode, non leggibile)
- Licenza RSA = leva reale di controllo
- Ollama nativo con GPU piena

---

## Release Candidate Preflight (2026-03-10)

Decisioni operative congelate prima del rebuild candidato:

1. **Source freeze**: commit `4a19bf2`.
2. **Versione candidata**: `1.0.0`, da riallineare in backend, frontend e installer.
3. **Policy bundle dati**:
   - `data/catalog.db` e' il catalogo canonico del prodotto, con i 391 esercizi attivi correnti;
   - `data/crm.db` nel bundle deve essere vuoto e first-run-safe.
4. **Dati reali cliente**: non entrano nell'installer. Lo stato reale di Chiara rientra solo tramite restore verificato del backup piu recente.
5. **Policy licenza**:
   - la chiave pubblica puo stare nel bundle;
   - la `license.key` del cliente NON deve vivere nel repository o in `installer/assets`;
   - la destinazione runtime resta `data/license.key` sulla macchina installata.

Questa sezione e' il contratto di base per ogni rebuild release candidate. Nessun installer nuovo va generato
se questi punti non sono gia stati riflessi nella documentazione operativa e nella checklist release.

---

## Architettura Distribuzione

```
Source (Git privato — MAI esposto al cliente)
|
+-- api/                    <- PyInstaller -> fitmanager.exe (102MB)
|   Include: FastAPI, SQLModel, uvicorn, bcrypt, jose
|   Esclude: torch, transformers, langchain (Phase 2 AI)
|
+-- frontend/               <- next build --standalone -> bundle (45MB)
|   Include: Node.js minimal runtime
|   Output: .next/standalone/ + .next/static/
|   Source maps: MAI distribuite
|
+-- installer/              <- Inno Setup -> FitManager_Setup.exe (83MB)
|   fitmanager.iss          Script installer Inno Setup
|   launcher.bat            Avvia backend + frontend + apre browser
|   assets/                 Icone, testi, EULA, license_public.pem
|
+-- tools/build/
    build-backend.sh        PyInstaller spec + esclusioni
    build-frontend.sh       next build standalone + copia
    build-media.sh          staging media esercizi per bundle
    (manuale) ISCC          compilazione Inno Setup reale via `installer/fitmanager.iss`
```

---

## Esperienza Cliente

```
1. Riceve link download (GitHub Release privato o sito web)
2. Scarica "FitManager_Setup_v1.2.exe" (~80MB)
3. Doppio click -> installer professionale
   +-----------------------------------+
   |  FitManager AI Studio             |
   |  Benvenuto nell'installazione     |
   |  [Avanti >]                       |
   +-----------------------------------+
4. Sceglie cartella (default: C:\FitManager)
5. Installer:
   - Copia binari (api.exe + frontend bundle)
   - Crea cartella dati (C:\FitManager\data\)
   - Crea shortcut desktop "FitManager"
   - Registra servizio Windows (opzionale)
   - Apre browser su localhost:3000
6. Primo avvio: Setup Wizard
   - Inserisci licenza (XXXX-XXXX-XXXX)
   - Crea account trainer (nome, email, password)
   - Configurazione iniziale (saldo cassa, etc.)
   - Dashboard
```

---

## Sistema di Licenza — Crittografia Asimmetrica RSA

### Flusso

```
SVILUPPATORE                              APPLICAZIONE
+-----------------------------+           +-----------------------------+
| Chiave privata RSA 2048     |           | Chiave pubblica (embedded)  |
| firma JWT:                  |           |                             |
| {                           |           | 1. Firma valida? (RSA)      |
|   "client_id": "gym-roma", |    --->   | 2. Scaduta?                 |
|   "expires": "2027-03-01", |           | 3. Tier permesso?           |
|   "tier": "pro",           |           | 4. Max clienti?             |
|   "max_clients": 50        |           |                             |
| }                           |           | NO = "Licenza non valida"   |
+-----------------------------+           +-----------------------------+
```

### Caratteristiche
- **Offline-first**: nessun phone-home, coerente con privacy-first
- **Non falsificabile**: senza chiave privata, nessuna licenza valida generabile
- **Flessibile**: piani diversi (basic 20 clienti, pro illimitati)
- **Leva reale**: licenza scade -> app mostra "Contatta supporto"

### Implementazione
- Chiave privata: `~/.fitmanager/private_key.pem` (solo sul PC sviluppatore)
- Chiave pubblica: embedded in `api/services/license.py`
- Middleware FastAPI: controlla licenza su ogni request (cache in memoria)
- CLI tool: `python -m tools.admin_scripts.generate_license --client "gym-roma" --tier pro --months 12`
- Storage licenza: `data/license.key` (file JWT nella cartella dati)
- La `license.key` del cliente non deve essere conservata nel repository, nei commit o in `installer/assets`

---

## Protezione IP — 4 Livelli

| Livello | Cosa protegge | Come |
|---------|--------------|------|
| PyInstaller | Python -> bytecode compilato | Non leggibile come sorgente |
| Next.js build | React -> JS minificato + webpack | Illeggibile senza source maps |
| Licenza RSA | Uso dell'app | Senza chiave privata = nessuna licenza |
| Git privato | Sorgente originale | Mai esposto al cliente |

---

## Gestione Aggiornamenti

### Fase 1 (MVP)
1. Build nuova versione
2. GitHub Release privato con .exe
3. Notifica cliente (email/WhatsApp)
4. Cliente scarica e reinstalla (dati preservati in data/)

### Fase 2 (Futuro)
- Auto-updater integrato (stile VS Code)
- App controlla GitHub API per nuove release
- Scarica e installa in background
- "Riavvia per aggiornare"

---

## Bundle Data Policy

### Catalogo scientifico

- `data/catalog.db` e' parte del prodotto distribuito.
- Deve essere coerente con il catalogo canonico del CRM e contenere i 391 esercizi attivi correnti
  (inclusi `stretching` e `avviamento`).
- Non deve dipendere da dati cliente o da contenuti business locali.

### Business DB

- `data/crm.db` nel bundle release candidate deve essere vuoto.
- Il prodotto deve restare avviabile al primo avvio tramite Setup Wizard anche senza restore.
- Dati reali, clienti, contratti, agenda, cassa, schede e media business rientrano solo tramite
  restore verificato del backup trainer.

### Verifica critica prima del pilot

Prima del pilot la release candidate deve superare questo flusso:

1. installazione pulita;
2. attivazione licenza;
3. avvio e verifica `Stato installazione`;
4. restore del backup reale di Chiara;
5. verifica presenza corretta di clienti, contratti, schede, agenda, cassa e media sensibili.

---

## Roadmap Implementativa

| Fase | Cosa | Effort | Priorita' | Status |
|------|------|--------|-----------|--------|
| 1a | License core backend (`api/services/license.py`) | 1 giorno | Alta | **DONE** — S1.1 |
| 1b | License middleware (enforcement HTTP) | mezzo giorno | Alta | **DONE** — S1.2 |
| 1c | License Generation CLI (`generate_license.py`) | mezzo giorno | Alta | **DONE** — S1.5 |
| 2 | JWT secret auto-generation al primo avvio | 2-3 ore | Alta | **DONE** — S1.3 |
| 3 | Health endpoint con stato licenza | 2-3 ore | Alta | **DONE** — S1.4 |
| 4 | Frontend license UX (pagina scadenza) | mezzo giorno | Alta | **DONE** — S1.6 |
| 5 | Setup Wizard primo avvio | 1 giorno | Alta | **DONE** — S2.1 |
| 6 | Next.js standalone output mode | 2-3 ore | Alta | **DONE** — S3.1 |
| 7 | PyInstaller spec per backend | 1 giorno | Alta | **DONE** — S3.2 |
| 8 | Launcher script (.bat -> avvia tutto) | 2-3 ore | Alta | **DONE** — S3.3 |
| 9 | Inno Setup installer | 1 giorno | Media | **DONE** — S3.3 |
| 10 | Auto-updater | 2-3 giorni | Bassa (v2) | — |

Tracking dettagliato: `docs/upgrades/specs/UPG-2026-03-04-06-launch-market-readiness-roadmap.md`

---

## Prerequisiti Sviluppo (da fare PRIMA del build)

Queste modifiche al codice devono essere fatte durante lo sviluppo normale,
PRIMA di eseguire il piano di distribuzione:

1. ~~**License middleware**~~: controlla licenza su ogni API request — **DONE** (S1.1 + S1.2)
2. ~~**License Generation CLI**~~: script per generare keypair + firmare token — **DONE** (S1.5)
3. ~~**JWT_SECRET auto-generation**~~: genera e salva al primo avvio — **DONE** (S1.3)
4. ~~**Health check robusto**~~: endpoint /health con status licenza + DB + versione — **DONE** (S1.4)
5. ~~**Pagina "Licenza Scaduta"**~~: UI dedicata con contatto supporto — **DONE** (S1.6)
6. ~~**Setup Wizard**~~: pagina primo avvio (crea trainer senza seed script) — **DONE** (S2.1)
7. **Path relativi**: tutti i path relativi alla cartella installazione — GIA' FATTO (CLAUDE.md enforced)
8. **Escludere dipendenze AI pesanti**: torch/transformers non necessari per Phase 1 — GIA' FATTO (import condizionali)

---

## Note Architetturali

- Il sistema di licenza e' l'UNICA leva di controllo reale
- Git privato e PyInstaller sono protezioni aggiuntive, non primarie
- La chiave privata RSA e' il segreto piu' importante — backup sicuro obbligatorio
- SQLite e' perfetto per installazioni single-user locali
- Ollama resta installazione separata (ha il suo installer ufficiale)
- Il frontend scopre l'API via porta (3000->8000) — funziona senza configurazione

---

*Questo piano e' definitivo. Da eseguire quando lo sviluppo raggiunge la maturita' per la vendita.*
