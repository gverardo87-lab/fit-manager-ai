# UPG-2026-03-09-11 - Workspace Ranking and Dominance Matrix v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-11`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace UX + Decision Engine + Runtime Planning`
- Priority: `high`
- Target release: `codex_02`

## Problem

`Oggi` ha gia un motore read-only funzionante e una shell frontend concreta, ma il punto critico non e piu l'assenza di dati.

Il problema reale e la selezione:

- il motore puo calcolare piu segnali di quelli che la pagina puo mostrare bene;
- la UI soffre ancora di densita verticale eccessiva anche con pochi `case_kind`;
- il ranking attuale e ancora troppo vicino alla sorgente dati, non abbastanza vicino alla decisione operativa;
- manca un layer esplicito di dominanza, soppressione e budget visivo.

Se si continua ad aggiungere segnali o famiglie senza questo layer, `Oggi` rischia di diventare un contenitore corretto ma non desiderabile.

## Desired Outcome

Definire una matrice implementabile che trasformi `Oggi` in una surface decisionale disciplinata:

- molti segnali possono essere calcolati in background;
- pochi casi possono sopravvivere alla visibilita iniziale;
- i casi forti devono dominare i casi deboli sullo stesso contesto;
- il ranking finale deve restare deterministico, spiegabile e auditabile;
- la viewport iniziale deve avere un budget duro, non solo un ordinamento.

## Scope

- In scope:
  - pipeline logica `signal -> case -> suppression -> promotion -> ranking -> viewport`;
  - matrice v1 di dominanza e visibilita;
  - verdetto prodotto sui 6 `case_kind` runtime gia attivi;
  - schema di scoring deterministico;
  - budget di densita per `Oggi`.
- Out of scope:
  - codice runtime;
  - refactor UI;
  - nuovi endpoint;
  - mutazioni workspace (`snooze`, `seen`, `managed externally`);
  - introduzione immediata di nuovi `case_kind`.

## Impact Map

