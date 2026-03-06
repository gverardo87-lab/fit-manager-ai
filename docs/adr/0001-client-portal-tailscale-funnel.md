# ADR - Client Portal Locale con Tailscale Funnel

- Date: 2026-03-05
- Status: accepted
- Deciders: G. Verardo (Sviluppatore)
- Related upgrade ID: UPG-2026-03-06-01

## Context

I migliori CRM per personal trainer (es. Trainerize, TrueCoach) offrono ai clienti un portale o un'app self-service per compilare l'anamnesi, consultare l'agenda o vedere i progressi.
FitManager AI Studio e' attualmente uno strumento solo-PT ("privacy-first", tutto in locale, zero cloud per i dati in chiaro).
Tuttavia, c'e' la forte necessita' di alleggerire il data-entry per il trainer (es. inviando un link su WhatsApp per l'anamnesi iniziale), mantenendo la rigorosa architettura locale-centrica.
Attualmente, la trainer usa Google Docs via link WhatsApp per l'anamnesi iniziale.

## Decision Drivers

- **Zero Cloud Storage**: I dati sensibili (es. anamnesi medica e sportiva) non devono MAI risiedere su server o database di terze parti, neanche temporaneamente, a meno che non siano criptati E2E.
- **Minimo Attrito Utente (Cliente)**: Il cliente finale deve poter cliccare un link dal proprio telefono e compilare l'anamnesi, senza installare app o VPN.
- **Semplicita' Architetturale (Maintainability)**: Evitare di mantenere un'infrastruttura backend parallela in cloud (database, auth, API) solo per i form pubblici.
- **Infrastruttura Esistente**: La trainer usa gia' Tailscale (100.127.28.16) per accedere al CRM dal proprio iPad personale quando non e' al PC fisico.

## Considered Options

### Option A: Cloud Relay E2E (Server Asincrono)
- **Pro**: Funziona 24/7. Il cliente puo' compilare l'anamnesi anche se il PC locale del trainer e' spento. I dati sono protetti da crittografia asimmetrica end-to-end.
- **Contro**: Alta complessita'. Richiede un piccolo server cloud (Vercel/Cloudflare Workers), la gestione di chiavi RSA pubbliche/private, e un worker locale sul CRM per "scaricare" i payload cifrati. Aumenta la superficie d'attacco e le dipendenze esterne.

### Option B: Kiosk in Studio (Wi-Fi LAN)
- **Pro**: 100% sicuro. Nessuna esposizione su internet. Il cliente compila su un tablet fornito dal trainer connesso alla stessa rete locale (`http://192.168.1.x:3000/kiosk`).
- **Contro**: Pessima UX per l'onboarding remoto. Non permette l'invio preventivo via WhatsApp (es. il giorno prima della visita). Limita le potenzialita' di marketing e prevendita.

### Option C: Tunnel Pubblico Diretto (Tailscale Funnel / Ngrok)
- **Pro**: I dati vanno direttamente dal browser del cliente al server FastAPI locale del trainer. Zero persistenza cloud. Tailscale e' gia' installato sulla macchina del trainer. Tailscale Funnel fornisce un dominio HTTPS pubblico instradato internamente al PC.
- **Contro**: Sincronia richiesta. Il link funziona *solo* se il PC del trainer e' acceso e l'app e' in esecuzione.

## Decision

**Option C (Tunnel Pubblico Diretto via Tailscale Funnel)** e' la soluzione approvata.

Sfruttando Tailscale, gia' in uso per l'accesso remoto via iPad (VPN P2P), possiamo abilitare la feature "Funnel". Tailscale Funnel permette di esporre in modo sicuro un servizio locale su internet pubblico tramite un URL Tailscale fisso e HTTPS (es. `https://chiara-studio.ts.net`), gestendo nativamente il reverse proxy senza dover esporre porte fisiche sul router o IP statici.

Il flusso sara':
1. Il backend FastAPI espone endpoint dedicati e rate-limited sotto `/public/...`.
2. Il frontend Next.js espone route dedicate sotto `/public/anamnesi/[token]`, senza header/sidebar, ottimizzate mobile.
3. Il CRM genera un link `https://<tailscale-funnel-domain>/public/anamnesi/<token-univoco>` e lo pre-compila in un messaggio WhatsApp.
4. Il cliente compila il form. La POST va direttamente al DB SQLite locale, invalidando il token monouso.

Questo rispetta il vincolo assoluto "zero dati verso terzi" e trasforma il CRM in un vero portale client-facing senza rinunciare all'architettura on-premise.

## Consequences

- **Positive**: Trasforma l'onboarding in un'esperienza premium ("White label" app feel) per il cliente. Elimina il data entry manuale da Google Docs. Zero costi cloud infrastrutturali.
- **Negative**: Il trainer deve essere consapevole che il link funziona solo a PC acceso (comunicazione chiara nel messaggio WhatsApp o alert nell'UI del CRM).
- **Follow-up actions**:
  1. Sperimentare localmente Tailscale Funnel per verificare il routing alla porta 3000 (frontend) e proxy API.
  2. Implementare la tabella DB `magic_links` o `public_tokens` per gestire accessi one-time e scadenze (es. 48 ore).
  3. Costruire l'UI kiosk-mode `/public/anamnesi/` e le API di submission Bouncer-protected (rate limiting per IP proxy Tailscale).

## Rollback / Exit Strategy

Se l'infrastruttura Tunnel si rivela instabile o il vincolo "PC acceso" frustra troppo i clienti/trainer:
1. Disabilitare la generazione dei link pubblici (feature flag).
2. Transizione morbida verso l'Opzione A (Cloud Relay E2E) riutilizzando lo stesso form UI ma cambiando l'endpoint di submit verso il cloud criptato.

## Supersedes / Superseded By

- Supersedes: Nessuno (prima implementazione di client-facing portal).
- Superseded by: N/A.
