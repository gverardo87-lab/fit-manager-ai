# UPG-2026-03-09-25 - Renewals & Cash Bucketed Viewport Shell v1

## Context

`Rinnovi & Incassi` era nato sopra `GET /api/workspace/cases?workspace=renewals_cash`, ma la shell iniziale caricava una lista larga e rendeva i bucket solo dopo il fetch completo.

Problema:

- la page shell vedeva troppi casi insieme quando il dataset cresceva
- la riduzione del rumore dipendeva dal rendering locale, non da cap espliciti
- il numero di casi visibili per bucket non era governato in modo stabile

## Objective

Introdurre un viewport budget per il workspace finance senza creare nuovi endpoint e senza duplicare logica backend.

## Scope

### In

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- sync docs governance

### Out

- nessun cambio API
- nessun cambio `workspace_engine`
- nessuna mutation
- nessun impatto su `Oggi`

## Decision

La shell finance usa ora query separate per bucket, tutte server-side:

- `now`
- `today`
- `upcoming_3d`
- `upcoming_7d`
- `waiting` solo on demand

Questo mantiene la logica di filtro/paginazione nel backend esistente e toglie al frontend il compito di tagliare una lista monolitica.

## Viewport Limits

- `now = 3`
- `today = 4`
- `upcoming_3d = 3`
- `upcoming_7d = 3`
- `waiting = 6` solo quando l'utente espande la sezione

## Resulting Behavior

- header e contatori restano ancorati al `summary` server-side
- ogni sezione mostra solo il proprio sottoinsieme paginato
- la pagina comunica esplicitamente quando sta mostrando una vista iniziale (`Mostro X su Y`)
- la sezione `Da pianificare` non consuma rete finche resta chiusa

## Why This Is The Right Step

Questo microstep evita un falso backend-first:

- non inventa un nuovo endpoint per nascondere un problema di rendering
- non slicea localmente una lista gia troppo grande
- non rompe il contratto generale `workspace/cases`

Si limita a usare il contratto giusto nel modo giusto.

## Verification Target

- `eslint` sulla page shell finance
- verifica manuale che:
  - la header note usi `summary` + casi visibili reali
  - i badge bucket mostrino il totale server-side
  - `waiting` faccia fetch solo quando espanso

## Residual Risks

- il budget vive ancora nella shell finance, non in uno snapshot dedicato come `today`
- se il workspace finance diventera molto piu ricco, il passo successivo corretto sara una surface summary dedicata, non una crescita dei `page_size`

## Next Smallest Step

Se il shell finance risulta finalmente leggibile:

1. valutare se introdurre una mini surface read-only dedicata per `renewals_cash`
2. oppure fermarsi e osservare il comportamento reale prima di aggiungere altro
