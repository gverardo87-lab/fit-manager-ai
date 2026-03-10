# Patch Spec - Connectivity Setup Wizard Plan v1

## Metadata

- Upgrade ID: UPG-2026-03-10-20
- Date: 2026-03-10
- Owner: Codex
- Area: Launch Readiness + Connectivity + Public Portal
- Priority: high
- Status: planned
- Target release: post-RC `1.0.0`, pre-pilot production hardening

## Problem

FitManager oggi supporta bene Tailscale, VPN e Funnel a livello tecnico, ma il flusso e'
ancora da installatore esperto:

- l'utente deve installare Tailscale da solo;
- deve capire come autenticarsi, leggere il proprio DNS `ts.net` e attivare Funnel;
- deve modificare `data/.env` a mano per `PUBLIC_PORTAL_ENABLED` e `PUBLIC_BASE_URL`;
- deve distinguere da solo tra accesso locale, accesso multi-dispositivo e portale pubblico;
- in caso di errore non esiste ancora una surface di prodotto che dica con chiarezza
  "cosa manca" e "qual e' il prossimo passo".

Questo e' accettabile per un prototipo o per un setup guidato dallo sviluppatore, ma non
per un prodotto locale-first che deve differenziarsi sul mercato per affidabilita e
facilita operativa.

## Desired Outcome

FitManager deve guidare il trainer fino a 3 esiti chiari, senza mai rompere il fallback
locale:

1. `Locale puro`
   - l'app resta usabile solo sul PC principale e, opzionalmente, su LAN;
   - nessuna dipendenza da Tailscale per il lavoro quotidiano.

2. `Multi-dispositivo`
   - il trainer puo usare il CRM da tablet/secondo device tramite Tailscale VPN;
   - nessun link pubblico verso i clienti.

3. `Portale pubblico`
   - il trainer continua a lavorare localmente o via VPN;
   - il prodotto genera e verifica in modo guidato i link pubblici per anamnesi clienti
     usando Funnel e `PUBLIC_BASE_URL`.

L'utente finale non deve conoscere i dettagli tecnici di `.env`, `tailscale funnel` o
`PUBLIC_BASE_URL`; deve essere il prodotto a spiegare, verificare e completare la propria
parte di configurazione.

## Product Decision

FitManager non deve diventare un client Tailscale proprietario e non deve raccogliere
credenziali Tailscale in UI.

Decisione:

- autenticazione Tailscale resta nel client ufficiale Tailscale;
- FitManager rileva lo stato del sistema e guida l'utente passo-passo;
- FitManager scrive solo la propria configurazione (`data/.env`) e verifica la propria
  readiness;
- il fallback locale resta sempre disponibile e prioritario.

## Scope

- In scope:
  - wizard guidato di connettivita in `Impostazioni` e nel primo avvio post-installazione;
  - stato runtime di Tailscale/Funnel leggibile dal backend;
  - profili di connettivita espliciti (`local_only`, `trusted_devices`, `public_portal`);
  - scrittura guidata e verificabile di `PUBLIC_PORTAL_ENABLED` / `PUBLIC_BASE_URL`;
  - sezione diagnostica `Connettivita` con semafori, CTA e check automatici;
  - aggiornamento runbook e documentazione installazione affinche il cliente sia guidato dal
    prodotto e non solo da istruzioni esterne.

- Out of scope:
  - login Tailscale in-app;
  - gestione password, MFA o sessioni Tailscale del cliente;
  - provisioning automatico ACL/admin console Tailscale;
  - sostituzione del launcher locale come entrypoint principale;
  - dipendenze cloud aggiuntive o servizi terzi fuori da Tailscale.

## Impact Map

- Files/modules da toccare:
  - `api/services/`:
    - nuovo `connectivity_runtime.py` o equivalente
    - eventuale helper `.env` runtime-safe
  - `api/routers/`:
    - nuovo router `connectivity.py` o estensione `system.py`
  - `api/schemas/`:
    - schema stato connettivita, schema wizard/apply config, schema verify
  - `frontend/src/app/(dashboard)/impostazioni/`
  - `frontend/src/components/settings/`
  - `frontend/src/hooks/`
  - `frontend/src/types/api.ts`
  - `docs/TAILSCALE_FUNNEL_SETUP.md`
  - `docs/SUPPORT_RUNBOOK.md`
  - `docs/RELEASE_CHECKLIST.md`
- `CLAUDE.md`, `frontend/CLAUDE.md`, `api/CLAUDE.md` quando il comportamento sara' reale

- Layer coinvolti: `api`, `frontend`, `tools`, `docs`

- Invarianti da preservare:
  - modalita locale sempre funzionante;
  - nessuna dipendenza da Tailscale per usare il CRM sul PC locale;
  - nessuna raccolta di credenziali Tailscale da parte di FitManager;
  - nessun dato clinico/finanziario nei test di connettivita;
  - `PUBLIC_BASE_URL` e `PUBLIC_PORTAL_ENABLED` restano in `data/.env`;
  - il portale pubblico resta disattivabile in ogni momento.

## Proposed Architecture

## Progress Update (2026-03-10)

