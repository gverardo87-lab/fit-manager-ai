# Patch Spec - Workout Clinical Print Pagination and Density

## Metadata

- Upgrade ID: UPG-2026-03-04-03
- Date: 2026-03-04
- Owner: Codex
- Area: Workout Clinical Export (`export-workout-pdf.ts`)
- Priority: high
- Target release: 2026-03-04 (`codex_01`)
- Status: implemented

## Problem

La stampa del file clinico mostrava:
- differenze cromatiche rispetto all'anteprima;
- impaginazione non stabile (spazi bianchi ampi e sezioni spezzate male);
- eccessiva altezza media delle foto nelle sezioni principali/blocchi, con aumento pagine e costo stampa.

## Desired Outcome

Allineare la resa stampa all'anteprima e ridurre densita verticale senza perdere leggibilita:
- colori coerenti in print;
- break pagina piu intelligenti;
- riduzione altezza foto e padding per -10/-15% pagine su schede dense.

## Scope

- In scope:
  - tuning CSS `@media print` (color adjust, page break, tabelle/blocchi);
  - aumento logo copertina;
  - compattazione proporzioni immagini e spacing nelle card esercizio e nei blocchi.
- Out of scope:
  - redesign visuale completo;
  - cambi backend o struttura dati workout.

## Impact Map

- Files/modules toccati:
  - `frontend/src/lib/export-workout-pdf.ts`
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - identita visuale clinica;
  - struttura a sezioni (avviamento/principale/stretching);
  - presenza foto esercizi.

## Acceptance Criteria

- Funzionale:
  - stampa da browser conserva i colori principali;
  - ridotti vuoti anomali tra sezioni e pagine;
  - blocchi strutturati (superset/emom/tabata/...) restano leggibili.
- UX:
  - logo copertina piu visibile;
  - scheda clinica piu compatta senza effetto "ammassato".
- Tecnico:
  - nessun errore lint su `export-workout-pdf.ts`.

## Test Plan

- Manual checks:
  - confronto visivo: anteprima schermo vs anteprima stampa;
  - casi con sessioni leggere e dense (molti blocchi/foto);
  - verifica non spezzare righe critiche in tabella.
- Build/Lint gates:
  - `npm --prefix frontend run lint -- "src/lib/export-workout-pdf.ts"`

## Risks and Mitigation

- Rischio 1: compattazione eccessiva che riduce leggibilita.
  - Mitigazione 1: riduzione moderata (10-15%) su foto/padding, senza toccare gerarchia tipografica.

- Rischio 2: regressioni print tra browser diversi.
  - Mitigazione 2: uso combinato `print-color-adjust` e regole `page-break` conservative.

## Rollback Plan

- Revert commit `2cf8cd4` e `a502f71`.

## Notes

- Commit implementazione: `2cf8cd4`, `a502f71`.
