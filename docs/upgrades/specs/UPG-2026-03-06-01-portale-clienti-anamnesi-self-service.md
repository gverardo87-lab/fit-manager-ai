# UPG-2026-03-06-01 — Portale Clienti: Anamnesi Self-Service

**Data**: 2026-03-07
**Branch**: `codex_02`
**Owner**: Claude Code
**Stato**: DONE (ruff + next build green, E2E Tailscale testato, PUBLIC_BASE_URL configurato)

---

## Problema

Il trainer inserisce manualmente i dati di anamnesi per ogni nuovo cliente, oppure usa Google Forms via WhatsApp — violando il paradigma "zero cloud" del prodotto. I dati transitano su server Google, fuori dal perimetro di privacy dell'applicazione.

---

## Soluzione

Il trainer genera un link monouso dall'interno del CRM. Il cliente lo apre da smartphone e compila direttamente. I dati arrivano nel DB locale SQLite senza intermediari cloud.

**Flusso**: Trainer genera link → lo invia su WhatsApp → Cliente compila da mobile → Dati salvati nel profilo → Token invalidato.

---

## Architettura

### Perche' UUID4 e non JWT stateless

Il requisito "monouso" richiede tracking dello stato (`used_at`). JWT e' stateless — impossibile invalidare dopo l'uso senza un DB di revoca. UUID4 + colonna `used_at` permette: monouso garantito, revocabilita', audit trail.

### Proxy Next.js per Tailscale Funnel

Il frontend funge da proxy per le chiamate ai endpoint pubblici (`/api/public/*`). Questo risolve due problemi:
1. Lo smartphone usa URL relativi → il browser Next.js proxya al backend server-side → nessun problema CORS o IP hardcoded
2. Funziona sia su LAN (192.168.x.x) che su Tailscale (100.x.x.x) senza configurazione aggiuntiva

### Middleware Next.js — Separazione `PUBLIC_ROUTES` vs `AUTH_ONLY_PAGES`

**Pitfall critico**: Next.js middleware gira PRIMA dei rewrite rules. Le chiamate `fetch('/api/public/*')` dalla pagina kiosk (senza cookie JWT) vengono intercettate dal middleware prima di essere proxiate al backend.

La soluzione corretta separa due concetti distinti:
- `PUBLIC_ROUTES`: rotte accessibili senza autenticazione (include `/api/public`)
- `AUTH_ONLY_PAGES`: sole pagine da cui redirectare gli utenti gia' autenticati (es. `/login`, `/register`)

Questa separazione previene che un trainer loggato che clicca il link kiosk venga reindirizzato alla homepage.

---

## File Creati / Modificati

| File | Azione | Descrizione |
|------|--------|-------------|
| `api/models/share_token.py` | Nuovo | SQLModel `ShareToken` — UUID4, trainer_id, client_id, scope, created_at, expires_at, used_at |
| `api/schemas/public.py` | Nuovo | Pydantic DTOs: ShareTokenCreate/Response, AnamnesiValidateResponse, AnamnesiSubmitRequest/Response |
| `api/routers/public_portal.py` | Nuovo | 3 endpoint + rate limiter IP-based + feature flag `PUBLIC_PORTAL_ENABLED` |
| `api/database.py` | Modifica | Import `ShareToken` in `create_db_and_tables()` |
| `api/main.py` | Modifica | Import + registrazione `public_portal_router`, `/api/public/*` in `LICENSE_EXEMPT_PATHS` |
| `alembic/versions/ecf22d7823a8_*.py` | Nuovo | Migrazione Alembic `share_tokens` table |
| `frontend/src/app/public/anamnesi/[token]/page.tsx` | Nuovo | Pagina kiosk mobile-first (fuori da `(dashboard)`) — wizard 6 step riusa `AnamnesiSteps` + `AnamnesiStepsSalute` |
| `frontend/src/hooks/useClients.ts` | Modifica | Aggiunto `useCreateShareToken(clientId)` |
| `frontend/src/types/api.ts` | Modifica | Aggiunte `ShareTokenResponse`, `AnamnesiValidateResponse` |
| `frontend/src/middleware.ts` | Modifica | Separazione `PUBLIC_ROUTES` + `AUTH_ONLY_PAGES`, aggiunto `/api/public` |
| `frontend/next.config.ts` | Modifica | Aggiunta rewrite `/api/public/:path*` → backend (proxy same-origin) |
| `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx` | Modifica | Bottone "Invia Questionario" + `ShareAnamnesiDialog` + warning localhost |

