# Patch Spec Template - Portale Clienti (Anamnesi Self-Service)

## Metadata

- Upgrade ID: UPG-2026-03-06-01
- Date: 2026-03-05
- Owner: G. Verardo (Sviluppatore)
- Area: Client Portal (Frontend & API)
- Priority: high
- Target release: Wave 4

## Problem

Attualmente, l'inserimento dei dati di anamnesi medica, sportiva e degli obiettivi per un nuovo cliente e' un processo manuale in capo al personal trainer.
La prassi comune (uso di Google Forms via WhatsApp) viola il paradigma "zero cloud" e crea un disallineamento dei dati rispetto al CRM locale.
Il trainer perde tempo in data entry e il cliente percepisce un'esperienza frammentata (messaggistica + tool esterni).

## Desired Outcome

Il trainer genera con un clic in FitManager un link univoco monouso e temporaneo per l'anamnesi.
Il link, inviato su WhatsApp, porta il cliente su una Web App nativa e curata (mobile-first), esposta via Tailscale Funnel.
Il cliente compila l'anamnesi e i dati vengono salvati direttamente e in modo sicuro nel database SQLite locale del trainer, senza transitare da cloud terzi.

## Scope

- In scope:
  - Generazione Token (JWT/UUID) e scadenza.
  - Generazione link pubblico (`https://<tailscale-funnel>/public/anamnesi/<token>`).
  - Creazione endpoint FastAPI pubblici (`GET /public/anamnesi/validate`, `POST /public/anamnesi/submit`) con Rate Limiting Bouncer.
  - Creazione UI Frontend (Next.js) `/public/anamnesi/[token]` in modalita' Kiosk (no sidebar, no auth richiesta).
  - Ingestione automatica dei dati Pydantic e invalidazione token.
- Out of scope:
  - Booking/Appuntamenti self-service (previsti per upgrade successivi).
  - Gestione schede d'allenamento pubbliche per il cliente.

## Impact Map

- Files/modules da toccare:
  - `api/routers/public_portal.py` (Nuovo router)
  - `api/models/token.py` (Nuova tabella `ShareableToken` o JWT statelss)
  - `api/schemas/public.py` (Validazione payload)
  - `frontend/src/app/public/anamnesi/[token]/page.tsx` (Nuova route)
  - Profilo Cliente UI (Aggiunta bottone "Richiedi Anamnesi").
- Layer coinvolti: `api` | `frontend`
- Invarianti da preservare:
  - Nessun dato sensibile esposto senza token valido.
  - Rate limiting stretto per prevenire brute-force o spam DDoS tramite il Funnel pubblico.
  - Zero Cloud Policy.

## Acceptance Criteria

- Funzionale: Il link generato apre il modulo anamnesi; il submit salva i dati nel profilo cliente corretto.
- UX: Form reattivo, validazione campi in tempo reale, feedback di successo al termine.
- Tecnico (type sync, query invalidation, security):
  - Il token deve essere monouso e avere scadenza (es. 48 ore).
  - Type sync garantito tra `schemas/public.py` e `frontend/types`.
  - Invalidation query (React Query) per il profilo cliente aggiornato quando il trainer riapre il CRM.

## Test Plan

- Unit/Integration:
  - Test di validazione del token (scaduto, non esistente, valido).
  - Test della POST `/public/anamnesi/submit` con validazione dati.
- Manual checks:
  - Test E2E tramite browser mobile connesso a rete 4G, simulando il routing di Tailscale Funnel.
- Build/Lint gates:
  - `check-all.sh` per garantire assenza di errori TypeScript e Ruff.

## Risks and Mitigation

- Rischio 1: Il PC del trainer e' spento quando il cliente tenta l'accesso (timeout o 502 Bad Gateway).
- Mitigazione 1: Messaggio chiaro lato CRM ("Il link funzionera' finche' FitManager e' aperto") e pagina di cortesia statica se Tailscale Funnel supporta custom offline pages.
- Rischio 2: Spam bots o DDoS via Tailscale Funnel.
- Mitigazione 2: Implementare Rate Limiting IP-based su `public_portal.py` e/o CAPTCHA leggero invisibile.

## Rollback Plan

- Disabilitazione feature flag `ENABLE_PUBLIC_PORTAL=false` nel file `.env`, che forza tutti gli endpoint pubblici a restituire 404.

## Notes

- Link a issue/PR/commit: Vedere ADR `0001-client-portal-tailscale-funnel.md` per il contesto architetturale.
