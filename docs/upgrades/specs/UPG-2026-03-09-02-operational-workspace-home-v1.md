# UPG-2026-03-09-02 - Operational Workspace Home v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-02`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace UX + Information Architecture + Cross-domain Operations`
- Priority: `high`
- Target release: `codex_02`
- Status: `planned`

## Problem

FitManager ha gia superfici verticali forti per dashboard, profilo cliente, monitoraggio, onboarding e finanza, ma non ha ancora una home post-login che diventi la "mental home" quotidiana del trainer.

Lo stato attuale presenta tre limiti:

1. La home principale e una dashboard overview valida, ma non e il centro operativo unico della giornata.
2. Le informazioni cross-domain esistono in piu luoghi e costringono il trainer a cercare attivamente cosa fare.
3. Una timeline unica costruita sui record grezzi genererebbe rumore, duplicazioni e perdita di gerarchia tra eventi molto diversi tra loro.

Esempio concreto: "anamnesi mancante", "sessione oggi alle 18:00" e "affitto studio da registrare" non possono vivere come semplici righe equivalenti in un feed cronologico unico. Hanno gravita, contesto, auditability e azioni corrette diverse.

## Desired Outcome

FitManager deve introdurre una nuova home post-login chiamata `Oggi`, basata su un motore operativo unificato che:

- mostri al trainer solo i casi operativi davvero rilevanti;
- unifichi agenda, onboarding, programmi, rinnovi e incassi senza duplicazioni;
- preservi la separazione tra overview neutra e contesti finanziari sensibili;
- permetta azioni forti e rapide, ma sempre coerenti con il dominio;
- crei un'abitudine quotidiana tale per cui il trainer apra FitManager prima di qualsiasi altro strumento.

## Scope

- In scope:
  - definizione della nuova home post-login `Oggi`;
  - definizione dei 4 workspace nativi `Oggi`, `Onboarding`, `Programmi`, `Rinnovi & Incassi`;
  - modello concettuale `Signal -> Case -> Action`;
  - strategia `dual timeline`;
  - catalogo iniziale dei casi operativi;
  - regole di merge, priorita, promozione e anti-rumore;
  - linee guida per visual hierarchy e action model;
  - sync documentale di log/ADR/workboard.
- Out of scope:
  - implementazione frontend o backend;
  - nuove query/API;
  - persistence model definitivo del case engine;
  - politiche di notifiche push/email/WhatsApp;
  - automazioni AI write-capable.

## Impact Map

- Files/modules da toccare:
  - `docs/upgrades/specs/UPG-2026-03-09-02-operational-workspace-home-v1.md`
  - `docs/adr/ADR-2026-03-09-operational-workspace-case-engine.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend`, `api`, `core`, `tools`
- Invarianti da preservare:
  - dashboard overview privacy-safe senza dati finanziari come default neutro;
  - dati economici completi solo in contesti finance dedicati;
  - comportamento deterministico per priorita e merge dei casi;
  - auditability su movimenti economici e azioni business-critical;
  - no duplicazione visiva dello stesso problema su piu workspace.

## Product Decisions Locked

- La home post-login target diventa `Oggi`.
- La dashboard attuale sopravvive come overview secondaria, raccomandata con naming `Panoramica`.
- I dati finanziari completi con importi e date restano confinati a `Rinnovi & Incassi` e ai contesti finance dedicati.
- Il trainer deve avere alto potere di azione sui casi mostrati, ma non tramite shortcut che saltano registrazioni auditabili.
- La timeline non deve essere un feed cronologico unico di record grezzi.
- L'unita di prodotto mostrata al trainer e il `case operativo`, non il singolo segnale di database.

## Core Model

### Signal

Fatto grezzo, osservabile e deterministico.

Esempi:

- rata scaduta;
- anamnesi mancante;
- sessione oggi alle 18:00;
- programma senza review da 24 giorni;
- spesa ricorrente non confermata nel mese corrente.

### Case

Unita operativa aggregata, mostrata al trainer come problema o opportunita da gestire.

Esempi:

- `Onboarding Marco Rossi bloccato`
- `Rinnovo contratto Rossi entro 7 giorni`
- `Affitto studio di marzo da confermare`

Regola chiave: il trainer vede casi, non record grezzi.

### Action

