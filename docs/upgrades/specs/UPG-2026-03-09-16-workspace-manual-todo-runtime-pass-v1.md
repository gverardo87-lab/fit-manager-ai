# UPG-2026-03-09-16 - Workspace manual todo runtime pass v1

## Context

`UPG-2026-03-09-15` ha formalizzato la policy matematica dei `todo_manual` dentro `Oggi`. Il runtime pero continuava a usare la semantica precedente:

- i todo senza scadenza entravano in `today`;
- i promemoria manuali potevano occupare troppi slot visibili;
- l'ordinamento tra todo non usava ancora `urgenza + eta`.

## Objective

Tradurre la policy approvata nel runtime di `workspace_engine.py` senza introdurre:

- nuovi `case_kind`;
- nuove superfici UI;
- inferenze da testo libero;
- contesto fittizio cliente/contratto/piano.

## Runtime Changes

### Bucket logic

- `todo` senza `data_scadenza` -> `waiting`
- `todo` non entra mai in `now`
- `todo` con scadenza:
  - overdue / today -> `today`
  - `1..3 giorni` -> `upcoming_3d`
  - `4..7 giorni` -> `upcoming_7d`
  - `>7 giorni` -> `waiting`

### Severity logic

- `<= -7 giorni` -> `high`
- `-6 .. 0 giorni` -> `medium`
- futuro / no due date -> `low`
- `critical` continua a non essere usato per `todo_manual`

### Todo score

Il motore ora ordina i promemoria con score deterministico:

```text
todo_score = urgency_score + age_bonus
```

Tie-break stabili:

1. `data_scadenza`
2. `created_at` locale
3. `todo_id`

### Viewport pressure

Il budget backend di `today` ora include anche il cap dinamico dei promemoria manuali:

```text
manual_today_cap =
  0  se structural_now_count >= 1
  1  se structural_now_count == 0 e structural_today_count >= 2
  2  altrimenti
```

Conseguenze:

- se esiste lavoro strutturale in `now`, i promemoria manuali non occupano la viewport di `today`
- se la giornata e gia piena di casi strutturali, i promemoria restano al massimo uno
- in giornate leggere possono comparire due todo manuali visibili

## Tests Added

- solo `todo_manual` dovuti oggi:
  - `today.total` resta completo
  - `today.items` visibili vengono capped a `2`
- `session_imminent` in `now` + `todo_manual` dovuto oggi:
  - il todo non compare nel `today` visibile
  - resta disponibile in `build_workspace_case_list()`
- `todo_manual` senza data:
  - non entra nella lista casi `workspace=today`

## Verification

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`
- `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py -p no:cacheprovider`
  - expected local outcome: blocked by the broken project `venv` launcher already known in this repo

## Residual risks

- i `todo_manual` sono ancora righe individuali; questo pass non introduce grouping o summary case
- il modello `Todo` non ha riferimenti entity-safe, quindi il motore non puo ancora misurare impatto cliente/contratto/piano

## Next smallest step

Se il rumore dei promemoria resta alto anche con il cap dinamico, introdurre una strategia di grouping per gli extra `todo_manual`, ma solo dopo osservazione reale su `crm_dev.db`.
