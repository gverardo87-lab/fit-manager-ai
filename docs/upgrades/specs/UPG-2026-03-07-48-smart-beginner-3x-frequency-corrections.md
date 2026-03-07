# UPG-2026-03-07-48 - SMART Beginner 3x Frequency Corrections

## Context

Dopo i microstep su `split_logic.py`, `plan_builder.py` e ranker runtime, il profilo `full_body 3x` risultava molto piu' equilibrato sui ratio principali.

Nel caso `3x beginner`, pero', restava un drift specifico:

- `deltoide_laterale`
- `bicipiti`
- `tricipiti`
- `polpacci`

venivano spesso segnalati a `1x/settimana` dall'analyzer, nonostante il piano li coinvolgesse indirettamente tramite compound.

Il motivo e' nel criterio scientifico gia' in uso nel backend:

- una sessione conta come "stimolo" solo se il muscolo raggiunge almeno `2.0` serie ipertrofiche in quella seduta;
- nei full body beginner, molti distretti accessori arrivano a `1.0-1.5` serie per seduta dai compound;
- il volume settimanale puo' quindi essere plausibile, ma la frequenza per-seduta resta sub-ottimale.

## Goal

Correggere il `3x beginner` nel layer giusto, cioe' il planner, distribuendo micro-dose dirette minime per portare i distretti accessori a `freq >= 2x` senza gonfiare artificialmente il volume totale.

## Scope

- `api/services/training_science/plan_builder.py`
- solo microciclo `full_body 3x` principiante
- solo piccoli distretti accessori
- nessun cambio API
- nessun cambio UI

## Non-Goals

- nessuna modifica all'analyzer di frequenza
- nessun cambio ai target MEV/MAV/MRV
- nessun nuovo solver globale multi-obiettivo
- nessun tuning del ranker runtime

## Implementation

### 1. Riconoscimento del caso clinico corretto

Introdotto un gate esplicito:

- livello `principiante`
- almeno 3 sessioni
- tutte `full_body`

La correzione non viene applicata a split `upper/lower`, `PPL` o profili intermedi/avanzati.

### 2. Frequency-aware micro-corrections

Per i muscoli:

- `deltoide_laterale`
- `bicipiti`
- `tricipiti`
- `polpacci`

il planner:

- calcola il volume ipertrofico per singola sessione;
- verifica quante sedute superano gia' la soglia `2.0`;
- se il totale e' `< 2`, seleziona le sessioni piu' vicine alla soglia;
- aggiunge solo la dose diretta minima necessaria tramite pattern di isolamento coerente.

Questo privilegia la distribuzione della frequenza, non l'accumulo cieco di serie.

### 3. Correzione session-aware

Le sessioni candidate vengono ordinate per:

1. gap piu' piccolo dalla soglia di stimolo;
2. minor numero di isolamenti gia' presenti;
3. minor densita' slot;
4. ordine stabile di sessione.

Così il planner preferisce colmare la seconda esposizione dove basta una micro-dose da `1-2` serie invece di aggiungere slot piu' pesanti altrove.

## Verification

```powershell
venv\Scripts\ruff.exe check api/services/training_science/plan_builder.py
```

## Residual Risks

- Il warning residuo piu' probabile resta `Quad : Ham`, che non dipende dalla frequenza accessori ma dalla distribuzione lower/posterior chain.
- Il recupero `Full Body B -> Full Body C` puo' restare alto su femorali/glutei/dorsali: questo richiede un microstep separato sul planner lower, non altre micro-correzioni su braccia/spalle.
- Il commento di Fase 1 in `build_plan()` resta storicamente rumoroso su A/B vs A/B/C e merita pulizia dedicata quando si rifinisce il file.
