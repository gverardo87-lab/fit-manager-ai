# UPG-2026-03-10-02 - Rinnovi & Incassi detail panel compaction v1

## Summary

Compattazione strutturale del dossier destro di `Rinnovi & Incassi`:

- ridotta altezza minima del pannello
- ridotti padding e scala tipografica nelle aree secondarie
- trasformato il body in una composizione piu densa
- rimossi separatori verticalmente costosi in favore di card-sezione piu piccole

## Goal

Ridurre scroll e spazio morto nel pannello dettaglio senza perdere:

- azione consigliata
- segnali chiave
- contesto collegato
- timeline sintetica

## Scope

### Included

- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`

### Excluded

- nessun cambio backend
- nessun cambio query
- nessun cambio ranking
- nessun redesign della queue finance

## Design decisions

### 1. Shorter panel shell

Il pannello passa da una presenza troppo alta e respirata a una shell piu corta:

- `min-height` ridotta
- header piu compatto
- blocco esposizione piu stretto

### 2. Dense content grid

`Perche ora` e `Contesto collegato` condividono ora una stessa fascia a griglia su viewport ampi:

- meno stacking inutile
- migliore uso dello spazio orizzontale
- scansione piu rapida

### 3. Lighter action block

Il blocco `Azione consigliata` resta dominante, ma:

- usa meno padding
- usa bottoni piu bassi
- evita di rubare viewport al resto del dossier

### 4. Timeline trimmed

La timeline mantiene il ruolo informativo ma:

- usa righe piu compatte
- riduce spazi tra marker, testo e CTA

## Verification

- `npm --prefix frontend run lint -- "src/components/workspace/WorkspaceDetailPanel.tsx"`

## Residual risks

- la queue e il dossier ora sono piu vicini come densita, ma i badge shared del workspace possono ancora risultare piu “system” che “finance-native”
- per il giudizio finale serve review headful reale su `3001`
