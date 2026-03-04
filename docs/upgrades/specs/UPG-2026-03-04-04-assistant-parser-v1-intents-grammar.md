# UPG-2026-03-04-04 - Assistant Intent/Grammar Spec (V1)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: Parser NLP Deterministico
- Priority: high
- Target release: test_react

## Goal

Definire tassonomia intent, regole linguistiche e strategia di risoluzione entita' per parser italiano orientato ai flussi CRM reali.

## Intent Taxonomy V1

- `agenda.create_event`
- `agenda.update_event_status`
- `client.create`
- `client.update`
- `contract.create`
- `movement.create_manual`
- `anamnesi.patch`
- `measurement.create`
- `workout_log.create`

## Normalization Rules

- Lowercase + trim.
- Accenti normalizzati (`perche'`, `po'`).
- Separazione simboli (`80kg` -> `80 kg`, `4x8` preservato).
- Alias data relativa:
  - `oggi`, `domani`, `dopodomani`
  - `lunedì prossimo` -> data assoluta timezone locale.
- Alias orario:
  - `alle 18`, `18:30`, `h18`.
- Numeri:
  - virgola -> punto per decimali (`82,5` -> `82.5`).

## Lexicon Core (esempi)

### Agenda

- trigger: `appuntamento`, `sessione`, `agenda`, `prenota`, `sposta`, `completa`, `rinvia`, `cancella`.
- categorie mappate:
  - `pt`, `personal` -> `PT`
  - `sala`, `allenamento libero` -> `SALA`
  - `corso` -> `CORSO`
  - `colloquio`, `consulenza` -> `COLLOQUIO`

### Cassa

- trigger: `incasso`, `entrata`, `uscita`, `spesa`, `pagamento`, `contanti`, `pos`, `bonifico`.
- tipo:
  - `incasso` -> `ENTRATA`
  - `spesa` -> `USCITA`

### Misurazioni

- trigger: `peso`, `bf`, `massa grassa`, `circonferenza`, `pressione`, `misurazione`.
- pattern tipici:
  - `peso 82`
  - `vita 88 cm`
  - `massa grassa 15%`

### Workout Log

- trigger: `allenamento fatto`, `sessione fatta`, `completata scheda`, `log workout`.
- pattern:
  - `Marco ha fatto sessione A oggi`
  - `logga allenamento scheda forza sessione 2`

## Grammar Patterns (estratti)

- Cliente + evento:
  - `<cliente> <data_relativa|data_assoluta> <ora> <categoria?>`
- Cliente + misura:
  - `<cliente> peso <numero>[kg]`
  - `<cliente> <metrica> <numero><unita?>`
- Movimento cassa:
  - `<tipo_trigger> <numero> <categoria?> <metodo?> <data?>`
- Contratto:
  - `<cliente> contratto <pacchetto> <crediti> crediti <prezzo> euro <inizio> <scadenza>`

## Entity Resolution Strategy

### Client Resolution

Ordine:

1. match esatto `nome cognome`.
2. match esatto `cognome nome`.
3. fuzzy (token sort ratio) su clienti attivi.
4. fallback su `active_client_id` dal context.

Soglie:

- `>= 0.92` auto-resolve.
- `0.80-0.91` ambiguity se piu' candidati.
- `< 0.80` unresolved.

### Exercise/Metric Resolution

- exercise: catalogo esercizi con priorita' exact, poi fuzzy.
- metric: catalogo metriche (`/metrics`) con sinonimi hardcoded V1.

## Confidence Scoring

Formula base:

`confidence = w_intent + w_entities + w_slots + w_validation - penalties`

Pesi iniziali:

- `w_intent = 0.35`
- `w_entities = 0.30`
- `w_slots = 0.20`
- `w_validation = 0.15`

Penalita':

- ambiguita' cliente: `-0.20`
- campo chiave mancante: `-0.30`
- conflitto semantico: `-0.25`

Classificazione finale:

- `>= 0.85` -> `ready`
- `0.65-0.84` -> `needs_confirmation`
- `< 0.65` -> `blocked`

## Ambiguity Protocol

Se ambiguita':

- response include `ambiguities[]` con candidati ordinati.
- commit rifiutato finche' frontend non invia risoluzione esplicita.

Tipi:

- `client_ambiguous`
- `metric_ambiguous`
- `time_ambiguous`
- `domain_ambiguous`

## Corpus and "Training" Plan (Rule-based)

Non training neurale. Training del parser:

- dataset `gold` in YAML/JSON:
  - input frase
  - intent atteso
  - slots attesi
  - status atteso
- copertura iniziale minima: 300 frasi.
- distribuzione:
  - agenda 25%
  - clienti/contratti 20%
  - cassa 20%
  - misurazioni/anamnesi 25%
  - workout log 10%

## Quality Targets

- intent accuracy >= 95%
- slot F1 >= 92%
- ambiguity false-positive <= 8%
- ambiguity false-negative <= 3%

## Versioning Strategy

- `assistant_parser_version` nel parse response (es. `v1.0.0`).
- breaking rules solo con changelog e migrazione test corpus.
