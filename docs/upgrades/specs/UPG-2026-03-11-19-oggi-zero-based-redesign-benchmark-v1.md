# UPG-2026-03-11-19 - Oggi Zero-Based Redesign Benchmark

## Metadata

- Upgrade ID: `UPG-2026-03-11-19`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `CRM UX Strategy + Workspace Design System + Benchmarking`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

> Benchmark di ispirazione, non source of truth per layout, IA o shell.
> I pattern e le metafore CRM qui raccolti servono come stimolo e anti-card-stack reminder.
> Usare questo documento solo dopo aver definito la page promise e il unit-of-work dominante della route reale `/oggi`.

## Why This Exists

Dopo due iterazioni implementative su `Oggi`, il verdetto utente e chiaro:

- la struttura e migliorata;
- il livello grafico non e ancora quello giusto;
- serve un redesign piu radicale, non un altro pass incrementale.

Questo microstep non prova a salvare la soluzione corrente.
Serve a:

1. azzerare la grammatica visiva di partenza;
2. confrontare `Oggi` con best practice attuali di CRM top su fonti ufficiali;
3. raccogliere spunti per evitare un altro output troppo card-based e troppo alto in verticale.

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

## What Top CRMs Suggest

I pattern CRM sales citati qui sono analogie utili, non mapping strutturali diretti al dominio FitManager.

### 1. One operational home, not a decorative dashboard

HubSpot descrive il `Sales Workspace` come un posto unico per gestire il carico giornaliero,
unificando attivita pipeline e closing in una sola home operativa.

Traduzione pratica per FitManager:

- `Oggi` puo trarre beneficio dall'evitare un cruscotto puramente a blocchi;
- puo funzionare meglio se percepito come luogo principale del lavoro vivo.

### 2. Queue plus preview is a strong pattern to evaluate

HubSpot prospecting queue porta task, activity e guided actions nella stessa surface e apre il
preview/contesto a lato.

Traduzione pratica:

- la coppia `queue + dossier` e una possibile direzione forte da valutare;
- la queue puo restare dominante se migliora davvero il lavoro vivo, senza renderla un default obbligatorio.

### 3. Next best action beats generic browsing

HubSpot guided actions e Salesforce guided selling convergono sullo stesso principio:

- l'utente deve vedere una prossima mossa motivata;
- quella mossa deve essere priorizzata con criterio esplicito.

Traduzione pratica:

- il redesign puo privilegiare casi in cui il passo successivo sia leggibile senza aprire un'altra vista.

### 4. Activity timeline is a useful recurring pattern

monday CRM mette timeline overview, unread count, color states e activity timeline come parte
visibile del record.

Traduzione pratica:

- il contesto cliente non dovrebbe apparire come un mini-report accessorio;
- puo funzionare bene come activity/status dossier compatto se aiuta davvero la page promise scelta.

### 5. Quick capture can reduce friction before association

monday CRM quick actions mobile permette di catturare nota o recap subito e associare dopo.

Traduzione pratica:

- nei workspace forti puo essere utile non forzare sempre l'utente a entrare nel record giusto prima di scrivere;
- per FitManager il quick capture resta una possibile leva, non un vincolo di shell o launch UX.

### 6. At-a-glance attention beats verbose sectioning

Pipedrive Pulse feed organizza il lavoro in pochi tab forti, con follow-up, attivita pianificate
oggi e filtri persistiti.

Traduzione pratica:

- troppi bucket stacked con header e sottotitoli lunghi degradano l'attenzione;
- meno lane e piu tensione operativa possono essere uno stimolo utile, non una struttura obbligatoria.

### 7. Single source of truth plus single consolidated view

Salesforce insiste su due idee:

- activity management come single source of truth;
- pipeline management in a single consolidated view.

Traduzione pratica:

- `Oggi` dovrebbe evitare di frammentare agenda, queue, dossier e supporto in quattro micro-surface che
  competono tra loro;
- il consolidamento resta uno stimolo utile, non una shell obbligatoria.

## Verdict On Current Oggi

### What is now correct

- `queue + detail` come pattern gia esplorato con segnali utili;
- mantenimento del contesto cliente/sessione;
- agenda subordinata;
- nessun ritorno alla dashboard overview classica.

### What is still wrong

- la pagina nasce ancora da una grammatica `card stack` piu che da una grammatica operativa compatta;
- troppo spazio verticale viene consumato prima dei casi reali;
- backlog e bucket sono ancora troppo esplicativi e poco focalizzati sul lavoro vivo;
- il rail destro ha utilita, ma non ancora una forma abbastanza convincente;
- manca ancora una decisione esplicita su quanto quick capture serva davvero a questa route.

## Possible Redesign Directions

### Hard reset principle

Il prossimo redesign di `Oggi` non dovrebbe partire da:

- come comprimere meglio queste card

ma da:

- qual e la superficie piu efficace per far muovere un trainer tra casi vivi, sessioni e follow-up.

### Candidate grammar directions

1. `Oggi` come newsroom operativa:
   - masthead corto;
   - una sola utility strip;
   - una lane principale di lavoro come possibile opzione.
2. Queue come righe dossier:
   - alternativa forte alle card alte;
   - possibile preferenza rispetto a mini pannelli autonomi;
   - righe dense con rail, titolo, meta, reason e CTA come pattern plausibile, non obbligatorio.
3. Backlog compresso:
   - meno sezioni stacked;
   - lane switch o segmented state per `3g / 7g / waiting` come opzione da valutare.
4. Right rail compatto:
   - detail panel compatto;
   - client context piu timeline/status oriented se coerente con la page promise;
   - scroll interno come scelta possibile, non obbligatoria.
5. Quick capture vicino al lavoro:
   - nota;
   - misura;
   - appuntamento;
   - follow-up.
   Come leva opzionale se riduce davvero attrito nel workflow reale.

## Skill Pack Changes Observed

In questo microstep il benchmark ha contribuito ad alcune correzioni storiche nelle skill locali,
ma non ha autorita' per imporne da solo il comportamento futuro:

- `fitmanager-operational-workspace-design`
  - ha spinto verso maggiore attenzione a `row dossier plus compact lane headers`
  - ha contribuito a density targets per workspace operativi
  - ha rafforzato red flags contro tall cards, utility duplicate e `Dettaglio` ridondante
- `fitmanager-responsive-adaptive-ui`
  - ha influenzato guardrail su header compatti, lane header single-line, row density e first fold utile
- `responsive-density-matrix`
  - ha raccolto target per workspace header, bucket header e queue row come riferimento di tuning

## No-Code Decision

Questo microstep e volutamente docs/system-only.

Per un redesign massiccio il prossimo passo corretto non e una patch spot.
Il prossimo passo corretto e:

- una nuova spec di redesign zero-based di `Oggi`;
- poi implementazione netta sopra la direzione scelta dalla route reale.

## Recommended Next Step

Aprire `UPG-2026-03-11-20` come:

- `Oggi v4 zero-based redesign`

con deliverable:

- page promise esplicita;
- unit-of-work dominante;
- nuova IA della pagina;
- eventuale grammatica righe/lane se confermata utile;
- eventuale shell/quick action layer solo se supportati dal workflow reale;
- persistenza URL di selezione/filtro.