Azione principale o secondaria con cui il trainer gestisce il case.

Esempi:

- `Apri prossimo step`
- `Registra incasso`
- `Crea rinnovo`
- `Attiva programma`
- `Snooze 1g`

## Workspace Architecture

FitManager introduce un solo motore operativo con 4 lenti native:

- `Oggi`
- `Onboarding`
- `Programmi`
- `Rinnovi & Incassi`

Ogni workspace e una vista filtrata e gerarchizzata sullo stesso insieme di casi operativi.

### Route map target

- `/` -> `Oggi`
- `/panoramica` -> overview secondaria dell'attuale dashboard
- `/workspace/onboarding` -> `Onboarding`
- `/workspace/programmi` -> `Programmi`
- `/workspace/rinnovi-incassi` -> `Rinnovi & Incassi`

Nota: il naming finale route puo cambiare, ma la semantica prodotto va bloccata in questa spec.

## Oggi Page Structure v1

```text
[ Workspace Switcher ]
Oggi | Onboarding | Programmi | Rinnovi & Incassi

[ Header ]
Titolo pagina + data + stato giornata + Command Palette

[ Focus Row ]
Next Best Action | Agenda Live | KPI compatti (Da fare ora / Oggi / Entro 7 giorni)

[ Main Area ]
Colonna principale: coda operativa deduplicata
Colonna secondaria: agenda oraria + dettaglio del case selezionato

[ Bottom Area ]
Completati oggi | In attesa / Snoozed
```

## Block Hierarchy v1

### 1. Workspace Switcher

Switch persistente tra le 4 viste native. Deve rendere immediata la sensazione di "modalita di lavoro".

### 2. Header

Contiene:

- titolo workspace;
- data estesa;
- micro-stato della giornata;
- accesso alla Command Palette.

### 3. Focus Row

Contiene:

- `Next Best Action`: un solo case dominante cross-domain;
- `Agenda Live`: prossimi slot orari della giornata;
- 3 KPI operativi non-finanziari: `Da fare ora`, `Oggi`, `Entro 7 giorni`.

### 4. Coda Operativa

Lista principale dei case, ordinata per impatto e non per semplice timestamp.

Bucket target:

- `Adesso`
- `Oggi`
- `Entro 3 giorni`
- `Entro 7 giorni`
- `In attesa`

### 5. Pannello Dettaglio Case

Mostra:

- perche il case e comparso;
- segnali che lo compongono;
- entita collegate;
- CTA primaria;
- quick actions;
- mini storico recente.

### 6. Completati Oggi

Sezione chiusa di default, utile per progress feedback senza inquinare la parte attiva.

## Card Anatomy v1

Ogni case card deve usare una grammatica uniforme:

- badge dominio: `Onboarding`, `Programmi`, `Agenda`, `Incassi`, `Rinnovi`, `Ops`;
- badge urgenza: `Scaduto`, `Oggi`, `3g`, `7g`, `In attesa`;
- titolo leggibile in un colpo solo;
- reason line esplicita;
- CTA primaria unica;
- massimo 3-4 quick actions;
- apertura del pannello dettaglio al click sulla card.

Regola: una card deve rispondere in meno di 2 secondi a tre domande:

1. Perche la vedo?
2. Quanto e urgente?
3. Cosa devo fare adesso?

## Timeline Strategy v1

La timeline unificata viene esplicitamente scartata.

FitManager adotta una lettura doppia:

### Timeline Agenda

Contiene solo elementi con orario reale:

- sessioni;
- colloqui;
- appuntamenti;
- eventi calendario.

### Operational Queue

Contiene case privi di orario preciso ma con urgenza operativa:

- onboarding bloccati;
- review programmi dovute;
- rate scadute;
- rinnovi in arrivo;
- spese da confermare;
- follow-up;
- riattivazioni.

Urgenza espressa per finestra, non per timestamp grezzo:

- `overdue`
- `today`
- `3 giorni`
- `7 giorni`
- `future`

## Operational Case Catalog v1