---

## Endpoint Backend

### `POST /api/clients/{client_id}/share-anamnesi` (JWT trainer)
- Verifica ownership `client.trainer_id == trainer.id` (Bouncer Pattern)
- Invalida token precedenti non usati per stesso client+scope
- Genera UUID4, crea `ShareToken` con `expires_at = now + 48h`
- Feature flag `PUBLIC_PORTAL_ENABLED` → 404 se disabilitato
- Ritorna `ShareTokenResponse` con URL relativo `/public/anamnesi/{token}`

### `GET /api/public/anamnesi/validate?token=X` (pubblico)
- Cerca token in DB
- Verifica: non scaduto (`expires_at > now`), non usato (`used_at is None`), client non soft-deleted
- Ritorna `AnamnesiValidateResponse` con nome mascherato ("Marco R."), nome trainer, `has_existing`
- 404 generico per qualsiasi condizione di invalidita' (no info leaking)

### `POST /api/public/anamnesi/submit` (pubblico)
- Stessa validazione token di validate
- Salva anamnesi: `client.anamnesi_json = json.dumps(anamnesi)`
- Invalida token: `token.used_at = datetime.now()` — commit atomico
- Ritorna `AnamnesiSubmitResponse`

### Rate Limiting (in-process, zero dipendenze)
```python
_rate_store: dict[str, list[float]] = defaultdict(list)
# 10 req/min per IP, 30 req/hour per IP
```
Applicato su tutti gli endpoint `/api/public/*`. Risposta: 429 se superato.

---

## Sicurezza

| Aspetto | Implementazione |
|---------|----------------|
| Entropia token | UUID4 = 122 bit, non indovinabile |
| Monouso | `used_at` settato atomicamente al submit → secondo tentativo = 404 |
| Scadenza | 48h verificata server-side su ogni richiesta |
| Rate limiting | 10 req/min / 30 req/h per IP — sufficiente per single-trainer |
| Zero PII nel token | UUID opaco, nessun dato personale nell'URL |
| Mascheramento nome | "Marco R." (non cognome completo) nella pagina pubblica |
| Soft-delete check | Token per client cancellato → 404 |
| Feature flag | `PUBLIC_PORTAL_ENABLED=false` default → tutti gli endpoint 404 |
| IDOR | Generazione token richiede JWT trainer + ownership check |
| No info leaking | 404 generico per token invalido/scaduto/usato |

---

## Frontend — Pagina Kiosk

**Percorso**: `frontend/src/app/public/anamnesi/[token]/page.tsx`

Layout fuori da `(dashboard)` — nessun sidebar, nessun AuthGuard. Stile login page (`bg-mesh-login`, card centrata). Mobile-first, max-w-lg.

**Flusso UI**:
1. Mount → `GET /api/public/anamnesi/validate?token=X`
2. Token valido → wizard 6 step (riusa `AnamnesiSteps` + `AnamnesiStepsSalute`)
3. Submit → `POST /api/public/anamnesi/submit`
4. Successo → pagina "Grazie" con check verde
5. Errori: "Link scaduto", "Link gia' utilizzato", "Link non valido"

**API client**: Istanza axios dedicata senza auth header, base URL da `window.location` (stesso pattern `getApiBaseUrl()`). Non usa `apiClient` (ha interceptor JWT + redirect 401).

**Data protection**: `beforeunload` listener se form compilato ma non inviato.

---

## Trainer UI — Dialog "Invia Questionario"

Bottone aggiunto in tutti e 3 gli stati della pagina anamnesi (empty, legacy, structured).

**Dialog**:
- Genera link → `POST /api/clients/{id}/share-anamnesi`
- Campo input readonly con URL + bottone "Copia" (`navigator.clipboard`)
- Bottone "Invia su WhatsApp" → `window.open('whatsapp://send?text=...')`
- **Warning amber**: visibile quando `window.location.hostname === "localhost"` → spiega che il link funziona solo su stesso PC e invita ad usare IP LAN o Tailscale

