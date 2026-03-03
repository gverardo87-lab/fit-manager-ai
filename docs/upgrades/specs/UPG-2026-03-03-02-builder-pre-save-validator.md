# Patch Spec - Builder Pre-Save Validator

## Metadata

- Upgrade ID: UPG-2026-03-03-02
- Date: 2026-03-03
- Owner: gvera + codex
- Area: Workout Builder (`/schede/[id]`)
- Priority: high
- Target release: 2026-03-03 (`codex_01`)
- Status: implemented

## Problem

Quando il salvataggio fallisce, l'utente riceve un errore generico e non capisce dove intervenire.
Caso tipico: dati sessione/blocco formalmente incompleti (es. blocco senza esercizi) che causano errore in update sessioni.

## Desired Outcome

Prima del salvataggio, il builder valida localmente i dati e mostra una lista issue breve e actionable.
Il PT deve capire in meno di 5 secondi cosa correggere e dove.
Principio guida: avvisare molto, bloccare pochissimo.

## Scope

- In scope:
  - Validatore pre-save nel builder.
  - Issue list con severita e CTA contestuale.
  - Blocco salvataggio solo su issue critiche estreme.
  - Normalizzazione/sanificazione automatica dei campi non validi quando possibile.
  - Compatibilita con `Ctrl+S` e bottone `Salva`.
- Out of scope:
  - Cambi schema backend.
  - Nuovi endpoint API.
  - Refactor esteso dei componenti blocchi/sessioni.

## Impact Map

- Files/modules da toccare:
  - `frontend/src/app/(dashboard)/schede/[id]/page.tsx`
  - `frontend/src/components/workouts/SessionCard.tsx` (solo se serve highlight/callback)
  - `frontend/src/components/workouts/BlockCard.tsx` (solo se serve CTA mirata)
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - Save flow attuale (manuale + `Ctrl+S`)
  - Protezione unsaved changes
  - Pattern UI esistente (messaggi chiari, niente blocchi opachi)

## Acceptance Criteria

- Funzionale:
  - Se esiste almeno un blocco senza esercizi, il salvataggio procede e il blocco vuoto viene escluso con avviso.
  - Se ci sono campi fuori range, il salvataggio procede con normalizzazione e avviso.
  - Se una sessione/scheda viene salvata vuota, il salvataggio procede con avviso esplicito di bozza incompleta.
  - Se viene inserito un carico elevato, il salvataggio procede con warning non bloccante.
  - Se una sessione ha issue critiche estreme, l'utente vede elenco issue con riferimento sessione/blocco.
  - `Ctrl+S` rispetta la validazione esattamente come il bottone `Salva`.
- UX:
  - Messaggio sintetico: cosa non va + azione consigliata.
  - CTA contestuale (es. "Aggiungi esercizio al blocco" o "Rimuovi blocco vuoto").
  - Nessun errore generico se il problema e gia noto lato client.
  - Nessun blocco non necessario: l'utente puo salvare anche lavoro parziale.
- Tecnico:
  - Nessun `any`.
  - Nessuna regressione su save di schede valide.
  - Build frontend verde.

## Test Plan

- Unit/Integration:
  - (se introdotta utility pura) test su `validateWorkoutSessions`.
- Manual checks:
  - Caso A: blocco con 0 esercizi -> save consentito + warning + blocco escluso.
  - Caso B: campi numerici fuori range -> save consentito + warning + valori normalizzati.
  - Caso C: scheda/sessione vuota -> save consentito + warning bozza incompleta.
  - Caso D: carico elevato (es. 180 kg) -> save consentito + warning.
  - Caso E: scheda valida -> save OK senza warning.
  - Caso F: `Ctrl+S` su caso A/B/C/D/E -> comportamento identico al click su `Salva`.
  - Caso G: caso critico estremo (es. zero sessioni) -> save bloccato con messaggio chiaro.
- Build/Lint gates:
  - `cd frontend && npx next build`

## Risks and Mitigation

- Rischio 1: false positive su validazioni troppo aggressive.
  - Mitigazione: classificare issue in `critical` vs `warning`; bloccare solo `critical`.
- Rischio 2: UX rumorosa con troppe notifiche.
  - Mitigazione: una sola surface principale (issue list compatta) + toast sintetico.

## Rollback Plan

- Ripristinare il flusso save precedente rimuovendo la chiamata al validatore in `handleSave`.
- Non richiede migrazioni o rollback backend.

## Notes

- Collegato a feedback reale: errore update sessioni percepito come generico/non actionable.
- Implementazione principale: `62e364e` (`page.tsx` + warning assistivi pre-save).