| Code | Nome | Root entity | Workspace principale | Regola di promozione in `Oggi` | CTA primaria |
|---|---|---|---|---|---|
| `ONB-01` | Readiness cliente | `client_id` | `Onboarding` | se onboarding fermo >24h, se esiste appuntamento entro 7 giorni o se uno step e overdue | `Apri prossimo step` |
| `DAY-01` | Sessione imminente | `event_id` | `Oggi` | sempre | `Apri agenda` |
| `DAY-02` | Follow-up post sessione | `event_id` o `client_id` | `Oggi` | entro 24h da no-show o sessione senza next action | `Crea follow-up` |
| `TODO-01` | Todo manuale | `todo_id` | `Oggi` | se scaduto o oggi | `Completa` |
| `PRG-01` | Programma da attivare | `plan_id` | `Programmi` | se il piano parte oggi/domani o il cliente ha gia sessioni fissate | `Attiva programma` |
| `PRG-02` | Review programma dovuta | `plan_id` | `Programmi` | da `today` in poi | `Apri review` |
| `PRG-03` | Compliance a rischio | `plan_id` | `Programmi` | se oltre soglia rischio o con review/sessione vicina | `Apri monitoraggio` |
| `PRG-04` | Fine ciclo / prossimo piano | `plan_id` | `Programmi` | ultimi 7 giorni del ciclo o piano completato senza successore | `Prepara prossimo piano` |
| `FIN-01` | Incasso critico | `contract_id` | `Rinnovi & Incassi` | sempre se esiste arretrato | `Registra incasso` |
| `FIN-02` | Incasso imminente | `contract_id` | `Rinnovi & Incassi` | per rate oggi o entro 3 giorni | `Apri scadenza` |
| `FIN-03` | Rinnovo da proporre | `contract_id` | `Rinnovi & Incassi` | entro 14 giorni dalla scadenza o crediti residui bassi | `Crea rinnovo` |
| `FIN-04` | Spesa ricorrente da confermare | `expense_id + month` | `Rinnovi & Incassi` | nel mese corrente se non confermata | `Conferma spesa` |
| `REL-01` | Cliente inattivo da riattivare | `client_id` | `Oggi` o `Onboarding` | solo come opportunita strategica, mai sopra casi urgenti | `Crea follow-up` |
| `OPS-01` | Anomalia operativa | variabile | `Oggi` | solo se blocca lavoro reale | `Risolvi` |
| `PORT-01` | Questionario cliente in sospeso | `client_id` o `share_token` | `Onboarding` | se onboarding fermo o appuntamento vicino | `Apri cliente` |

## Merge Rules v1

- Un solo case `ONB-01` per cliente.
- Un solo case `FIN-01` per contratto e finestra di arretrato.
- Un solo case programma dominante per `plan_id` quando review/compliance/fine ciclo insistono sullo stesso piano.
- `DAY-01` domina quando esiste un orario reale vicino; gli altri segnali dello stesso cliente si mostrano nel dettaglio.
- La promozione di un case in `Oggi` non crea una copia separata: cambia solo la visibilita.
- Una card non puo mostrare piu di 3 segnali interni in preview. Gli altri stanno nel pannello dettaglio.

## Priority Rules v1

Ordine raccomandato cross-domain:

1. eventi con orario reale e blocco operativo imminente (`DAY-01`);
2. perdita economica attuale (`FIN-01`);
3. onboarding bloccato con impatto su avvio/appuntamento (`ONB-01`);
4. attivazioni e review programma (`PRG-01`, `PRG-02`, `PRG-03`, `PRG-04`);
5. incassi e rinnovi imminenti ma non ancora critici (`FIN-02`, `FIN-03`);
6. spese ricorrenti da confermare (`FIN-04`);
7. opportunita e riattivazioni (`REL-01`);
8. todo manuali e housekeeping (`TODO-01`, `OPS-01`) se non bloccanti.

## Action Model v1

### Azioni generiche

- `Apri`
- `Snooze`
- `Segna gestito`
- `Converti in todo`
- `Aggiungi nota`

### Azioni di dominio

- `Avvia anamnesi`
- `Registra misure`
- `Attiva programma`
- `Apri review`
- `Registra incasso`
- `Crea rinnovo`
- `Conferma spesa`
- `Apri agenda`

### Guardrail

- `Snooze` e consentito sui casi soft e operativi, non come sostituto di una registrazione contabile.
- `Segna gestito` non puo sostituire azioni auditabili su incassi, spese o contratti.
- Ogni case deve avere una CTA primaria unica.
- Il pannello dettaglio deve sempre spiegare la reason line in forma esplicita.

