# UPG-2026-03-09-26 - Renewals & Cash Empty Bucket Suppression v1

## Context

Dopo il viewport budget per bucket, il workspace `Rinnovi & Incassi` era gia piu corto, ma continuava a sprecare altezza verticale rendendo sezioni vuote come `Critici` o `Oggi` anche quando il dataset reale non conteneva casi in quei bucket.

## Objective

Sopprimere i bucket vuoti nella shell finance, lasciando in pagina solo sezioni con lavoro reale.

## Scope

### In

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- sync docs governance

### Out

- nessun cambio API
- nessun cambio runtime workspace
- nessuna mutation

## Decision

La shell finance rende ora una sezione solo se il totale server-side del relativo bucket e maggiore di zero:

- `Critici` -> solo se `criticalTotal > 0`
- `Oggi` -> solo se `todayTotal > 0`
- `Entro 7 giorni` -> solo se `upcomingTotal > 0`
- `Da pianificare` resta gia condizionale su `waitingTotal > 0`

## Why

Un bucket vuoto in questa pagina non aiuta il trainer:

- non aumenta la comprensione
- aumenta la scrollata
- comunica lavoro assente con un pannello in piu

Meglio mostrare solo le famiglie che hanno davvero pressione aperta.

## Verification Target

- `eslint` su `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- review visuale sui casi reali:
  - se `todayTotal = 0`, il bucket `Oggi` non compare
  - se `criticalTotal = 0`, il bucket `Critici` non compare

## Residual Risks

- il bucket suppression vive solo nella shell finance, non nel contratto API
- se in futuro servira una descrizione esplicita di bucket assenti, andra trattata come copy di summary, non come card vuota
