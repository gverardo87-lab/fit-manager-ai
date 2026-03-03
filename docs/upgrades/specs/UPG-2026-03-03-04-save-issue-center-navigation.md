# Patch Spec - Save Issue Center Navigation

## Metadata

- Upgrade ID: UPG-2026-03-03-04
- Date: 2026-03-03
- Owner: gvera + codex
- Area: Workout Builder (`/schede/[id]`)
- Priority: medium
- Target release: 2026-03-03 (`codex_01`)
- Status: in_progress

## Problem

Il pannello avvisi di salvataggio mostra solo i primi 3 item.
Quando gli avvisi sono molti, il PT non riesce a leggere tutto senza rilanciare il salvataggio
e deve cercare manualmente i punti da correggere.
Inoltre alcuni warning risultano non navigabili dopo il save quando gli ID locali vengono riallineati con quelli server.

## Desired Outcome

Rendere il pannello avvisi navigabile: espansione completa e scorciatoia per saltare subito al primo punto da rivedere.
Principio: informare rapidamente senza introdurre blocchi.

## Scope

- In scope:
  - toggle "mostra tutti / mostra meno" sugli avvisi salvataggio
  - CTA "vai al primo punto da rivedere" se esiste target navigabile
  - fallback navigazione su `sessionNumber` (target stabile anche dopo riallineamento ID)
  - catalogazione warning per categoria (bozza, normalizzazione, sicurezza, integrita)
  - action nel toast per portare l'utente direttamente agli avvisi
  - reset stato espansione quando gli avvisi vengono invalidati
- Out of scope:
  - nuove validazioni pre-save
  - modifiche backend

## Impact Map

- Files/modules da toccare:
  - `frontend/src/app/(dashboard)/schede/[id]/page.tsx`
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - salvataggio non bloccante per warning
  - shortcut `Ctrl+S` invariata
  - comportamento attuale di jump sugli avvisi cliccabili

## Acceptance Criteria

- Funzionale:
  - con >3 avvisi il PT puo espandere la lista completa.
  - il PT puo saltare al primo punto correggibile con un click.
  - se il target per ID non esiste, la navigazione fa fallback alla sessione corretta.
- UX:
  - il pannello resta sintetico di default.
  - le categorie warning sono leggibili a colpo d'occhio.
  - nessun nuovo attrito nel flusso di salvataggio.
- Tecnico:
  - nessun `any`.
  - build frontend verde.

## Test Plan

- Manual checks:
  - generare >3 warning e verificare toggle espandi/chiudi.
  - verificare CTA "vai al primo punto da rivedere".
  - salvare una scheda con elementi nuovi (ID locali negativi) e verificare jump comunque funzionante.
  - verificare action del toast "Rivedi avvisi".
  - modificare la scheda dopo warning: avvisi e stato espansione si resettano.
- Build/Lint gates:
  - `cd frontend && npx next build`

## Risks and Mitigation

- Rischio 1: pannello troppo rumoroso.
  - Mitigazione: default compatto (prime 3 righe), espansione solo on-demand.

## Rollback Plan

- Rimuovere stato `saveIssuesExpanded` e CTA aggiuntive, tornando alla lista ridotta statica.

## Notes

- Patch UX incrementale sul pre-save validator (UPG-2026-03-03-02).
