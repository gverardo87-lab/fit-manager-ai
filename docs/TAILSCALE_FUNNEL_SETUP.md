# Tailscale Funnel — Setup e Guida Operativa

> **Documento di riferimento per installazione, configurazione e troubleshooting
> di Tailscale Funnel su FitManager AI Studio.**
> Destinato sia allo sviluppatore che all'installatore sui PC dei clienti chinesiologi.

---

## Cos'e' Tailscale Funnel

Tailscale Funnel espone un servizio locale su internet pubblico con HTTPS automatico.
Il cliente finale (es. paziente del chinesiologo) clicca un link nel browser del telefono
e compila l'anamnesi — **senza installare nulla**, da qualsiasi rete (4G, Wi-Fi casa, ecc.).

I dati vanno direttamente dal browser al PC del trainer. Zero cloud, zero intermediari.

---

## Metodologia Operativa Definitiva

### Chi accede e come

| Chi | Come accede | URL | Richiede |
|-----|-------------|-----|----------|
| **Trainer (PC studio)** | Browser locale | `http://localhost:3000` | Nulla |
| **Trainer (tablet studio)** | Stesso Wi-Fi (LAN) | `http://192.168.x.x:3000` | Stesso Wi-Fi |
| **Trainer (fuori studio)** | Tailscale VPN | `http://100.x.x.x:3000` | App Tailscale su tablet |
| **Cliente (anamnesi)** | Link monouso WhatsApp | `https://nome.ts.net/public/anamnesi/{token}` | Solo browser |

### Flusso operativo quotidiano

1. Il trainer accende il PC → FitManager si avvia automaticamente (backend 8000 + frontend 3000)
2. Tailscale Funnel e' gia' attivo in background (`--bg`, sopravvive a riavvii)
3. Il trainer lavora da `localhost:3000` (o tablet via LAN/VPN)
4. Quando serve inviare un'anamnesi al cliente:
   - Profilo cliente → Anamnesi → "Invia Questionario"
   - Il link generato punta automaticamente a `https://nome.ts.net/...` (grazie a `PUBLIC_BASE_URL`)
   - Il trainer copia il link e lo invia su WhatsApp
5. Il cliente apre il link dal telefono → compila → dati nel DB locale del trainer

### Cosa NON serve al cliente finale
- Nessuna installazione (ne' Tailscale ne' altro)
- Nessun login o registrazione
- Nessuna app da scaricare
- Solo un link nel browser del telefono (Chrome, Safari, qualsiasi)

### Vincolo operativo
Il link funziona **SOLO** se il PC del trainer e' acceso e FitManager e' in esecuzione.
Se il PC e' spento, il cliente vedra' un errore di connessione.

---

## Prerequisiti

| Requisito | Dettaglio |
|-----------|-----------|
| Tailscale installato | v1.56+ (richiesto per `--bg` persistente) |
| Account Tailscale | Gratuito (piano Personal fino a 3 utenti) |
| MagicDNS abilitato | Admin Console → DNS → MagicDNS ON |
| HTTPS Certificates abilitato | Admin Console → DNS → HTTPS Certificates ON |
| ACL Funnel permission | Admin Console → Access Controls (vedi sotto) |
| PC acceso | Il link funziona SOLO se il PC e FitManager sono in esecuzione |

---

## Installazione Completa su PC Cliente (Runbook)

> **Checklist operativa per l'installatore.** Seguire nell'ordine esatto.
> Tempo stimato: 15-20 minuti (di cui 10 di download/installazione).

### Fase 1 — Tailscale (5 min)

- [ ] 1.1 Scaricare Tailscale da https://tailscale.com/download/windows
- [ ] 1.2 Installare e autenticarsi con l'account del trainer (email personale)
- [ ] 1.3 Verificare installazione:
  ```bash
  tailscale status
  # Deve mostrare la macchina con IP 100.x.x.x e nome (es. "pc-studio")
  ```
- [ ] 1.4 Annotare i dati della macchina:
  - **Nome macchina**: _________________ (es. `pc-studio`)
  - **Tailnet**: _________________ (es. `tail1234ab.ts.net`)
  - **DNS name completo**: _________________ (es. `pc-studio.tail1234ab.ts.net`)
  - **IP Tailscale**: _________________ (es. `100.x.x.x`)