- `Phase A - Contract + Runtime Read-only`: chiusa con `UPG-2026-03-10-21`
  - backend read-only `connectivity_runtime.py`
  - endpoint protetto `/api/system/connectivity-status`
  - type sync frontend
  - nuova surface `Connettivita` in `Impostazioni`
- Stato attuale: il prodotto sa leggere e spiegare lo stato reale della macchina, ma non
  applica ancora configurazioni `.env` e non offre ancora il wizard passo-passo.

### 1. Runtime Service Backend

Nuovo service backend per interrogare in sola lettura lo stato connettivita' locale.

Responsabilita:

- verificare se il client Tailscale e' installato;
- verificare se il nodo e' online;
- leggere IP Tailscale e DNS name quando disponibili;
- rilevare stato Funnel;
- leggere la configurazione corrente `PUBLIC_PORTAL_ENABLED` / `PUBLIC_BASE_URL`;
- determinare il `connectivity_profile` effettivo;
- restituire anche una lista di `checks` e `missing_requirements`.

Nota:
il piano non fissa ancora l'implementazione su uno specifico output CLI JSON senza prima
validare la versione Tailscale effettivamente installata in ambiente target. Il principio e':
preferire output macchina-readable se affidabile, con fallback read-only minimo.

### 2. Connectivity Profiles

Nuovo enum di prodotto:

- `local_only`
- `trusted_devices`
- `public_portal`

Regole:

- `local_only`:
  - `PUBLIC_PORTAL_ENABLED=false`
  - `PUBLIC_BASE_URL` opzionale/non necessaria
  - nessun requisito Tailscale

- `trusted_devices`:
  - Tailscale installato e nodo connesso
  - nessun Funnel richiesto
  - `PUBLIC_PORTAL_ENABLED=false`

- `public_portal`:
  - Tailscale installato e nodo connesso
  - DNS `ts.net` disponibile
  - `PUBLIC_PORTAL_ENABLED=true`
  - `PUBLIC_BASE_URL=https://<dns-name>`
  - Funnel verificato come attivo/pronto

### 3. Settings UX

Nuova surface `Connettivita` in `Impostazioni`, separata ma coerente con:

- `Stato installazione`
- `Snapshot diagnostico`

Blocchi UI:

1. `Profilo attuale`
   - Solo su questo PC
   - Anche su altri dispositivi
   - Portale clienti attivo

2. `Health checks`
   - Tailscale installato
   - Account connesso
   - Nodo online
   - IP Tailscale rilevato
   - DNS name rilevato
   - `.env` allineato
   - Funnel pronto
   - Portale pubblico verificato

3. `CTA guidate`
   - Installa Tailscale
   - Verifica accesso
   - Configura accesso altri dispositivi
   - Attiva portale clienti
   - Riesegui test

### 4. Guided Wizard

Wizard lineare, riapribile, con progressione deterministica:

1. scelta profilo
2. installazione Tailscale
3. login nel client Tailscale ufficiale
4. verifica automatica lato FitManager
5. proposta/scrittura configurazione `.env`
6. attivazione Funnel per `public_portal`
7. test finale e riepilogo

Principio UX:
`Rileva -> Spiega -> Applica -> Verifica`

Mai:
`Mostra testo tecnico e lascia all'utente il compito di capire`.

## API Contract (Planned)

### `GET /api/system/connectivity-status`

Payload read-only con:

- `profile`
- `tailscale_installed`
- `tailscale_connected`
- `tailscale_ip`
- `dns_name`
- `funnel_status`
- `public_portal_enabled`
- `public_base_url`
- `checks[]`
- `missing_requirements[]`
- `next_recommended_action`

### `POST /api/system/connectivity-config`

Scrittura guidata di configurazione FitManager, non di Tailscale.

Input:

- `profile`
- `public_portal_enabled`
- `public_base_url`

Output:

- `.env` aggiornato
- riepilogo delle chiavi scritte
- eventuale `restart_required`

### `POST /api/system/connectivity-verify`

Riesegue i test applicativi e produce un verdetto leggibile:

- `status = ready | partial | blocked`
- elenco check pass/fail
- CTA successiva

### `POST /api/system/connectivity-open-download`

Opzionale, solo se utile:

- restituisce il link ufficiale Tailscale o apre la pagina guida
- nessuna automazione opaca sul sistema operativo

## Execution Plan

### Phase A - Contract + Runtime Read-only

Obiettivo:
far leggere a FitManager lo stato reale di Tailscale/Funnel senza cambiare ancora la UX.

Microstep:

1. modellare schemi `ConnectivityStatusResponse`
2. creare runtime service read-only
3. esporre endpoint `connectivity-status`
4. aggiungere test backend su stati assenti / presenti / configurazione parziale

Done:

- backend sa distinguere `local_only`, `trusted_devices`, `public_portal`
- nessuna scrittura su `.env` ancora

### Phase B - Surface in Settings

Obiettivo:
rendere visibile e actionable la connettivita senza introdurre ancora il wizard completo.

Microstep:

1. hook frontend `useConnectivityStatus`
2. card `Connettivita`
3. semafori e CTA
4. loading/error/partial state

