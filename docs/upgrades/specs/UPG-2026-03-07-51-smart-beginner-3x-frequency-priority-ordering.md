# UPG-2026-03-07-51 - SMART Beginner 3x Frequency Priority Ordering

## Context

Il microstep precedente sul `3x beginner` aveva introdotto correzioni frequency-aware per:

- deltoide laterale
- bicipiti
- tricipiti
- polpacci

ma i warning residui su `bicipiti` e `polpacci` mostravano che la correzione arrivava ancora troppo tardi nel planner.

Diagnosi:

- la correzione veniva eseguita dopo la compensazione volume generica;
- nel `full_body 3x` beginner i pochi slot accessori disponibili possono essere gia' saturati da Fase 3;
- di conseguenza la frequency correction restava teoricamente corretta, ma praticamente senza spazio di esecuzione.

## Goal

Dare priorita' scientifica alla distribuzione della frequenza nel `3x beginner`, prima di riempire gli slot residui con la compensazione volume generica.

## Scope

- `api/services/training_science/plan_builder.py`
- solo ordine delle fasi nel planner beginner/full-body
- nessun cambio API
- nessun cambio UI

## Implementation

### 1. Frequency correction anticipata

Nel `build_plan()`:

- la correzione `_apply_beginner_full_body_frequency_corrections()` viene eseguita prima del calcolo degli `iso_deficits`;
- questo permette di riservare gli slot accessori ai distretti che altrimenti restano a `1x` pur con volume settimanale plausibile.

### 2. Safety net mantenuta

La stessa correzione resta anche dopo:

- compensazione volume generica;
- correzione `Quad : Ham`;
- iterazione del feedback loop.

Quindi il planner lavora ora in due tempi:

1. assicura la seconda esposizione settimanale dei piccoli distretti;
2. usa poi gli slot rimanenti per colmare i deficit di volume.

## Verification

```powershell
venv\Scripts\ruff.exe check api/services/training_science/plan_builder.py
```

## Residual Risks

- `Quad : Ham` resta il warning biomeccanico piu' probabile nel `3x beginner`.
- L'overlap `Full Body B -> Full Body C` su dorsali/femorali/glutei/trapezio resta un tema separato di recovery distribution.
- Se dopo questo step restano warning su bicipiti/polpacci, il prossimo tuning corretto non e' nello UI ma nella struttura `A/B/C` o nel cap slot/accessori del beginner.
