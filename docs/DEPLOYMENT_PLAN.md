# FitManager AI Studio — Piano di Distribuzione

> Piano approvato il 2026-03-01. Da eseguire quando il prodotto e' pronto per la vendita.

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

## Architettura Distribuzione

```
Source (Git privato — MAI esposto al cliente)
|
+-- api/                    <- PyInstaller -> api.exe (~50MB)
|   Include: FastAPI, SQLModel, uvicorn, bcrypt, jose
|   Esclude: torch, transformers, langchain (Phase 2 AI)
|
+-- frontend/               <- next build --standalone -> bundle (~30MB)
|   Include: Node.js minimal runtime
|   Output: .next/standalone/ + .next/static/
|   Source maps: MAI distribuite
|
+-- installer/              <- Inno Setup -> FitManager_Setup.exe
|   fitmanager.iss          Script installer Inno Setup
|   launcher.bat            Avvia api.exe + frontend
|   assets/                 Icone, testi, EULA
|
+-- tools/build/
    build-backend.sh        PyInstaller spec + esclusioni
    build-frontend.sh       next build standalone + copia
    build-installer.sh      Inno Setup compile
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

## Roadmap Implementativa

| Fase | Cosa | Effort | Priorita' |
|------|------|--------|-----------|
| 1 | Sistema licenza RSA + middleware FastAPI | 1-2 giorni | Alta |
| 2 | Next.js standalone output mode | 2-3 ore | Alta |
| 3 | PyInstaller spec per backend | 1 giorno | Alta |
| 4 | Launcher script (.bat -> avvia tutto) | 2-3 ore | Alta |
| 5 | Inno Setup installer | 1 giorno | Media |
| 6 | Script build automatizzato | mezzo giorno | Media |
| 7 | Setup Wizard primo avvio | 1 giorno | Media |
| 8 | Auto-updater | 2-3 giorni | Bassa (v2) |

---

## Prerequisiti Sviluppo (da fare PRIMA del build)

Queste modifiche al codice devono essere fatte durante lo sviluppo normale,
PRIMA di eseguire il piano di distribuzione:

1. **Setup Wizard**: pagina primo avvio (crea trainer senza seed script)
2. **License middleware**: controlla licenza su ogni API request
3. **JWT_SECRET auto-generation**: genera e salva al primo avvio
4. **Path relativi**: tutti i path relativi alla cartella installazione
5. **Escludere dipendenze AI pesanti**: torch/transformers non necessari per Phase 1
6. **Health check robusto**: endpoint /health con status licenza + DB + versione
7. **Pagina "Licenza Scaduta"**: UI dedicata con contatto supporto

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
