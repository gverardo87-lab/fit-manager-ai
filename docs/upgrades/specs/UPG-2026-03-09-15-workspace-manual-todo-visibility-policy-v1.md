# UPG-2026-03-09-15 - Workspace manual todo visibility policy v1

## Context

Nel workspace `Oggi`, i `todo_manual` non sono casi strutturali del CRM ma promemoria personali del trainer. Il modello reale oggi e minimale:

- `titolo`
- `descrizione`
- `data_scadenza` opzionale
- `created_at`
- `completato`

Non esistono ancora link nativi a:

- `client_id`
- `contract_id`
- `plan_id`
- `event_id`

Questa limitazione cambia completamente la logica ammissibile: un promemoria manuale non puo essere trattato come un caso business-first se il sistema non sa a cosa si riferisce.

## Problema Runtime Attuale

Nel runtime corrente:

- un `todo` senza scadenza entra in `today`;
- ogni `todo` aperto viene reso come caso individuale;
- la priorita dei promemoria e ancora troppo vicina a quella dei casi strutturali;
- l'accumulo di promemoria puo sporcare `Oggi` anche quando la giornata e gia piena di lavoro reale.

Questo comportamento viola il principio guida del workspace:

`Oggi` deve scegliere il prossimo lavoro giusto, non esporre ogni promemoria disponibile.

## Obiettivo

Definire una policy matematica, deterministica e implementabile per i `todo_manual`, tale che:

1. i promemoria restino utili;
2. non rubino viewport a sessioni, finanza critica o blocchi reali;
3. l'algoritmo usi solo campi realmente presenti nel modello;
4. il risultato sia spiegabile e auditabile.

## Invarianti

### Invariante 1

Un `todo_manual` non entra mai nel bucket `now`.

Motivo:
- non ha orario;
- non ha contesto entity-safe;
- non puo competere con casi che bloccano una seduta o fanno perdere denaro oggi.

### Invariante 2

Un `todo_manual` senza `data_scadenza` non entra mai in `today`.

Motivo:
- senza scadenza, il sistema non ha prova matematica che il promemoria sia un lavoro della giornata;
- un todo senza data e memoria di supporto, non urgenza operativa.

### Invariante 3

Un `todo_manual` non puo superare in viewport un caso strutturale nei bucket `now/today`.

Per `casi strutturali` si intendono almeno:

- `session_imminent`
- `payment_overdue`
- `onboarding_readiness`
- `contract_renewal_due`

### Invariante 4

Il workspace puo calcolare tutti i promemoria, ma non deve renderli tutti individualmente sopra la fold.

## Variabili Derivate

Per ogni `todo_manual` aperto:

- `due_delta_days`
  - se `data_scadenza` esiste: `data_scadenza - reference_date`
  - altrimenti `null`

- `age_days`
  - `reference_date - created_at_local_date`

- `is_dated`
  - `data_scadenza is not null`

- `is_overdue`
  - `due_delta_days < 0`

- `is_due_today`
  - `due_delta_days == 0`

- `is_due_soon`
  - `1 <= due_delta_days <= 3`

- `is_due_week`
  - `4 <= due_delta_days <= 7`

- `is_undated`
  - `due_delta_days is null`

## Bucket Policy

| Todo state | Regola bucket |
|---|---|
| `is_overdue` | `today` |
| `is_due_today` | `today` |
| `is_due_soon` | `upcoming_3d` |
| `is_due_week` | `upcoming_7d` |
| `is_undated` | `waiting` |
| `due_delta_days > 7` | `waiting` |

Conseguenza importante:

`todo` senza scadenza -> `waiting`, non `today`.

## Severity Policy

| Condizione | Severity |
|---|---|
| `due_delta_days <= -7` | `high` |
| `-6 <= due_delta_days <= -1` | `medium` |
| `due_delta_days == 0` | `medium` |
| `1 <= due_delta_days <= 3` | `low` |
| `4 <= due_delta_days <= 7` | `low` |
| `is_undated` | `low` |

Un `todo_manual` non diventa `critical` in v1.

Motivo:
- manca il contesto business;
- il sistema non puo dimostrare che il ritardo abbia impatto equivalente a finanza o agenda.