Done:

- l'utente capisce cosa manca per arrivare al profilo desiderato

### Phase C - Guided Config Apply

Obiettivo:
spostare la scrittura di `PUBLIC_PORTAL_ENABLED` e `PUBLIC_BASE_URL` dal file manuale al prodotto.

Microstep:

1. endpoint apply config
2. guardrail su valori ammessi
3. scrittura `.env` idempotente
4. feedback `restart required`

Done:

- il trainer non deve piu toccare `.env` a mano per il caso standard

### Phase D - Wizard Flow

Obiettivo:
orchestrare il percorso end-to-end dentro l'app.

Microstep:

1. wizard stepper
2. scelta profilo
3. gating progressivo sui prerequisiti
4. step finale di verifica

Done:

- da installazione fresca il trainer puo arrivare al proprio indirizzo Tailscale guidato dal
  prodotto

### Phase E - Public Portal Validation

Obiettivo:
chiudere davvero il flusso anamnesi pubblica come esperienza di prodotto.

Microstep:

1. verifica `PUBLIC_BASE_URL`
2. stato portale pubblico
3. test guidato link anamnesi
4. aggiornamento runbook e checklist

Done:

- il prodotto conferma quando il link pubblico e' davvero pronto

## Documentation Alignment Plan

Quando il blocco iniziera' davvero, i documenti da riallineare saranno:

1. `CLAUDE.md`
2. `frontend/CLAUDE.md`
3. `api/CLAUDE.md`
4. `docs/TAILSCALE_FUNNEL_SETUP.md`
5. `docs/SUPPORT_RUNBOOK.md`
6. `docs/RELEASE_CHECKLIST.md`
7. `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`

Regola:
prima si implementa il contratto reale, poi si promuovono i documenti autorevoli.
Questa spec e' il ponte tracciabile tra l'idea prodotto e l'implementazione.

## Acceptance Criteria

- Funzionale:
  - l'utente puo scegliere un profilo di connettivita comprensibile;
  - il prodotto rileva automaticamente lo stato di Tailscale/Funnel;
  - il prodotto sa configurare in autonomia `PUBLIC_PORTAL_ENABLED` e `PUBLIC_BASE_URL`;
  - il fallback locale resta sempre operativo.

- UX:
  - zero editing manuale di `.env` per il caso standard;
  - zero richiesta di credenziali Tailscale dentro FitManager;
  - stato espresso come checklist rosso/ambra/verde con CTA esplicite;
  - il trainer capisce in ogni momento se sta configurando accesso locale, multi-dispositivo o
    pubblico.

- Tecnico:
  - type sync completo backend/frontend;
  - nessun dato sensibile nei payload di stato;
  - nessuna regressione sui flow `localhost`, LAN, VPN e Funnel gia' esistenti;
  - modalita locale verificata anche se Tailscale non e' installato.

## Test Plan

- Unit/Integration:
  - test backend runtime parsing con Tailscale assente
  - test backend runtime parsing con Tailscale presente ma non connesso
  - test backend apply config su `.env`
  - test frontend su loading/error/blocked/ready state

- Manual checks:
  - installazione pulita senza Tailscale -> profilo `local_only`
  - login Tailscale -> passaggio a `trusted_devices`
  - attivazione Funnel -> passaggio a `public_portal`
  - generazione link anamnesi con `PUBLIC_BASE_URL` corretta

- Build/Lint gates:
  - `ruff check api/ tests/`
  - lint frontend file toccati
  - `bash tools/scripts/check-all.sh` prima del commit finale del blocco

## Risks and Mitigation

- Rischio 1: forte dipendenza da output CLI Tailscale diversi per versione/piattaforma.
  - Mitigazione: iniziare con service read-only piccolo, validare su macchina target, evitare
    assunzioni premature su JSON non ancora provati.

- Rischio 2: il prodotto sembra "gestire Tailscale" ma in realta non puo intervenire su ACL/admin.
  - Mitigazione: CTA e copy oneste; distinguere chiaramente tra configurazione FitManager e
    passaggi che l'utente deve fare nel client/admin console.

- Rischio 3: rompere l'affidabilita locale introducendo dipendenza remota implicita.
  - Mitigazione: `local_only` resta il default e non viene mai disabilitato.

- Rischio 4: confondere installatore e trainer con troppi stati.
  - Mitigazione: soli 3 profili di prodotto e checklist diagnostica compatta.

## Rollback Plan

- se il blocco regressa:
  - mantenere la configurazione manuale via `data/.env`;
  - lasciare `TAILSCALE_FUNNEL_SETUP.md` come runbook tecnico;
  - disattivare la nuova surface wizard mantenendo `Stato installazione` e `Snapshot diagnostico`.

## Next Smallest Step

Aprire il primo microstep implementativo:

`UPG-2026-03-10-21` o successivo, focalizzato su `Phase A - Contract + Runtime Read-only`.

Prima implementazione consigliata:

1. schema backend/frontend di `connectivity-status`
2. service read-only
3. card minima in `Impostazioni`
4. zero scritture `.env` nel primo step
