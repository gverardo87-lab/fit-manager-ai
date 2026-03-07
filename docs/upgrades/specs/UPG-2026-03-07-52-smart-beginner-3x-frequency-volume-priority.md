# UPG-2026-03-07-52 — SMART Beginner 3x Frequency Priority by Weekly Volume

## Contesto

Dopo `UPG-2026-03-07-48` e `UPG-2026-03-07-51`, il `full_body 3x` principiante aveva ancora un difetto reale:

- `bicipiti` e `polpacci` potevano migliorare
- `deltoide_laterale` poteva ancora restare sotto MEV e addirittura a `0x/settimana`

Il problema non era nell'analyzer ma nell'ordine di priorita' interno del planner: gli slot accessori venivano ancora spesi senza dare precedenza ai muscoli veramente sotto-target.

## Decisione

Raffinare `_apply_beginner_full_body_frequency_corrections()` in `plan_builder.py` con due regole:

1. `_BEGINNER_FULL_BODY_FREQUENCY_MUSCLES` diventa ordinato, non piu' `set`
2. i piccoli distretti vengono processati in base al loro stato settimanale reale:
   - prima sotto MEV
   - poi sotto MAV_min
   - poi dentro MAV
   - infine sopra MAV_max

Inoltre, se un muscolo e' gia' a `mav_max`, la correzione frequency-aware lo salta del tutto.

## Obiettivo

Riservare gli slot accessori beginner ai muscoli davvero carenti, con priorita' pratica a `deltoide_laterale`, evitando che bicipiti/tricipiti/polpacci assorbano spazio quando sono gia' oltre il bisogno settimanale.

## Impatto

- planner SMART piu' coerente per `principiante 3x`
- riduzione dei falsi negativi di frequenza sui piccoli distretti
- nessun cambio API
- nessun cambio UI
- nessun cambio nel core analyzer

## Verifica

- `venv\Scripts\ruff.exe check api/services/training_science/plan_builder.py`

## Rischi Residui

- `Quad : Ham` resta ancora il principale warning biomeccanico beginner
- il recovery overlap `Full Body B -> Full Body C` puo' restare dominante
- la correzione resta locale al caso `full_body 3x` principiante, non e' ancora un solver globale di scheduling/accessory caps