- Files/modules touched:
  - `docs/upgrades/specs/UPG-2026-03-09-11-workspace-ranking-and-dominance-matrix-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `docs`
- Invarianti da preservare:
  - `Oggi` resta una surface decisionale, non analitica;
  - nessuna finanza completa fuori da `renewals_cash`;
  - nessun warning standalone senza una famiglia e una regola di merge;
  - nessun ranking opaco o non spiegabile.

## Decision Summary

La strategia v1 raccomandata e:

1. calcolare tutti i segnali utili nel motore;
2. sintetizzarli in pochi casi operativi;
3. applicare regole hard di dominanza e soppressione;
4. ordinare solo i casi sopravvissuti;
5. applicare un budget di viewport che limita cio che compare sopra la fold.

In altre parole:

> Il ranking non decide da solo cosa mostrare.  
> Prima si elimina il rumore. Poi si ordina il valore residuo.

## Runtime Pipeline v1

### 1. Normalize

Tutte le sorgenti grezze vengono convertite in `signals` standardizzati.

Campi minimi raccomandati:

- `signal_code`
- `domain`
- `root_entity_type`
- `root_entity_id`
- `family`
- `base_tier`
- `due_date`
- `days_to_due`
- `severity`
- `reason`
- `primary_cta`

### 2. Synthesize

I segnali non vengono resi direttamente.
Vengono aggregati in `candidate cases` per:

- `family`
- `merge_root`
- `root_entity`

Obiettivo:

- un cliente non deve generare tre righe separate per `anamnesi missing`, `baseline missing`, `workout missing`;
- un contratto non deve generare una riga per ogni rata scaduta;
- un piano non deve generare una riga per ogni sintomo di manutenzione.

### 3. Suppress

Prima del ranking si applicano regole hard:

- dominanza;
- soppressione duplicati;
- soppressione segnali deboli gia coperti;
- promozioni limitate per vicinanza operativa.

### 4. Promote

Solo i casi che cambiano davvero il lavoro della giornata possono salire in `Adesso` o `Oggi`.

### 5. Rank

I casi sopravvissuti vengono ordinati da uno score deterministico.

### 6. Budget

Anche dopo il ranking, la UI non deve rendere tutto:

- un caso puo essere valido ma non meritare la viewport iniziale;
- il budget e parte del motore decisionale, non solo della UI.

## Families v1

Le famiglie operative ufficiali restano:

- `Sessione da Preparare`
- `Cliente da Preparare`
- `Cliente da Rivalutare`
- `Programma da Rivedere`
- `Finanza`
- `Todo e Opportunita`

Per il runtime attuale di `Oggi`, la priorita operativa deve concentrarsi sulle prime 4 famiglie effettivamente utili in giornata:

- `Sessione da Preparare`
- `Cliente da Preparare`
- `Finanza`
- `Todo e Opportunita` solo quando non compete con le tre sopra

`Cliente da Rivalutare` e `Programma da Rivedere` restano famiglie valide, ma non devono ancora entrare come prime protagoniste finche non esiste una disciplina forte di visibilita.

## Current Runtime Verdict

Questa matrice fissa il verdetto sui 6 `case_kind` gia presenti nel motore.

| Case kind | Family | Verdict | Default visibility | Notes |
|---|---|---|---|---|
| `session_imminent` | `Sessione da Preparare` | `KEEP` | `promoted` | Caso dominante per tempo reale |
| `payment_overdue` | `Finanza` | `KEEP` | `promoted` | Mai degradare a badge |
| `onboarding_readiness` | `Cliente da Preparare` | `KEEP_COMPRESSED` | `case` | Va compresso e mergeato meglio, non espanso |
| `contract_renewal_due` | `Finanza` | `KEEP_CONTROLLED` | `case` | Sale solo se vicino o concretamente rilevante |
| `client_reactivation` | `Todo e Opportunita` | `DEGRADE` | `later` | Non deve rubare viewport a casi strutturali |
| `todo_manual` | `Todo e Opportunita` | `DEGRADE` | `later` | Utile, ma subordinato ai casi sistemici |

## Signal Matrix v1

Questa tabella formalizza i segnali principali, inclusi quelli non ancora visibili come `case` nel runtime.

| Signal | Family | Root | Base tier | Promote if | Suppress if | Merge target |
|---|---|---|---|---|---|---|
| `event_now` | `Sessione da Preparare` | `event` | `promoted` | sempre | mai | `session_imminent` |
| `event_next_2h` | `Sessione da Preparare` | `event` | `promoted` | sempre | mai | `session_imminent` |
| `anamnesi_missing` | `Cliente da Preparare` | `client` | `case` | cliente attivo o appuntamento entro `14d` | esiste sessione dominante entro `24h` | `onboarding_readiness` |
| `anamnesi_legacy` | `Cliente da Preparare` | `client` | `case` | onboarding attivo o appuntamento vicino | esiste sessione dominante | `onboarding_readiness` |
| `baseline_missing` | `Cliente da Preparare` | `client` | `case` | programma da avviare o sessione entro `7d` | esiste sessione dominante | `onboarding_readiness` |
| `workout_missing` | `Cliente da Preparare` | `client` | `case` | onboarding bloccato o avvio imminente | onboarding gia dominato da CTA piu forte | `onboarding_readiness` |
| `portal_questionnaire_pending` | `Cliente da Preparare` | `client` | `badge` | invio fermo `>48h` o appuntamento vicino | anamnesi gia ricevuta | `onboarding_readiness` |
| `measurement_gap_soft` | `Cliente da Rivalutare` | `client` | `badge` | mai da solo | esiste gia case clinico stesso cliente | `client_revaluation` |
| `measurement_gap_critical` | `Cliente da Rivalutare` | `client` | `case` | goal attivo, programma attivo o sessione entro `7d` | esiste sessione dominante | `client_revaluation` |
| `anamnesi_review_due` | `Cliente da Rivalutare` | `client` | `badge` | appuntamento entro `14d` o molto oltre soglia | cliente inattivo | `client_revaluation` |
| `workout_age_soft` | `Programma da Rivedere` | `plan` | `badge` | mai da solo | piano non attivo | `program_review` |
| `workout_age_critical` | `Programma da Rivedere` | `plan` | `case` | compliance bassa, fine ciclo vicina, sessione entro `7d` | piano non attivo o chiuso | `program_review` |
| `plan_review_due` | `Programma da Rivedere` | `plan` | `case` | review oggi o scaduta | esiste fine ciclo dominante | `program_review` |
| `plan_compliance_risk` | `Programma da Rivedere` | `plan` | `case` | sotto soglia o no logs recenti | piano non ancora partito | `program_review` |
| `payment_overdue` | `Finanza` | `contract` | `promoted` | sempre | mai | `payment_overdue` |
| `renewal_due` | `Finanza` | `contract` | `case` | `<= 7d`, crediti bassi o valore residuo alto | pagamento scaduto dominante sullo stesso contratto | `contract_renewal_due` |
| `client_inactive` | `Todo e Opportunita` | `client` | `later` | quiet day o inattivita alta | esiste gia caso piu forte sul cliente | `client_reactivation` |
| `todo_manual` | `Todo e Opportunita` | `todo` | `later` | `today` o overdue | esiste caso piu forte sullo stesso contesto | `todo_manual` |

## Dominance Rules v1

Queste regole battono sempre il ranking.

### DR-01 Session dominates client blockers

Se esiste un `session_imminent` per un cliente entro `24h`, i blocker clinici dello stesso cliente non devono vivere come casi paralleli nello stack iniziale.

Devono essere:

- assorbiti come segnali del caso sessione;
- oppure relegati a `detail-only`.

### DR-02 Overdue payment dominates contract follow-up

Se esiste `payment_overdue`, lo stesso contratto non deve mostrare in parallelo `contract_renewal_due` sopra la fold.

Il rinnovo puo:

- restare nel dettaglio;
- o comparire piu sotto solo se non c e conflitto percettivo.

### DR-03 One onboarding case per client

Per ogni cliente esiste al massimo un case `onboarding_readiness`.

Tutti i segnali `anamnesi`, `baseline`, `workout_missing`, `portal_questionnaire_pending` devono essere interni allo stesso case.

### DR-04 Program review absorbs plan maintenance

Per ogni piano esiste al massimo un case `program_review`.

`workout_age`, `plan_review_due`, `plan_compliance_risk`, `plan_cycle_closing` devono convergere nello stesso contenitore logico.

### DR-05 Structural work dominates manual todo

Un `todo_manual` non puo superare nello stack un caso strutturale sullo stesso cliente/contratto/piano se quest ultimo e ancora aperto e azionabile.

### DR-06 Later opportunities never steal urgent slots

`client_reactivation` e `todo_manual` non possono occupare slot `Adesso` se esistono gia:

- sessioni imminenti;
- onboarding bloccati rilevanti;
- finanza critica.

## Suppression Rules v1

- `SR-01`: massimo un case per stessa `root_entity` sopra la fold.
- `SR-02`: i segnali `soft` non generano case se gia coperti da un caso piu forte della stessa famiglia.
- `SR-03`: un case con `base_tier=badge` non puo promuoversi da solo senza trigger esplicito.
- `SR-04`: i casi `later` vengono completamente nascosti dalla viewport iniziale se il budget e gia saturo di `promoted` o `case`.
- `SR-05`: i case senza CTA concreta non entrano nella viewport iniziale.

## Ranking Model v1

Dopo dominanza e soppressione, i casi rimasti vengono ordinati con uno score deterministico.

### Formula

```text
score =
  urgency_score
