# UPG-2026-03-11-19 - Oggi Zero-Based Redesign Benchmark

## Metadata

- Upgrade ID: `UPG-2026-03-11-19`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `CRM UX Strategy + Workspace Design System + Benchmarking`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo due iterazioni implementative su `Oggi`, il verdetto utente e chiaro:

- la struttura e migliorata;
- il livello grafico non e ancora quello giusto;
- serve un redesign piu radicale, non un altro pass incrementale.

Questo microstep non prova a salvare la soluzione corrente.
Serve a:

1. azzerare la grammatica visiva di partenza;
2. confrontare `Oggi` con best practice attuali di CRM top su fonti ufficiali;
3. aggiornare le skill locali in modo da impedire un altro output troppo card-based e troppo alto in verticale.

## Benchmark Sources Used

Solo fonti ufficiali / primarie:

- HubSpot Sales Workspace:
  - `review-sales-activity-in-the-sales-workspace`
  - `use-the-prospecting-queue`
- monday CRM:
  - `Timeline Overview`
  - `Emails & Activities: quick actions on mobile`
- Pipedrive:
  - `Pulse feed`
  - `Activity Priority Labels`
- Salesforce Sales Cloud:
  - `Sales Cloud`
  - `features / activity management / pipeline management`

## What Top CRMs Are Actually Doing

### 1. One operational home, not a decorative dashboard

HubSpot descrive il `Sales Workspace` come un posto unico per gestire il carico giornaliero,
unificando attivita pipeline e closing in una sola home operativa.

Traduzione pratica per FitManager:

- `Oggi` non deve sembrare un cruscotto con blocchi;
- deve sembrare il luogo principale del lavoro vivo.

### 2. Queue plus preview is a default pattern, not an exception

HubSpot prospecting queue porta task, activity e guided actions nella stessa surface e apre il
preview/contesto a lato.

Traduzione pratica:

- la coppia `queue + dossier` va irrigidita come grammatica primaria;
- la queue non puo essere subordinata a hero, card summary o utility panels ridondanti.

### 3. Next best action beats generic browsing

HubSpot guided actions e Salesforce guided selling convergono sullo stesso principio:

- l’utente deve vedere una prossima mossa motivata;
- quella mossa deve essere priorizzata con criterio esplicito.

Traduzione pratica:

- ogni riga di `Oggi` deve rendere ovvio il passo successivo senza aprire un’altra vista.

### 4. Activity timeline is not an optional extra

monday CRM mette timeline overview, unread count, color states e activity timeline come parte
visibile del record.

Traduzione pratica:

- il contesto cliente non deve apparire come un mini-report accessorio;
- deve comportarsi come un activity/status dossier compatto e sempre utile.

### 5. Quick capture must reduce friction before association

monday CRM quick actions mobile permette di catturare nota o recap subito e associare dopo.

Traduzione pratica:

- nei workspace forti non si forza sempre l’utente a entrare nel record giusto prima di scrivere;
- FitManager deve introdurre quick capture piu diretto nel launch UX.

### 6. At-a-glance attention beats verbose sectioning

Pipedrive Pulse feed organizza il lavoro in pochi tab forti, con follow-up, attivita pianificate
oggi e filtri persistiti.

Traduzione pratica:

- troppi bucket stacked con header e sottotitoli lunghi degradano l’attenzione;
- meglio meno lane, piu tensione, piu persistenza stato/filtro.

### 7. Single source of truth plus single consolidated view

Salesforce insiste su due idee:

- activity management come single source of truth;
- pipeline management in a single consolidated view.

Traduzione pratica:

- `Oggi` non deve frammentare agenda, queue, dossier e supporto in quattro micro-surface che
  competono tra loro;
- deve consolidare.

## Verdict On Current Oggi

### What is now correct

- `queue + detail` come backbone;
- mantenimento del contesto cliente/sessione;
- agenda subordinata;
- nessun ritorno alla dashboard overview classica.

### What is still wrong

- la pagina nasce ancora da una grammatica `card stack` e non da una grammatica `lane + dossier`;
- troppo spazio verticale viene consumato prima dei casi reali;
- backlog e bucket sono ancora troppo esplicativi e troppo poco lane-oriented;
- il rail destro ha utilita, ma non ancora una forma abbastanza canonica;
- manca un vero quick capture layer.

## Zero-Based Redesign Direction

### Hard reset principle

Il prossimo redesign di `Oggi` non deve partire da:

- come comprimere meglio queste card

ma da:

- qual e la superficie piu efficace per far muovere un trainer tra casi vivi, sessioni e follow-up.

### New target grammar

1. `Oggi` come newsroom operativa:
   - masthead corto;
   - una sola utility strip;
   - una lane principale di lavoro.
2. Queue come righe dossier:
   - non card alte;
   - non mini pannelli autonomi;
   - righe dense con rail, titolo, meta, reason e CTA.
3. Backlog compresso:
   - meno sezioni stacked;
   - lane switch o segmented state per `3g / 7g / waiting`.
4. Right rail canonico:
   - detail panel compatto;
   - client context ancora piu timeline/status oriented;
   - scroll interno, non crescita libera.
5. Quick capture sempre vicino:
   - nota;
   - misura;
   - appuntamento;
   - follow-up.

## Skill Pack Changes Introduced

In questo microstep vengono aggiornate le skill locali per evitare di ricadere nello stesso output:

- `fitmanager-operational-workspace-design`
  - preferenza esplicita per `row dossier plus compact lane headers`
  - density targets per workspace operativi
  - red flags contro tall cards, utility duplicate e `Dettaglio` ridondante
- `fitmanager-responsive-adaptive-ui`
  - nuovi guardrail su header compatti, lane header single-line, row density e first fold utile
- `responsive-density-matrix`
  - target espliciti per workspace header, bucket header e queue row

## No-Code Decision

Questo microstep e volutamente docs/system-only.

Per un redesign massiccio il prossimo passo corretto non e una patch spot.
Il prossimo passo corretto e:

- una nuova spec di redesign zero-based di `Oggi`;
- poi implementazione netta sopra la nuova grammatica.

## Recommended Next Step

Aprire `UPG-2026-03-11-20` come:

- `Oggi v4 zero-based redesign`

con deliverable:

- nuova IA della pagina;
- nuova grammatica righe/lane;
- nuova shell rail destro;
- quick action layer;
- persistenza URL di selezione/filtro.