### Fase 2 — Admin Console Tailscale (3 min)

Accedere a https://admin.tailscale.com con l'account del trainer.

- [ ] 2.1 **DNS** → verificare che **MagicDNS** sia ON (di solito attivo di default)
- [ ] 2.2 **DNS** → abilitare **HTTPS Certificates** se non attivo
- [ ] 2.3 **Access Controls** → nell'editor visuale, sezione **Capabilities**:
  - **Target**: selezionare l'email dell'account Tailscale del trainer
  - **Attribute**: `funnel`
  - **IP Pools**: lasciare vuoto
  - **Salvare** la policy
- [ ] 2.4 Verificare permesso Funnel:
  ```bash
  tailscale funnel status
  # OK: qualsiasi risposta che NON sia "Funnel not available"
  # (anche "No serve config" va bene — il permesso c'e')
  ```

### Fase 3 — FitManager (5 min)

- [ ] 3.1 Eseguire l'ultima build `FitManager_Setup_1.0.0.exe`
- [ ] 3.2 Primo avvio: completare il Setup Wizard (credenziali trainer)
- [ ] 3.3 Attivare licenza (se richiesta)
- [ ] 3.4 Verificare che il CRM funzioni: `http://localhost:3000` → login → navigazione OK

### Fase 4 — Configurazione Portale Pubblico (2 min)

- [ ] 4.1 Aprire il file `data/.env` nella cartella di installazione FitManager
- [ ] 4.2 Aggiungere le seguenti righe (sostituire con il DNS name annotato al punto 1.4):
  ```env
  PUBLIC_PORTAL_ENABLED=true
  PUBLIC_BASE_URL=https://<nome-macchina>.<tailnet>.ts.net
  ```
  Esempio concreto:
  ```env
  PUBLIC_PORTAL_ENABLED=true
  PUBLIC_BASE_URL=https://pc-studio.tail1234ab.ts.net
  ```
- [ ] 4.3 Riavviare FitManager (chiudere e riaprire)

### Fase 5 — Attivazione Funnel Persistente (2 min)

- [ ] 5.1 Aprire terminale (PowerShell o CMD)
- [ ] 5.2 Attivare Funnel persistente:
  ```bash
  tailscale funnel --bg 3000
  ```
  Output atteso:
  ```
  Available on the internet:
  https://<nome>.<tailnet>.ts.net/
  |-- proxy http://127.0.0.1:3000
  ```
- [ ] 5.3 Verificare che sia in background:
  ```bash
  tailscale funnel status
  # Deve mostrare la configurazione attiva
  ```

### Fase 6 — Test End-to-End (3 min)

- [ ] 6.1 **Test login via Funnel**: da un telefono (4G, Tailscale DISABILITATO):
  - Aprire `https://<nome>.ts.net/login` → deve apparire la pagina login
  - Fare login con le credenziali → deve funzionare
- [ ] 6.2 **Test anamnesi**: dal PC (localhost:3000):
  - Navigare su un profilo cliente → Anamnesi → "Invia Questionario"
  - Il link generato deve iniziare con `https://<nome>.ts.net/public/anamnesi/...`
  - Copiare il link → aprirlo dal telefono (4G) → deve apparire il form
  - Compilare e inviare → verificare che i dati compaiano nel profilo cliente
- [ ] 6.3 **Test monouso**: riaprire lo stesso link → deve mostrare "Link gia' utilizzato"

### Post-installazione — Comunicazione al Trainer

- [ ] Comunicare il link Funnel: `https://<nome>.ts.net`
- [ ] Spiegare: **"Il link per i clienti funziona solo quando FitManager e' aperto sul PC"**
- [ ] Spiegare: **"Tu lavori normalmente da localhost:3000, i link per i clienti li genera il sistema"**
- [ ] Spiegare: **"Dal tablet puoi accedere tramite lo stesso Wi-Fi usando l'IP del PC"**
- [ ] Annotare l'IP LAN del PC per accesso tablet: _________________ (es. `192.168.1.10`)
- [ ] Test tablet: aprire `http://<IP-LAN>:3000` dal tablet del trainer → login → OK

