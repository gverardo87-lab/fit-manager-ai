# UPG-2026-03-09-28 - Rinnovi & Incassi visual redesign v1

## Summary

Primo redesign grafico del workspace `Rinnovi & Incassi`, mantenendo invariata tutta la logica runtime.

Il microstep introduce:

- hero finance piu forte e meno neutrale
- metric tiles piu leggibili e meno "dashboard anni 90"
- filtro workspace come segmented rail scuro, non piu pulsanti generici
- card `finance` dedicate con linguaggio visivo caldo/editoriale
- detail panel `finance` dedicato, senza contaminare `Oggi`

## Goal

Dare a `Rinnovi & Incassi` un'identita propria:

- privata
- premium
- operativa
- chiaramente diversa sia dalla dashboard sia da `Oggi`

## Scope

### Included

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`

### Excluded

- nessun cambio API
- nessun cambio query/runtime
- nessun nuovo case kind
- nessun redesign di `Oggi`

## Design decisions

### 1. Finance-only visual variant

`WorkspaceCaseCard` e `WorkspaceDetailPanel` ricevono `variant="finance"`:

- `Oggi` conserva il look operativo neutro
- `Rinnovi & Incassi` usa superfici, contrasti e call-to-action dedicate

### 2. Hero meno neutro

La testata finance passa da card chiara standard a pannello caldo con:

- atmosfera piu privata
- messaggio piu netto
- metric tiles 2x2 con numeri dominanti

### 3. Queue piu "scrivania", meno lista admin

Le sezioni della queue non sono piu blocchi bianchi ripetitivi:

- ogni bucket ha tono proprio
- la gerarchia dei casi e piu leggibile
- il backlog `waiting` resta espandibile ma non opaco

### 4. Detail panel piu decisionale

Il pannello destro mette in evidenza:

- azione consigliata
- quadro economico
- segnali
- contesto
- timeline

con una grammatica visiva coerente con il dominio finance.

## Invariants preserved

- nessuna modifica ai dati mostrati
- nessuna modifica al ranking
- nessuna modifica alle query
- nessuna esposizione di dati finance fuori dal workspace dedicato

## Verification

- `npm --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx"`
- smoke route su `http://localhost:3001/rinnovi-incassi` con cookie auth valido

## Residual risks

- il redesign e mirato a `Rinnovi & Incassi`, quindi i componenti shared hanno ora due grammatiche visuali da mantenere
- non e stata fatta una review visuale pixel-perfect in browser headful dentro questo microstep
- se il linguaggio finance funziona bene, il prossimo passo corretto e un redesign separato di `Oggi`, non un merge dei due look
