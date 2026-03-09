# UPG-2026-03-09-24 - Renewals & Cash Finance Dominance v1

## Context

Il workspace `Rinnovi & Incassi` ora espone piu famiglie finance utili:

- `payment_overdue`
- `payment_due_soon`
- `contract_renewal_due`
- `recurring_expense_due`

Sul dataset reale DEV, almeno un contratto compariva contemporaneamente come:

- `payment_due_soon`
- `contract_renewal_due`

Questo produce due righe concorrenti sullo stesso contratto, pur avendo un solo prossimo gesto economico veramente corretto.

## Objective

Introdurre una regola di dominanza finance-specifica, deterministica e spiegabile:

- se un contratto ha `payment_due_soon`, il relativo `contract_renewal_due` non viene generato

## Scope

### In

- `api/services/workspace_engine.py`
- `tests/test_workspace_today.py`
- sync docs governance

### Out

- nessuna nuova UI
- nessun nuovo endpoint
- nessuna mutation
- nessun impatto su `Oggi`

## Hard Rule

### Dominance

`payment_due_soon` domina `contract_renewal_due` sullo stesso `contract_id`.

Traduzione runtime:

- si costruiscono prima i case `payment_due_soon`
- si estrae l'insieme `due_soon_contract_ids`
- `contract_renewal_due` non viene generato per quei contratti

## Rationale

Quando un contratto ha gia una rata imminente:

- il gesto economico corretto e gestire l'incasso vicino
- il rinnovo non deve competere come seconda riga nello stesso orizzonte breve
- il rinnovo riapparira automaticamente quando la scadenza imminente uscira dal motore

Questa scelta e piu rigorosa di un semplice downgrade bucket:

- evita duplicazione vera
- mantiene un solo case per contratto nella finestra breve
- non nasconde dati strutturalmente, li differisce al momento corretto

## Invariants Preserved

- `payment_overdue` continua a dominare `payment_due_soon`
- `contract_renewal_due` continua a esistere per i contratti senza scadenze imminenti
- `renewals_cash` resta il solo contesto con importi completi
- `Oggi` non cambia

## Verification Target

- contratto con rata entro 7 giorni + contratto in scadenza -> visibile solo `payment_due_soon`
- contratto con rinnovo ma senza rata entro 7 giorni -> `contract_renewal_due` ancora visibile
- smoke test reale DEV: overlap `payment_due_soon ∩ contract_renewal_due` deve scendere a `0`

## Residual Risks

- la dominanza e corretta sullo stesso contratto, ma non raggruppa ancora piu contratti dello stesso cliente
- se in futuro servira un livello piu alto, la mossa giusta sara un merge finance per cliente, non una nuova proliferazione di card

## Next Smallest Step

Se il workspace finance resta leggibile sul dataset reale:

1. valutare un cap viewport anche su `renewals_cash`
2. oppure introdurre un micro-summary backlog per bucket invece di mostrare tutte le righe upcoming