---

## Architettura Tecnica — Come Funziona

```
Cliente (smartphone 4G, qualsiasi rete)
  |
  | HTTPS (certificato Let's Encrypt gestito da Tailscale)
  v
Tailscale Funnel (cloud Tailscale — solo routing, zero dati persistiti)
  |
  | TCP tunnel crittografato
  v
PC Trainer (Tailscale daemon locale)
  |
  | proxy http://127.0.0.1:3000
  v
Next.js Frontend (porta 3000)
  |
  | rewrite /api/* → http://localhost:8000/api/*
  | rewrite /media/* → http://localhost:8000/media/*
  v
FastAPI Backend (porta 8000) → SQLite locale
```

### Perche' funziona senza esporre la porta 8000

Il frontend Next.js funge da **reverse proxy**:
- Il browser chiama URL relativi (`/api/auth/login`)
- Next.js rewrite li proxya internamente a `http://localhost:8000/api/auth/login`
- Il backend non e' mai esposto direttamente su internet

Configurazione in `frontend/next.config.ts`:
```typescript
rewrites: async () => ({
  source: "/api/:path*",
  destination: `http://localhost:${backendPort}/api/:path*`,
})
```

### API URL Detection (`frontend/src/lib/api-client.ts`)

```typescript
// HTTPS o nessuna porta → siamo dietro Funnel/reverse proxy → URL relativi
if (protocol === "https:" || !port) return "/api";
// Altrimenti → mapping diretto porta (LAN, localhost, VPN)
return `http://${hostname}:${apiPort}/api`;
```

### PUBLIC_BASE_URL — Link Generation

```
Trainer lavora da localhost:3000
  → genera link anamnesi
  → backend legge PUBLIC_BASE_URL da data/.env
  → ritorna URL assoluto: https://nome.ts.net/public/anamnesi/{token}
  → frontend mostra URL completo (non prepende localhost)
  → il link funziona dal telefono del cliente
```

Senza `PUBLIC_BASE_URL`, il link userebbe `window.location.origin` (es. `http://localhost:3000/...`)
che non sarebbe raggiungibile dal telefono del cliente.

### Proxy Next.js (`frontend/src/proxy.ts`)

`/api` e' nelle `PUBLIC_ROUTES` — il proxy non interferisce con le chiamate API
proxiate. L'autenticazione JWT e' gestita dal backend FastAPI.

---

## Gestione Funnel

### Attivare (persistente — raccomandato)
```bash
tailscale funnel --bg 3000
```
Sopravvive a chiusura terminale e riavvii del PC (richiede Tailscale v1.56+).

### Disattivare
```bash
tailscale funnel --bg off
```

### Verificare stato
```bash
tailscale funnel status
```

### Attivare (temporaneo — solo per test)
```bash
tailscale funnel 3000
# Ctrl+C per fermare
```

---

## Feature Flag e Configurazione

```env
# data/.env — configurazione completa per portale pubblico
PUBLIC_PORTAL_ENABLED=true
PUBLIC_BASE_URL=https://<nome-macchina>.<tailnet>.ts.net
```

### PUBLIC_PORTAL_ENABLED
Default: `false`. Se disabilitato, tutti gli endpoint `/api/public/*` ritornano 404.
Il Funnel continuera' a funzionare per il login trainer (utile per accesso remoto),
ma i link anamnesi per i clienti non saranno generabili.

### PUBLIC_BASE_URL
Default: vuoto (URL relativo). Se configurato, i link anamnesi generati usano questo
dominio come base — il trainer puo' lavorare da `localhost:3000` normalmente e i link
generati saranno comunque accessibili dal cliente via Funnel.

**Senza** `PUBLIC_BASE_URL`: il link usa `window.location.origin` — se il trainer
accede da localhost, il link sara' `http://localhost:3000/public/anamnesi/{token}`
(non raggiungibile dal cliente).

**Con** `PUBLIC_BASE_URL`: il link sara' sempre
`https://<nome>.ts.net/public/anamnesi/{token}` indipendentemente da come il trainer
accede al CRM.

