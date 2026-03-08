# Implementazione Tailscale Funnel per Portale Clienti

Questo documento descrive la strategia adottata e l'implementazione effettuata per permettere ai clienti del CRM "FitManager AI Studio" di compilare il questionario anamnestico dal proprio smartphone, **senza dover scaricare l'app di Tailscale** o registrarsi ad alcun servizio, garantendo l'architettura privacy-first (Zero Cloud).

## È necessario un dominio di proprietà?

**No, non è necessario acquistare un dominio di proprietà.**
Tailscale fornisce automaticamente un dominio pubblico gratuito per la tua rete (`*.ts.net`, es. `chiarabassani.tail12345.ts.net`) accompagnato da un certificato HTTPS valido generato tramite Let's Encrypt.

Attraverso la funzionalità **Tailscale Funnel**, un nodo della tua rete privata può esporre in modo sicuro un servizio locale su Internet utilizzando questo dominio `*.ts.net`.

## Cosa è stato implementato finora (Ramo `fix-tailscale-funnel-anamnesi`)

Per supportare pienamente Tailscale Funnel e permettere ai clienti di accedere da una normale rete (4G, Wi-Fi di casa, ecc.), il codice è stato esteso nei seguenti punti:

### 1. Backend: Abilitazione Traffico Esterno (CORS)
Il file `api/main.py` è stato modificato per accettare le richieste HTTP/HTTPS provenienti dal dominio generato da Tailscale (`*.ts.net`).
- La regex di validazione `allow_origin_regex` è stata aggiornata.
- Aggiunto supporto al protocollo HTTPS in origine.

### 2. Backend: Generazione URL Pubblici Assoluti
Il router `api/routers/public_portal.py` che genera il link monouso (`create_share_token`) ora legge la variabile d'ambiente `PUBLIC_PORTAL_URL`.
- Se configurata, il sistema restituirà un URL assoluto (es. `https://chiarabassani.tail12345.ts.net/public/anamnesi/1234...`) invece di un percorso relativo.
- Il token generato contiene questo URL, disaccoppiando l'accesso del cliente dal contesto di navigazione del trainer.

### 3. Frontend: Miglioramento UI e Gestione Link
La UI per il trainer in `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx` è stata adattata:
- Gestisce fluidamente la copia e la condivisione (via WhatsApp) degli URL assoluti ricevuti dal backend.
- L'avviso in arancione che blocca moralmente l'invio del link se il trainer è su `localhost` viene ora **nascosto** se il link restituito dal backend è già pubblico e pronto (un link `http/https` assoluto).

## Guida Operativa all'Attivazione

### Step 1: Configurare Tailscale Funnel sul PC (Server)

1. Aprire il pannello di controllo Tailscale o usare la CLI per abilitare HTTPS sul proprio account (in *Settings* -> *Certificates* e attivare *Enable HTTPS*).
2. Scoprire il proprio "MagicDNS name" usando il comando:
   ```bash
   tailscale status
   ```
   (Cercare una stringa simile a `tuo-nome.tailXXXX.ts.net`).
3. Avviare il Funnel per esporre la porta `3000` (Frontend del CRM) al mondo esterno:
   ```bash
   tailscale funnel 3000
   ```
   Tailscale risponderà con l'URL pubblico (es. `https://tuo-nome.tailXXXX.ts.net`).

### Step 2: Configurare l'Ambiente del CRM (Backend)

Per far sì che l'applicazione sfrutti il nuovo accesso, aggiungi l'URL appena generato nel file `.env` (o `data/.env` se in produzione):

```env
PUBLIC_PORTAL_ENABLED=true
PUBLIC_PORTAL_URL=https://tuo-nome.tailXXXX.ts.net
```

### Step 3: Test e Utilizzo

1. Il trainer avvia normalmente l'app e accede a `localhost:3000`.
2. Nella scheda "Anamnesi" di un cliente, clicca su "Invia Questionario" e genera il link.
3. Anche lavorando in locale, il link generato sarà `https://tuo-nome.tailXXXX.ts.net/public/anamnesi/xxxx...`.
4. Condiviso su WhatsApp, il cliente clicca il link: la richiesta passa da Internet -> Server Tailscale globale -> Tailscale Funnel sul PC del trainer -> Backend locale (Porta 3000 -> 8000 via Proxy Next.js).
5. Il cliente compila e salva i dati in totale sicurezza, finendo direttamente sul database SQLite locale di FitManager.