---

## Pitfalls Rilevati e Risolti

### 1. Middleware Next.js intercetta fetch API prima dei rewrite
**Causa**: middleware gira prima dei rewrite — `fetch('/api/public/*')` senza cookie viene bloccato.
**Fix**: aggiungere `/api/public` a `PUBLIC_ROUTES` distinto da `AUTH_ONLY_PAGES`.

### 2. `alembic upgrade head` fallisce su tabella gia' creata
**Causa**: `create_db_and_tables()` al startup di FastAPI crea le tabelle. Alembic trova la tabella gia' esistente.
**Fix**: `alembic stamp <revision>` su entrambi i DB per marcare la migrazione come applicata.

### 3. Link generato da localhost non fruibile da smartphone
**Causa**: `window.location.origin = "http://localhost:3000"` → URL irraggiungibile da altri device.
**Fix**: warning amber nel dialog; il trainer deve usare IP LAN o Tailscale per generare link.

---

## Test E2E Eseguito

### Test 1 — Tailscale VPN (2026-03-07)
1. Backend su porta 8000 (`crm.db`) + Frontend su porta 3000
2. Trainer accede via `http://100.127.28.16:3000` (Tailscale VPN)
3. Naviga su profilo cliente → anamnesi → "Invia Questionario"
4. Genera link → copia URL `http://100.127.28.16:3000/public/anamnesi/{token}`
5. Apre URL su smartphone (4G roaming via Tailscale) → form visibile
6. Compila wizard → "Invia" → pagina "Grazie"
7. Stesso link riaperto → "Link gia' utilizzato"
8. Profilo cliente nel CRM → anamnesi aggiornata

**Risultato**: OK. Richiede Tailscale installato sullo smartphone (limitante).

### Test 2 — Tailscale Funnel (2026-03-08)
1. Backend su porta 8000 + Frontend su porta 3000 (production build)
2. `tailscale funnel 3000` → `https://giacomo.tail8a3bc3.ts.net/`
3. Da smartphone 4G **senza Tailscale**:
   - `https://giacomo.tail8a3bc3.ts.net/login` → pagina login visibile
   - Login con credenziali → accesso completo al CRM via HTTPS
   - Generazione link anamnesi → URL con dominio `.ts.net`
   - Cliente compila da qualsiasi browser → dati nel DB locale

**Risultato**: OK. Zero installazioni richieste al cliente. HTTPS automatico.

### Modifiche per Funnel (2026-03-08)
- `api-client.ts`: `getApiBaseUrl()` rileva HTTPS/no-port → ritorna `/api` (URL relativo)
- `next.config.ts`: rewrite `/api/:path*` → backend (era solo `/api/public/:path*`)
- `middleware.ts`: `/api` aggiunto a `PUBLIC_ROUTES` (il middleware non blocca piu' le API proxiate)

### PUBLIC_BASE_URL (2026-03-08)
- `public_portal.py`: `create_share_token` legge `PUBLIC_BASE_URL` da env → se presente, genera URL assoluto
- `anamnesi/page.tsx`: `ShareAnamnesiDialog` rileva URL assoluto (`http*`) → non prepende `window.location.origin`
- Warning localhost nascosto se `PUBLIC_BASE_URL` configurato (il link e' gia' corretto)
- Permette al trainer di lavorare da `localhost:3000` e generare link Funnel validi

---

## Stato Feature Flag e Configurazione

```env
# data/.env
PUBLIC_PORTAL_ENABLED=true
PUBLIC_BASE_URL=https://<nome-macchina>.<tailnet>.ts.net
```

- `PUBLIC_PORTAL_ENABLED`: default `false`. Attivare per abilitare il portale.
- `PUBLIC_BASE_URL`: default vuoto. Se configurato, i link anamnesi usano questo dominio.

---

## Documentazione Collegata

- **Setup completo Funnel**: `docs/TAILSCALE_FUNNEL_SETUP.md`
- **ADR architetturale**: `docs/adr/0001-client-portal-tailscale-funnel.md` (branch `arch-client-portal-tailscale-*`)
- **Pitfalls**: root `CLAUDE.md` sezione Pitfalls (middleware, localhost, API proxy)