**Importante**: dopo aver modificato `data/.env`, riavviare FitManager (il backend
legge le variabili d'ambiente solo all'avvio).

---

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| "Funnel not available" | ACL non configurato | Admin Console → Access Controls → aggiungere funnel attr |
| Login gira e da errore | Proxy blocca `/api/*` | Verificare `PUBLIC_ROUTES` include `/api` in `src/proxy.ts` |
| Link anamnesi con "localhost" | `PUBLIC_BASE_URL` non configurato | Aggiungere `PUBLIC_BASE_URL=https://...` in `data/.env` e riavviare |
| Link anamnesi non funziona da telefono | PC spento o FitManager non in esecuzione | Avviare FitManager + verificare `tailscale funnel status` |
| "ERR_CONNECTION_REFUSED" da telefono | Funnel non attivo | `tailscale funnel --bg 3000` |
| Certificato non valido | HTTPS Certificates non abilitato | Admin Console → DNS → abilitare HTTPS Certificates |
| Pagina bianca dopo login | Backend non raggiungibile | Verificare backend su porta 8000: `curl localhost:8000/health` |
| Immagini esercizi non caricate | Rewrite `/media/*` mancante | Verificare `next.config.ts` ha rewrite per `/media/:path*` |
| Tablet non raggiunge il CRM | IP LAN errato o firewall | Verificare IP con `ipconfig`, controllare firewall Windows porta 3000 |
| Funnel --bg fallisce con "foreground listener" | Funnel temporaneo gia' attivo | Chiudere il terminale con Funnel foreground, poi `tailscale funnel --bg 3000` |

---

## Sicurezza

| Aspetto | Implementazione |
|---------|----------------|
| Trasporto | HTTPS (Let's Encrypt via Tailscale) |
| Dati in transito | Solo routing via Tailscale cloud, zero persistenza |
| Dati a riposo | SQLite locale sul PC del trainer |
| Token anamnesi | UUID4 monouso, scadenza 48h, invalidato dopo uso |
| Rate limiting | 10 req/min, 30 req/h per IP (in-process) |
| Mascheramento | Nome cliente mascherato nella pagina pubblica ("Marco R.") |
| Feature flag | Disattivabile con `PUBLIC_PORTAL_ENABLED=false` |
| Backend | Non esposto direttamente — solo via Next.js proxy |
| Zero PII nel token | UUID opaco, nessun dato personale nell'URL |
| Soft-delete check | Token per client cancellato → 404 |

---

## Costi

- **Tailscale Personal**: gratuito (fino a 3 utenti, 100 dispositivi)
- **Funnel**: incluso nel piano gratuito
- **Dominio**: fornito da Tailscale (`*.ts.net`), zero costi DNS
- **Certificato HTTPS**: Let's Encrypt automatico, zero costi

---

## Setup Attuale (Sviluppo — gvera)

```
Tailscale:     v1.94.2
Macchina:      giacomo
Tailnet:       tail8a3bc3.ts.net
DNS name:      giacomo.tail8a3bc3.ts.net
IP Tailscale:  100.127.28.16
IP LAN:        192.168.1.23
Funnel:        https://giacomo.tail8a3bc3.ts.net/ → proxy http://127.0.0.1:3000
data/.env:     PUBLIC_PORTAL_ENABLED=true, PUBLIC_BASE_URL=https://giacomo.tail8a3bc3.ts.net
```

Dispositivi Tailscale:
- `giacomo` (PC dev, Windows) — 100.127.28.16
- `ipad-10th-gen-wifi` (iPad Chiara) — 100.77.229.76
- `iphone183` (iPhone) — 100.116.68.114

---

## Note per Sviluppo Futuro

- **Custom domain**: Tailscale supporta custom domain su Funnel (piano a pagamento).
  Es. `https://studio-chiara.fitmanager.it` invece di `*.ts.net`
- **Auto-start FitManager**: configurare launcher.bat in Startup di Windows
  per avvio automatico al login del trainer
- **Monitoring uptime**: potenziale feature futura — notifica push se il PC e' offline
  quando un cliente tenta di accedere
- **Multi-porta Funnel**: possibile esporre anche la porta 8000 direttamente,
  ma non necessario grazie al proxy Next.js
