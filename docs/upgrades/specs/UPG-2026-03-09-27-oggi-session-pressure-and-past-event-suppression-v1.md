# UPG-2026-03-09-27 - Oggi session pressure and past event suppression v1

## Summary

Microstep backend-only sul workspace `Oggi` per fissare due invarianti operative:

1. se esistono `session_imminent`, i `payment_overdue` non devono comparire in `workspace=today`
2. una sessione terminata non deve piu restare un caso prioritario piu tardi nella stessa giornata

## Why

Sul dataset reale il trainer aveva due problemi di fiducia:

- `Oggi` poteva ancora mostrare arretrati economici mentre la giornata era dominata dalle sessioni
- a tarda sera una sessione del mattino poteva restare nel motore come caso `now`, perche il bucket delle sessioni non distingueva in modo duro gli eventi gia finiti

Questa combinazione rompe la promessa della pagina: `Oggi` deve seguire il tempo reale del trainer, non il solo calendario del giorno.

## Scope

### Included

- soppressione dei `payment_overdue` dal workspace `today` quando nello snapshot esiste almeno un `session_imminent`
- esclusione delle sessioni gia concluse da `session_cases` e `agenda_items`
- riallineamento di `build_workspace_today()` e `build_workspace_case_list(workspace="today")`
- test backend mirati

### Excluded

- nessun cambio UI
- nessun cambio ai workspace finance
- nessuna mutation nuova
- nessuna modifica alla gerarchia `renewals_cash`

## Runtime rules

### Rule 1: finance suppression under session pressure

Se nello snapshot `today` esiste almeno un caso `session_imminent`, allora i casi `payment_overdue`:

- restano visibili in `workspace=renewals_cash`
- non compaiono in `workspace=today`
- non compaiono nel `focus_case` di `Oggi`
- non contribuiscono ai summary count di `today`

### Rule 2: past sessions are not operational

Per gli eventi agenda del giorno corrente:

- `current`: `data_inizio <= now <= data_fine`
- `upcoming`: `data_inizio > now`
- `past`: `data_fine < now`

Gli eventi `past`:

- non generano `session_imminent`
- non entrano nella `WorkspaceTodayAgenda`
- non possono piu determinare il `focus_case`

## Files

- `api/services/workspace_engine.py`
- `tests/test_workspace_today.py`

## Verification

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`
- smoke HTTP reale su `http://localhost:8001`

## Expected outcome

- di mattina o nel pomeriggio, con sessioni ancora operative, `Oggi` puo concentrarsi solo sul lavoro agenda
- a fine giornata, finite le sessioni, `Oggi` torna a far emergere gli incassi scaduti
- nessuna sessione del mattino resta prioritaria alle 21:00