## Workspace-Specific Display Rules

### `Oggi`

- focus cross-domain;
- no feed cronologico unico;
- dati finanziari solo come segnali sintetici e priorita, non come superficie estesa;
- obiettivo: regia della giornata.

### `Onboarding`

- raggruppamento per stadio del journey;
- enfasi su step mancanti e blocchi di readiness;
- vista secondaria piu approfondita rispetto a `Oggi`.

### `Programmi`

- enfasi su attivazioni, review, compliance, fine ciclo;
- linguaggio tecnico e metodologico;
- contesto economico non prioritario.

### `Rinnovi & Incassi`

- qui sono ammessi importi completi, date complete, aging e rischio;
- visibilita piena su rate, rinnovi, spese ricorrenti e scadenze economiche;
- action model piu rigoroso e auditabile.

## Rollout Plan

### Phase 0 - Documentation Lock

- approvare questa spec;
- approvare ADR con decisione architetturale;
- allineare naming di home/dashboard/workspace.

### Phase 1 - Information Architecture

- definire route finale;
- definire workspace switcher e naming prodotto;
- definire i bucket di urgenza.

### Phase 2 - Data and API Design

- mappare segnali esistenti ai `case type`;
- definire chiavi di merge e priorita;
- definire shape read-only del payload workspace.

### Phase 3 - Frontend Delivery

- introdurre `Oggi` come nuova home post-login;
- spostare overview attuale in `Panoramica`;
- costruire agenda rail, queue operativa e case detail panel.

### Phase 4 - Trainer Power Features

- quick actions;
- snooze/in attesa;
- completed today;
- viste salvate future.

## Acceptance Criteria

- Funzionale:
  - esiste un modello prodotto unificato per `Signal -> Case -> Action`;
  - `Oggi` e definita come nuova home post-login target;
  - i 4 workspace nativi condividono lo stesso motore concettuale;
  - il catalogo minimo dei casi operativi e documentato.
- UX:
  - la pagina `Oggi` separa agenda oraria e coda operativa;
  - le regole anti-rumore e anti-duplicazione sono esplicite;
  - la finanza completa e confinata al workspace dedicato.
- Tecnico (type sync, query invalidation, security):
  - la spec preserva privacy-first overview e contesti finance dedicati;
  - la futura implementazione e guidata da comportamento deterministico, non da ranking opaco;
  - la spec non introduce bypass per azioni auditabili.

## Test Plan

- Unit/Integration:
  - non applicabile in questo step docs-only;
  - da pianificare in implementazione: test di merge, ranking, promozione, anti-duplicazione.
- Manual checks:
  - review manuale coerenza con principi di prodotto e privacy;
  - review manuale coerenza con dashboard/worklist esistenti.
- Build/Lint gates:
  - non applicabile in questo step docs-only.

## Risks and Mitigation

- Rischio 1: il workspace `Oggi` diventa una dashboard troppo densa.
  - Mitigazione 1: mostrare solo case deduplicati, non segnali grezzi.
- Rischio 2: finanza e operations si mescolano in modo rumoroso.
  - Mitigazione 2: mantenere `Rinnovi & Incassi` come vista finanziaria completa e `Oggi` come regia sintetica.
- Rischio 3: troppa "magia" nella priorita dei casi.
  - Mitigazione 3: esplicitare priority rules e reason line su ogni card.
- Rischio 4: duplicazioni tra workspace nativi.
  - Mitigazione 4: un singolo case puo essere promosso, ma resta un solo oggetto logico.

## Rollback Plan

Se la futura implementazione risultasse rumorosa o poco chiara:

- mantenere la dashboard overview attuale come default;
- spostare `Oggi` dietro feature flag o route secondaria;
- ridurre il catalogo casi ai soli domini `Agenda + Onboarding + Incassi`;
- disattivare temporaneamente le promotion rules piu aggressive.

## Notes

- Deliverable di questo upgrade: documentazione e decisioni, nessun cambio runtime.
- Related docs:
  - `docs/adr/ADR-2026-03-09-operational-workspace-case-engine.md`
  - `docs/upgrades/specs/UPG-2026-03-06-34-myportal-v2-worklist-architecture.md`
  - `docs/upgrades/specs/UPG-2026-03-09-01-client-profile-crm-hub-redesign.md`
