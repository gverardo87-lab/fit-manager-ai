# UPG-2026-03-10-01 - Rinnovi & Incassi palette realignment v1

## Summary

Riallineamento cromatico del workspace `Rinnovi & Incassi` dopo review UX negativa sul tema dark-heavy:

- abbandonato il quasi-nero come linguaggio dominante
- introdotta una palette `pearl + petrol + clay`
- aumentato il contrasto reale tra canvas, surface, testo primario e meta testo
- corretto il bottone `Dettaglio` sui layout stacked, che ora porta davvero al pannello dossier

## Goal

Portare il workspace finance verso un look:

- professionale
- premium
- piu caldo e piu leggibile
- meno tech-dark, meno piatto, meno aggressivo

adatto a una professionista chinesiologa senza scivolare ne nel beauty-pink ne nel dark admin generico.

## Scope

### Included

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`

### Excluded

- nessun cambio backend
- nessun cambio query o ranking
- nessun nuovo endpoint
- nessun redesign di `Oggi`

## Palette decision

### Primary neutrals

- canvas: pearl / ivory soft
- surface: white-warm
- border: taupe light
- text primary: slate deep
- text secondary: slate muted

### Functional accents

- primary action: petrol
- warm support accent: clay
- critical: soft red, non neon
- warning: warm amber

## Design rationale

La direzione e coerente con pattern ricorrenti dei migliori sistemi business:

- neutrali chiari come base
- un solo primary serio e affidabile
- colori semantici usati come segnali, non come rumore
- contrasto tra testo primario e meta testo molto piu netto del tema precedente

Nel workspace finance questo significa:

- queue chiara e leggibile
- dossier destro coerente con la stessa palette
- CTA chiaramente distinguibili
- minore affaticamento visivo rispetto al dark quasi assoluto

## Interaction fix

`Dettaglio` non e piu una affordance ambigua:

- seleziona il caso
- su viewport stacked scrolla verso il dossier
- mantiene invariato il contratto dati

## Verification

- `npm --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/components/workspace/workspace-ui.ts"`

## Residual risks

- la queue e piu leggibile, ma i badge `kind/severity` usano ancora il sistema shared esistente e potrebbero meritare un pass cromatico dedicato
- il dossier destro e molto migliore, ma puo ancora essere compattato strutturalmente in un microstep successivo
- la validazione finale richiede review headful reale su `3001`
