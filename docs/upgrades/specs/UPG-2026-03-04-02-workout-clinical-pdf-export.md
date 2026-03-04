# Patch Spec - Workout Clinical Export (HTML -> PDF)

## Metadata

- Upgrade ID: UPG-2026-03-04-02
- Date: 2026-03-04
- Owner: Codex
- Area: Workout Builder (`/schede/[id]`)
- Priority: high
- Target release: 2026-03-04 (`codex_01`)
- Status: implemented

## Problem

L'export scheda era centrato su Excel, mentre la prima cliente richiedeva un output clinico diretto in PDF
con branding personalizzato e fotografie esercizi nel layout finale.
Inoltre il flusso popup/browser per la stampa risultava fragile.

## Desired Outcome

Fornire un export clinico robusto e professionale con:
- layout tipo "scheda clinica" multi-pagina;
- logo cliente in copertina e in preview;
- foto esercizi incluse nel file scaricato;
- doppio formato operativo: anteprima stampabile + file clinico scaricabile.

## Scope

- In scope:
  - nuovo generatore clinico in `frontend/src/lib/export-workout-pdf.ts` (HTML locale ottimizzato per stampa PDF);
  - bottoni export aggiornati (`Scarica Clinico`, `Anteprima`) in `ExportButtons.tsx`;
  - gestione logo cliente (upload/change/remove) con persistenza per trainer in localStorage;
  - embedding immagini esercizi start/end in base64 nel file clinico.
- Out of scope:
  - modifica pipeline backend media;
  - rimozione export Excel legacy.

## Impact Map

- Files/modules toccati:
  - `frontend/src/lib/export-workout-pdf.ts`
  - `frontend/src/components/workouts/ExportButtons.tsx`
  - `frontend/src/components/workouts/WorkoutPreview.tsx`
  - `frontend/src/app/(dashboard)/schede/[id]/page.tsx`
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - preview corrente invariata;
  - nessun blocco popup richiesto per il file clinico;
  - mantenimento type safety TS.

## Acceptance Criteria

- Funzionale:
  - click su `Scarica Clinico` produce file `.html` locale pronto per `Stampa > Salva come PDF`;
  - logo cliente visibile in copertina se presente;
  - foto start/end visibili dove disponibili.
- UX:
  - export senza popup bloccati dal browser;
  - mantenimento bottone anteprima per formato operativo esistente.
- Tecnico:
  - lint verde sui file frontend toccati;
  - fallback gestito quando foto non disponibili.

## Test Plan

- Manual checks:
  - download file clinico da scheda con e senza logo;
  - verifica foto esercizi in card principali e blocchi;
  - stampa da file locale in PDF.
- Build/Lint gates:
  - `npm --prefix frontend run lint -- "src/lib/export-workout-pdf.ts" "src/components/workouts/ExportButtons.tsx" "src/components/workouts/WorkoutPreview.tsx"`

## Risks and Mitigation

- Rischio 1: immagini non caricate nel file scaricato.
  - Mitigazione 1: prefetch con `Promise.allSettled` + embedding base64 + warning utente.

- Rischio 2: regressione UX export precedente.
  - Mitigazione 2: mantenimento bottone `Anteprima` separato.

## Rollback Plan

- Revert commit `d49b3d0` e ripristino export precedente.

## Notes

- Commit implementazione: `d49b3d0`.