## Score Deterministico

Per ordinare i `todo_manual` tra loro:

```text
todo_score = urgency_score + age_bonus
```

Con:

```text
urgency_score =
  60  if due_delta_days <= -7
  45  if -6 <= due_delta_days <= -1
  35  if due_delta_days == 0
  20  if 1 <= due_delta_days <= 3
  10  if 4 <= due_delta_days <= 7
   0  if due_delta_days is null or > 7
```

```text
age_bonus =
  0   if age_days < 7
  5   if 7 <= age_days < 14
 10   if 14 <= age_days < 21
 15   if age_days >= 21
```

Tie-break:

1. `data_scadenza` ascendente
2. `created_at` ascendente
3. `todo_id` ascendente

## Structural Pressure

Per decidere quanti `todo_manual` possono occupare la viewport di `Oggi`, il motore deve calcolare:

```text
structural_now_count =
  numero di casi non-todo nel bucket now

structural_today_count =
  numero di casi non-todo nel bucket today
```

## Viewport Cap dei Todo Manuali

Il cap visibile in `Oggi` deve essere dinamico:

```text
manual_today_cap =
  0  se structural_now_count >= 1
  1  se structural_now_count == 0 e structural_today_count >= 2
  2  se structural_now_count == 0 e structural_today_count <= 1
```

Interpretazione:

- se hai urgenza vera in `now`, i promemoria non meritano viewport;
- se la giornata ha gia due o piu casi strutturali, puo vivere al massimo un promemoria manuale;
- solo in giornata quasi libera i promemoria possono occupare due slot.

## Policy di Rendering

### Caso A: `eligible_manual_today_count == 0`

- nessun `todo_manual` visibile in `today`

### Caso B: `eligible_manual_today_count <= manual_today_cap`

- i promemoria restano individuali

### Caso C: `eligible_manual_today_count > manual_today_cap`

- solo i primi `manual_today_cap` entrano nello stack visibile
- i rimanenti:
  - restano inclusi nel `total` di sezione
  - restano disponibili in `/api/workspace/cases`
  - non generano righe individuali sopra la fold

Nota v1:

non e obbligatorio introdurre subito un case aggregato sintetico. La policy minima puo usare:

- `items` visibili troncati
- `total` reale di sezione
- copy UI che segnala che esiste backlog ulteriore

## Policy per i Todo Senza Scadenza

I `todo` senza scadenza sono ammessi nel workspace, ma solo come backlog laterale:

- bucket = `waiting`
- severity = `low`
- mai in `today`
- mai sopra la fold

Se in futuro si vorra promuoverli, servira almeno uno dei seguenti arricchimenti di schema:

- `priority`
- `entity_ref`
- `linked_client_id / contract_id / plan_id / event_id`
- `tag` strutturati

Senza questi campi, la promozione sarebbe arbitraria.

## Regole che il Runtime Non Deve Implementare

Non implementare in v1:

- NLP sul titolo per inferire cliente o contratto
- scoring semantico da testo libero
- euristiche opache tipo "sembra importante"
- promozione di todo senza scadenza in base al testo

Queste scelte rompono la spiegabilita del workspace.

## Effetto Atteso su `Oggi`

Con questa policy:

- i promemoria restano utili ma subordinati;
- i todo senza data smettono di sporcare `today`;
- la giornata non viene invasa da liste di memo personali;
- il trainer continua a trovare tutto in `/cases`, ma la home operativa resta credibile.

## Decisione Raccomandata

La policy raccomandata per il prossimo runtime pass e:

1. `todo` senza scadenza -> `waiting`
2. `todo` non entra mai in `now`
3. `todo` max visibile in `today` = cap dinamico da `structural_now_count` e `structural_today_count`
4. extras restano in `total` + `/cases`, non come righe individuali

## Next Smallest Step

Tradurre questa policy nel runtime di `workspace_engine.py` senza introdurre nuovi `case_kind`:

- cambiare bucket logic dei todo
- introdurre `todo_score`
- applicare `manual_today_cap`
- mantenere `WorkspaceCaseListResponse` completo
