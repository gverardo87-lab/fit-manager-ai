# UPG-2026-03-09-09 - Workspace Signal Visibility Policy v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-09`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace UX + Decision Engine + Information Architecture`
- Priority: `high`
- Target release: `codex_02`

## Problem

`Oggi` sta migliorando come shell operativa, ma resta esposta a un rischio chiaro di overload:

- troppe righe alte nello stack producono una scrollata verticale eccessiva;
- misurazioni, anamnesi e schede da rifare hanno gia logiche sparse nel prodotto e rischiano di entrare come warning duplicati;
- le soglie di freshness non sono ancora allineate tra backend e frontend;
- il trainer rischia di vedere record tecnici invece di casi operativi.

In particolare oggi esiste gia un drift reale tra:

- readiness backend:
  - `measurement_review` a `+30 giorni`
  - `workout_review` a `+21 giorni`
  - `anamnesi_review` a `+180 giorni`
- alert frontend:
  - `scheda_age` warning/critical a `21/35 giorni`
  - `measurement_gap` warning/critical a `25/35 giorni`

Senza una policy unica, `Oggi` non puo diventare affidabile come collega operativo.

## Desired Outcome

Introdurre una policy unica e dichiarativa che stabilisca, per ogni segnale workspace:

- se deve restare nascosto;
- se deve comparire solo come badge interno;
- se deve diventare un caso autonomo;
- quando puo essere promosso in `Oggi`;
- in quale famiglia deve essere mergeato;
- quando deve essere soppresso per evitare duplicati.

La regola prodotto di base e:

> Un segnale entra in `Oggi` solo se cambia davvero l'azione di oggi.

## Scope

- In scope:
  - policy di visibilita per segnali `anamnesi`, `misurazioni`, `scheda/programmi`;
  - unificazione semantica di famiglie, merge root e promotion rules;
  - budget di densita UI per lista e pannello dettaglio;
  - riallineamento concettuale con i segnali gia esistenti (`sessioni`, `finanza`, `todo`, `renewal`).
- Out of scope:
  - nuova UI o refactor codice in questo step;
  - nuove mutation (`snooze`, `seen`, `managed externally`);
  - nuovi endpoint API;
  - spostamento della dashboard `/`;
  - dettaglio clinico sensibile o visualizzazione di valori raw in `Oggi`.

## Impact Map

