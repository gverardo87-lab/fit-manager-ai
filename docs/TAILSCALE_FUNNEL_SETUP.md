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

## Prerequisiti

| Requisito | Dettaglio |
|-----------|-----------|
| Tailscale installato | v1.50+ (Funnel supportato da v1.38) |
| Account Tailscale | Gratuito (piano Personal fino a 3 utenti) |
| MagicDNS abilitato | Admin Console → DNS → MagicDNS ON |
| HTTPS Certificates abilitato | Admin Console → DNS → HTTPS Certificates ON |
| ACL Funnel permission | Admin Console → Access Controls (vedi sotto) |
| PC acceso | Il link funziona SOLO se il PC e FitManager sono in esecuzione |

---

## Step 1 — Installazione Tailscale (primo setup)

1. Scaricare da https://tailscale.com/download/windows
2. Installare e autenticarsi con l'account del trainer
3. Verificare: `tailscale status` deve mostrare la macchina con IP `100.x.x.x`

---

## Step 2 — Abilitazione nella Admin Console

Accedere a https://admin.tailscale.com con l'account del trainer.

### 2a. DNS
1. **MagicDNS**: verificare che sia ON (di solito attivo di default)
2. **HTTPS Certificates**: abilitare se non attivo

### 2b. Access Controls (ACL)
1. Andare su **Access Controls**
2. Nell'editor visuale, sezione **nodeAttrs** (o **Capabilities**):
   - **Target**: selezionare l'email dell'account Tailscale del trainer
   - **Attribute**: `funnel`
   - **IP Pools**: lasciare vuoto
3. **Salvare** la policy

### 2c. Verifica
```bash
tailscale funnel status
# Deve rispondere (anche "No serve config" va bene — significa che non c'e' niente attivo ma il permesso c'e')
# Se risponde "Funnel not available" → il permesso ACL non e' stato configurato correttamente
```

---

## Step 3 — Attivazione Funnel

### Comando singolo
```bash
tailscale funnel 3000
```

Output atteso:
```
Available on the internet:

https://<nome-macchina>.<tailnet>.ts.net/
|-- proxy http://127.0.0.1:3000

Press Ctrl+C to exit.
```

Il link pubblico e': `https://<nome-macchina>.<tailnet>.ts.net/`

### Setup attuale (sviluppo — gvera)
```
Tailscale: v1.94.2
Macchina:  giacomo
Tailnet:   tail8a3bc3.ts.net
DNS name:  giacomo.tail8a3bc3.ts.net
IP:        100.127.28.16
Funnel:    https://giacomo.tail8a3bc3.ts.net/ → proxy http://127.0.0.1:3000
```

---

## Step 4 — Verifica end-to-end

1. Backend in esecuzione su porta 8000
2. Frontend in esecuzione su porta 3000 (production build: `npm run prod`)
3. Funnel attivo: `tailscale funnel 3000`
4. Da un telefono (4G, Tailscale DISABILITATO sul telefono):
   - Aprire `https://<nome>.ts.net/login` → deve apparire la pagina login
   - Fare login con le credenziali → deve funzionare (API proxiate via Next.js)
   - Navigare nelle pagine → tutto deve funzionare normalmente
5. Generare link anamnesi: profilo cliente → anamnesi → "Invia Questionario"
   - Il link generato usa `window.location.origin` = `https://<nome>.ts.net`
   - Inviare su WhatsApp → il cliente apre dal telefono → compila → dati nel DB locale

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

### Middleware Next.js (`frontend/src/middleware.ts`)

`/api` e' nelle `PUBLIC_ROUTES` — il middleware non interferisce con le chiamate API
proxiate. L'autenticazione JWT e' gestita dal backend FastAPI.

---

## Installazione su PC Cliente (Checklist)

### Pre-installazione
- [ ] Tailscale installato sul PC del trainer
- [ ] Account Tailscale creato (email del trainer)
- [ ] MagicDNS abilitato nell'admin console
- [ ] HTTPS Certificates abilitato nell'admin console
- [ ] ACL Funnel configurato (target: email trainer, attr: funnel)
- [ ] Annotare il DNS name: `<macchina>.<tailnet>.ts.net`

### Installazione FitManager
- [ ] Eseguire `FitManager_Setup.exe`
- [ ] Primo avvio: Setup Wizard (credenziali trainer)
- [ ] Attivare licenza
- [ ] Configurare `PUBLIC_PORTAL_ENABLED=true` in `data/.env`

### Attivazione Funnel
- [ ] Aprire terminale come amministratore
- [ ] `tailscale funnel 3000`
- [ ] Verificare link: `https://<nome>.ts.net/login` da telefono (4G)
- [ ] Se tutto OK → configurare Funnel persistente (vedi sezione sotto)

### Post-installazione
- [ ] Comunicare al trainer il link Funnel: `https://<nome>.ts.net`
- [ ] Spiegare: "Il link funziona solo quando FitManager e' aperto sul PC"
- [ ] Test completo: generare link anamnesi → inviare su WhatsApp → compilare da telefono

---

## Funnel Persistente (Background Service)

Per evitare di tenere il terminale aperto:

```bash
# Rende il Funnel permanente (sopravvive ai riavvii)
tailscale funnel --bg 3000
```

Il flag `--bg` (disponibile da Tailscale v1.56+) esegue il serve in background
come parte del daemon Tailscale. Sopravvive a chiusura terminale e riavvii del PC.

Per rimuovere:
```bash
tailscale funnel --bg off
```

Per verificare stato:
```bash
tailscale funnel status
```

---

## Feature Flag

```env
# data/.env
PUBLIC_PORTAL_ENABLED=true    # Abilita endpoint pubblici anamnesi
```

Default: `false`. Se disabilitato, tutti gli endpoint `/api/public/*` ritornano 404.
Il Funnel continuera' a funzionare per il login trainer (utile per accesso remoto),
ma i link anamnesi per i clienti non saranno generabili.

---

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| "Funnel not available" | ACL non configurato | Admin Console → Access Controls → aggiungere funnel attr |
| Login gira e da errore | Middleware blocca `/api/*` | Verificare `PUBLIC_ROUTES` include `/api` in middleware.ts |
| Link anamnesi "localhost" | Trainer accede da localhost | Accedere via `https://<nome>.ts.net` per generare link |
| "ERR_CONNECTION_REFUSED" | PC spento o FitManager non in esecuzione | Avviare FitManager + `tailscale funnel 3000` |
| Certificato non valido | HTTPS Certificates non abilitato | Admin Console → DNS → abilitare HTTPS Certificates |
| Pagina bianca dopo login | Backend non raggiungibile | Verificare backend su porta 8000: `curl localhost:8000/health` |
| Immagini esercizi non caricate | Rewrite `/media/*` non funziona | Verificare `next.config.ts` ha rewrite per `/media/:path*` |

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

---

## Costi

- **Tailscale Personal**: gratuito (fino a 3 utenti, 100 dispositivi)
- **Funnel**: incluso nel piano gratuito
- **Dominio**: fornito da Tailscale (`*.ts.net`), zero costi DNS
- **Certificato HTTPS**: Let's Encrypt automatico, zero costi

---

## Note per Sviluppo Futuro

- **Custom domain**: Tailscale supporta custom domain su Funnel (piano a pagamento).
  Es. `https://studio-chiara.fitmanager.it` invece di `*.ts.net`
- **Funnel su piu' porte**: possibile esporre anche la porta 8000 direttamente,
  ma non necessario grazie al proxy Next.js
- **Monitoring uptime**: potenziale feature futura — notifica push se il PC e' offline
  quando un cliente tenta di accedere