+ blocker_score
+ revenue_risk_score
+ session_proximity_score
+ staleness_score
+ lifecycle_value_score
- redundancy_penalty
- snooze_penalty
```

### Weight Bands

| Component | Range | Meaning |
|---|---:|---|
| `urgency_score` | `0..40` | tempo e scadenza |
| `blocker_score` | `0..30` | blocco operativo reale |
| `revenue_risk_score` | `0..35` | perdita soldi o rischio economico |
| `session_proximity_score` | `0..25` | sessione o avvio imminente |
| `staleness_score` | `0..20` | freshness degradata con impatto reale |
| `lifecycle_value_score` | `0..10` | valore commerciale o retention |
| `redundancy_penalty` | `0..40` | similarita a casi gia visibili |
| `snooze_penalty` | `0..20` | memoria locale futura |

### Tie-breakers

In caso di score uguale:

1. `case_kind` priority hard-coded
2. `severity`
3. `due_date`
4. `root_entity.label`

## Viewport Budget v1

Il budget e una regola del motore, non solo della UI.

### Initial Surface Budget

- massimo `2` casi in `Adesso`
- massimo `4` casi in `Oggi`
- massimo `1` caso per stessa `root_entity` sopra la fold
- massimo `1` caso opportunistico (`todo` o `reactivation`) sopra la fold

### Card Density Budget

La lista iniziale deve mostrare solo:

- titolo
- una `reason line`
- un badge urgenza
- una CTA primaria
- eventuale contatore `+N segnali`

Tutto il resto va nel detail panel.

### Detail Budget

Il pannello dettaglio puo espandere:

- segnali interni;
- contesto collegato;
- timeline sintetica;
- azioni secondarie.

Ma non deve duplicare integralmente cio che la card ha gia espresso.

## Recommended Runtime Phasing

### Phase 1

Applicare dominanza, soppressione e viewport budget ai 6 `case_kind` gia runtime.

Nessun nuovo segnale visibile.

### Phase 2

Integrare `measurement_freshness` e `workout_freshness` nel workspace engine come:

- `badge` interni;
- segnali di scoring;
- non ancora come nuove righe autonome in `Oggi`.

### Phase 3

Solo dopo la stabilizzazione della superficie:

- promuovere alcuni segnali freshness a `case`;
- introdurre `Programma da Rivedere` e `Cliente da Rivalutare` come famiglie runtime vere.

## Acceptance Criteria

- il motore puo continuare a calcolare molti segnali, ma la viewport iniziale resta sotto controllo;
- `session_imminent` e `payment_overdue` dominano davvero i casi piu deboli;
- `todo_manual` e `client_reactivation` smettono di competere con i casi strutturali;
- `onboarding_readiness` resta un solo case per cliente;
- la matrice permette di integrare freshness senza introdurre nuovi warning orfani;
- la strategia e implementabile senza LLM, senza ML e senza logiche opache.

## Verification Plan

Questo microstep e docs-only.

Verifiche richieste:

- review manuale coerenza con:
  - `UPG-2026-03-09-08`
  - `UPG-2026-03-09-09`
  - `UPG-2026-03-09-10`
- `rg` cross-doc su:
  - `UPG-2026-03-09-11`
  - `dominance matrix`
  - `viewport budget`

## Risks and Mitigation

- Rischio 1: il team implementa solo lo score e ignora dominanza/soppressione.
  - Mitigazione 1: questa spec dichiara esplicitamente che il ranking arriva solo dopo le regole hard.
- Rischio 2: la UI continua a mostrare troppe informazioni anche con un motore migliore.
  - Mitigazione 2: il budget viewport e il budget card fanno parte del contratto, non della rifinitura grafica.
- Rischio 3: si reintroducono nuovi `case_kind` prima di disciplinare i 6 esistenti.
  - Mitigazione 3: `Phase 1` vieta espansione runtime prima della stabilizzazione dei casi correnti.

## Notes

- Questa spec non chiede piu potenza di calcolo. Chiede piu disciplina nella selezione.
- Il prossimo passo corretto non e un nuovo `case_kind`.
- Il prossimo passo corretto e applicare questa matrice ai 6 casi esistenti, riducendo davvero il rumore di `Oggi`.