- Files/modules touched:
  - `docs/upgrades/specs/UPG-2026-03-09-09-workspace-signal-visibility-policy-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `docs`
- Invarianti da preservare:
  - `Oggi` resta una surface decisionale, non analitica;
  - dati anamnestici sensibili non compaiono in lista;
  - dati economici completi restano confinati in `Rinnovi & Incassi`;
  - nessun nuovo warning standalone viene introdotto senza una famiglia di merge.

## Policy Model

Ogni segnale workspace deve essere descritto da 5 attributi minimi:

1. `display_tier`
   - `hidden`
   - `badge`
   - `case`
   - `promoted`
2. `merge_root`
   - `client`
   - `plan`
   - `contract`
   - `event`
3. `family`
   - famiglia operativa di destinazione
4. `promote_if`
   - condizione che lo rende visibile in `Oggi`
5. `suppress_if`
   - condizione che evita il doppione o il rumore

## Top-level Families

`Oggi` non deve crescere per tipi di dato. Deve crescere per famiglie operative.

### 1. Sessione da Preparare

- root: `event`
- purpose: proteggere sessioni o appuntamenti imminenti
- contiene:
  - sessione imminente
  - readiness blocker del cliente collegato
  - eventuale contratto/credito da verificare
- note:
  - se esiste una sessione vicina, i blocker readiness non devono vivere come case parallelo nello stack
  - devono essere assorbiti nel caso sessione

### 2. Cliente da Preparare

- root: `client`
- purpose: onboarding e readiness iniziale
- contiene:
  - anamnesi mancante
  - anamnesi legacy
  - baseline misure mancante
  - scheda mancante
  - portale anamnesi inviato ma incompleto
- note:
  - e la famiglia canonica per i dati che bloccano l'avvio cliente

### 3. Cliente da Rivalutare

- root: `client`
- purpose: freshness clinico-operativa nel tempo
- contiene:
  - misurazioni stale
  - anamnesi review due
  - review generale cliente
- note:
  - non serve a bloccare l'avvio, ma a mantenere la qualita nel tempo

### 4. Programma da Rivedere

- root: `plan`
- purpose: manutenzione metodologica e ciclo scheda
- contiene:
  - scheda invecchiata
  - review programma dovuta
  - compliance a rischio
  - no recent logs
  - fine ciclo senza prossimo piano
- note:
  - i problemi di scheda attiva devono preferire questa famiglia, non generare alert orfani

### 5. Finanza

- root: `contract`
- purpose: incassi, rinnovi, scadenze economiche
- contiene:
  - rate scadute
  - rate imminenti
  - rinnovi
  - spese ricorrenti
- note:
  - non si mergea mai con famiglie cliniche o programmi

### 6. Todo e Opportunita

- root: `todo` o `client`
- purpose: lavoro non bloccante ma utile
- contiene:
  - todo manuali
  - follow-up
  - riattivazioni

## Visibility Tiers

### `hidden`

Il segnale non compare nello stack e non genera da solo un caso.

Usi tipici:

- reminder troppo deboli;
- segnali gia coperti da un caso piu forte;
- dati che non cambiano l'azione di oggi.

### `badge`

Il segnale non genera un case autonomo, ma vive come dettaglio interno di un caso esistente.

Usi tipici:

- scheda vecchia ma non ancora critica;
- anamnesi review lontana;
- measurement gap presente ma senza impatto immediato.

### `case`

Il segnale puo generare un case autonomo, di norma in area manutenzione o `Puo aspettare`.

Usi tipici:

- cliente da rivalutare;
- programma da rivedere;
- rinnovo non ancora critico ma concreto.

### `promoted`

Il segnale puo essere promosso in `Adesso` o `Oggi` perche ha impatto operativo diretto.

Usi tipici:

- sessione entro poche ore con blocker;
- incasso scaduto;
- onboarding bloccato con primo appuntamento vicino;
- review cliente o piano che impatta una sessione imminente.

## Signal Catalog v1

| Signal | Family | Merge root | Default tier | Promote if | Suppress if |
|---|---|---|---|---|---|
| `anamnesi_missing` | `Cliente da Preparare` | `client` | `case` | cliente nuovo/attivo oppure appuntamento entro 14d | esiste `Sessione da Preparare` per lo stesso cliente entro 24h |
| `anamnesi_legacy` | `Cliente da Preparare` | `client` | `case` | primo ciclo attivo o appuntamento entro 14d | esiste `Sessione da Preparare` dominante |
| `baseline_missing` | `Cliente da Preparare` | `client` | `case` | programma da iniziare o sessione entro 7d | esiste `Sessione da Preparare` dominante |
| `workout_missing` | `Cliente da Preparare` | `client` | `case` | programma deve partire oggi/domani o onboarding fermo >24h | cliente gia coperto da case onboarding con CTA piu forte |
| `portal_questionnaire_pending` | `Cliente da Preparare` | `client` | `badge` | appuntamento entro 7d o invio fermo >48h | anamnesi gia ricevuta o apertura wizard locale gia avviata |
| `measurement_gap_soft` | `Cliente da Rivalutare` | `client` | `badge` | mai direttamente | esiste `Programma da Rivedere` o `Cliente da Rivalutare` gia aperto |
| `measurement_gap_critical` | `Cliente da Rivalutare` | `client` | `case` | programma attivo, goal attivo o appuntamento entro 7d | `Sessione da Preparare` domina lo stesso cliente |
| `anamnesi_review_due` | `Cliente da Rivalutare` | `client` | `badge` | appuntamento entro 14d o review molto oltre soglia | cliente non attivo o nessuna interazione prossima |
| `workout_age_soft` | `Programma da Rivedere` | `plan` | `badge` | mai direttamente | piano non attivo o review gia pianificata |
| `workout_age_critical` | `Programma da Rivedere` | `plan` | `case` | compliance bassa, fine ciclo vicina o sessione entro 7d | piano completato senza continuita commerciale aperta |
| `plan_review_due` | `Programma da Rivedere` | `plan` | `case` | review scaduta o oggi | esiste fine ciclo dominante sullo stesso piano |
| `plan_compliance_risk` | `Programma da Rivedere` | `plan` | `case` | compliance sotto soglia o no logs recenti | piano da attivare, non ancora eseguito |
| `plan_cycle_closing` | `Programma da Rivedere` | `plan` | `case` | fine ciclo entro 7d o completato senza successore | esiste rinnovo gia in chiusura ma senza impatto sul piano no |

## Threshold Policy v1

Questa spec non modifica ancora il runtime, ma definisce la policy target.

### Anamnesi

- `missing`: case immediato per clienti attivi o in onboarding
- `legacy`: case immediato per clienti attivi o onboarding
- `review_due_days`: `180`
- `review_visible_tier`: `badge`
- `review_case`: solo se supera molto la soglia oppure se esiste una sessione/visita vicina

### Misurazioni

- `soft_warning_days`: `25`
- `case_days`: `35`
- `case_family`: `Cliente da Rivalutare`
- `promoted` solo se:
  - esiste programma attivo
  - oppure goal attivo
  - oppure appuntamento entro `7 giorni`

### Scheda / Programma

- `soft_warning_days`: `21`
- `case_days`: `35`
- `case_family`: `Programma da Rivedere`
- `promoted` solo se:
  - compliance bassa
  - review dovuta
  - fine ciclo vicina
  - sessione entro `7 giorni`

## Conflict Resolution

Per ridurre davvero il rumore servono regole di soppressione nette.

### Rule 1: Sessione batte readiness

Se esiste una sessione vicina per un cliente con blocker readiness:

- non mostrare `Cliente da Preparare` come riga separata in cima allo stack
- assorbire i blocker nel caso `Sessione da Preparare`

### Rule 2: Onboarding batte freshness

Se un cliente non e ancora pronto all'avvio:

- non mostrare anche `Cliente da Rivalutare`
- misurazioni/anamnesi review restano badge interni o hidden

### Rule 3: Piano batte singolo alert scheda

I segnali di scheda non devono mai comparire come alert autonomi scollegati.

- se c'e un piano attivo, i segnali di age/review/compliance devono confluire in `Programma da Rivedere`

### Rule 4: Finanza non si mergea

Incassi, rinnovi e spese:

- restano indipendenti dalle famiglie cliniche
- possono convivere nello stack ma non si fondono con casi cliente/piano

## UI Density Budget

Per non trasformare `Oggi` in un elenco infinito, la policy introduce un budget di visualizzazione.

### Lista stack

Ogni riga deve mostrare solo:

- titolo
- una reason line
- un badge urgenza
- CTA primaria
- opzionale `+N segnali`

Da non mostrare di default in lista:

- piu di una linea di impatto;
- timeline dettagliata;
- valori misurazione raw;
- contenuto anamnesi;
- issue exercise-level.

### Detail panel

Il pannello dettaglio puo mostrare:

- massimo `3` segnali in primo piano
- contesto collegato
- ultima data utile
- prossima azione

I segnali extra devono essere collassati in `altri segnali`.

### Bucket caps

Prima vista raccomandata:

- `Adesso`: massimo `4` righe visibili
- `Oggi`: massimo `6` righe visibili
- `Puo aspettare`: collassato di default

## Privacy and Data Exposure Rules

### Misurazioni

In `Oggi` non devono apparire:

- grafici;
- andamento raw;
- valori antropometrici dettagliati.

Sono ammessi solo:

- ultima data misurazione;
- gap in giorni;
- eventuale riferimento ad obiettivi attivi.

### Anamnesi

In `Oggi` non devono apparire:

- risposte sensibili;
- dettagli clinici specifici;
- categorie patologiche granulari.

Sono ammessi solo:

- `missing`
- `legacy`
- `review due`

### Schede

In `Oggi` non devono apparire di default:

- lista esercizi;
- warning exercise-level;
- analisi scientifica completa.

Sono ammessi solo:

- eta del piano;
- fase ciclo;
- compliance sintetica;
- CTA verso review o piano successivo.

## Acceptance Criteria

- Ogni nuovo segnale workspace ha una famiglia di merge dichiarata.
- Nessun segnale `anamnesi`, `misurazioni`, `scheda` entra come warning standalone senza policy.
- `Oggi` resta decisionale e non diventa una vista analitica.
- Il drift attuale tra soglie frontend/backend e esplicitato e tracciato in una policy target unica.
- La prossima iterazione UI puo ridurre densita e scroll senza perdere contenuto operativo.

## Risks and Mitigation

- Rischio 1: la policy introduce piu regole del necessario.
  - Mitigazione 1: partire da 3 famiglie nuove (`preparare`, `rivalutare`, `programma`) e non da 10 case kind aggiuntivi.
- Rischio 2: alcune soglie oggi non coincidono con i servizi runtime.
  - Mitigazione 2: questa spec dichiara la policy target; il prossimo microstep deve riallineare il motore e le utility pure.
- Rischio 3: il pannello dettaglio puo comunque crescere troppo.
  - Mitigazione 3: cap esplicito di `3` segnali prioritari e collasso del resto.

## Rollout Recommendation

Ordine corretto dei prossimi microstep:

1. introdurre una `workspace freshness policy` condivisa tra service/backend e utility frontend;
2. riallineare i segnali `misurazioni`, `anamnesi`, `scheda` alle nuove famiglie;
3. comprimere la row UI dello stack;
4. solo dopo aggiungere i nuovi segnali visibili a `Oggi`.

## Notes

- Questa spec non aggiunge nessun warning nuovo; impedisce che i prossimi warning entrino nel workspace nel modo sbagliato.
- Il principio da preservare resta semplice:
  - `Oggi` mostra lavoro da decidere
  - le altre pagine mostrano dati da esplorare
