# UPG-2026-03-11-16 - Oggi v3 Launch Workspace Spec

## Metadata

- Upgrade ID: `UPG-2026-03-11-16`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `Workspace UX + Launch Readiness + CRM Operations`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `planned`

## Problem

`Oggi` esiste, ma la route attuale non e ancora il vero workspace operativo del launch.

Il drift concreto e questo:

- `frontend/src/app/(dashboard)/oggi/page.tsx` usa ancora `useSessionPrep()` e una grammatica
  centrata su `SessionPrepCard`;
- il contratto read-only workspace piu evoluto esiste gia (`useWorkspaceToday()`,
  `useWorkspaceCases()`, `useWorkspaceCaseDetail()`), ma non guida la pagina;
- i componenti `WorkspaceCaseCard`, `WorkspaceDetailPanel` e `WorkspaceAgendaPanel` esistono,
  ma non sono il backbone della surface `Oggi`;
- la spec `UPG-2026-03-09-08` dichiara una logica `stack + detail`, mentre il file reale si e
  spostato di nuovo verso una pagina specializzata sulla preparazione sessione.

Questa situazione lascia aperti tre rischi di launch:

1. `Oggi` non e ancora la "mental home" del trainer.
2. Le nuove skill UX non vengono testate nel caso piu difficile e piu utile.
3. Il prodotto resta con una pagina di prova buona per session prep, ma non sufficiente come
   workspace quotidiano cross-domain.

## Desired Outcome

Definire `Oggi v3` come primo workspace launch-grade di FitManager:

- action-first, non dashboard-first;
- centrato sulla queue operativa deduplicata;
- con detail panel canonico del caso selezionato;
- con agenda subordinata, non competitiva;
- alimentato dal contratto workspace read-only gia esistente;
- abbastanza forte da diventare il vero banco prova delle nuove skill:
  - `fitmanager-operational-workspace-design`
  - `fitmanager-responsive-adaptive-ui`

Il risultato atteso non e solo una pagina migliore.
Il risultato atteso e un criterio oggettivo per capire se il nuovo skill pack sta davvero alzando
il livello oppure no.

## Scope

- In scope:
  - definizione docs-first di `Oggi v3` come workspace action-first;
  - chiarimento del drift fra route attuale e contratto workspace esistente;
  - page structure target desktop/tablet/mobile;
  - gerarchia di bucket, selezione caso, ruolo dell'agenda e del detail panel;
  - uso corretto dei hook workspace read-only gia disponibili;
  - criteri di review per tarare skill e agent routing dopo la prima implementazione.
- Out of scope:
  - modifica runtime frontend in questo microstep;
  - cambio di home post-login da `/` a `/oggi`;
  - nuove API o mutation workspace (`snooze`, `mark managed`, `seen`, `quick actions`);
  - nuovi `case_kind`;
  - tuning delle skill prima di aver implementato e reviewato `Oggi v3`.

## Impact Map

- Files/modules touched:
  - `docs/upgrades/specs/UPG-2026-03-11-16-oggi-v3-launch-workspace-spec.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend` | `docs`
- Invarianti da preservare:
  - `Oggi` resta privacy-safe e non apre una surface finance completa;
  - la queue operativa deve restare deterministica e spiegabile;
  - nessuna regressione verso una "seconda dashboard";
  - agenda e detail non devono distruggere la leggibilita della queue;
  - la responsive non deve appiattire la pagina in una pila generica di card.

## Current-State Verdict

### Cosa va tenuto

- esiste gia un contratto workspace read-only solido;
- esistono gia componenti che parlano la lingua giusta del workspace;
- esiste gia una policy forte su ranking, dominance e viewport budget;
- l'agenda subordinata introdotta nei pass precedenti e una direzione corretta.

### Cosa va scartato

- il backbone `session-prep-first` della route attuale;
- il focus esclusivo sulle sessioni come se `Oggi` fosse solo un preflight clinico;
- hero e microcopy che fanno sembrare la pagina un briefing test, non uno strumento inevitabile.

### Verdetto netto

`Oggi` oggi non e da buttare, ma non e ancora il workspace launch-grade da usare come standard
del CRM. Va trattato come una base intermedia da rifondare sopra il contratto workspace vero.

## Locked Decisions

- `Oggi` resta su route `/oggi` in questa fase: niente cutover della home finche la surface non e
  convincente sul serio.
- Il backbone dati di `Oggi v3` deve usare:
  - `useWorkspaceToday()`
  - `useWorkspaceCases()`
  - `useWorkspaceCaseDetail()`
- `useSessionPrep()` puo restare come sorgente secondaria o come modulo specialistico, ma non come
  spina dorsale della pagina.
- Il centro di gravita della pagina e la queue, non l'hero, non l'agenda, non i KPI.
- Il detail panel e un dossier operativo del caso selezionato, non un box accessorio.
- Agenda visibile solo quando cambia il comportamento della giornata.
- Nessun importo finance completo in `Oggi`.

## Oggi v3 Structure

### 1. Header breve, non hero dominante

Il top della pagina deve rispondere a:

- che giorno e;
- quanto e piena la giornata;
- quanti casi meritano attenzione adesso;
- qual e il tono operativo della giornata.

Non deve rubare troppo spazio alla queue.

Contenuto raccomandato:

- titolo `Oggi`;
- data estesa;
- brief di 1 riga;
- 2 o 3 contatori compatti:
  - `Adesso`
  - `Oggi`
  - opzionale `Puo aspettare`

### 2. Agenda strip subordinata

`WorkspaceAgendaPanel` resta utile, ma solo come strip di supporto.

Regola:

- visibile solo se esiste uno slot `current` o un evento che puo cambiare la prossima mossa entro
  la finestra operativa;
- massimo 1 item in prima vista;
- mai sopra o piu forte della queue.

### 3. Main shell = Queue + Detail

Desktop target:

- colonna sinistra dominante per la queue;
- colonna destra sticky per il detail panel.

La pagina deve far percepire subito che:

- a sinistra c e il lavoro;
- a destra c e il contesto del lavoro selezionato.

### 4. Queue buckets

Bucket target iniziali:

- `Adesso`
- `Oggi`
- `Puo aspettare`

Regole:

- `Adesso` contiene solo il lavoro che cambia davvero l'ordine del trainer;
- `Oggi` contiene il lavoro rilevante ma non dominante;
- `Puo aspettare` puo essere compresso o collassabile in base alla pressione dei bucket sopra.

### 5. Detail panel canonico

Ordine interno target:

1. azione consigliata
2. perche ora
3. contesto collegato
4. timeline sintetica

Il detail panel deve spiegare il caso senza costringere a ulteriori salti.

## Data Contract for v3

### Primary sources

- `useWorkspaceToday()`
  - summary minima
  - `focus_case`
  - `agenda`
  - total di sezione
- `useWorkspaceCases()`
  - liste bucketizzate server-side
  - budget coerente col motore
- `useWorkspaceCaseDetail()`
  - dossier del caso selezionato

### Default selection rule

Ordine raccomandato:

1. `today.focus_case` se ancora visibile nella queue
2. primo caso in `Adesso`
3. primo caso in `Oggi`
4. nessun caso selezionato se la queue e vuota

### Explicit anti-goal

`Oggi v3` non deve fare fetch paralleli eterogenei che ricreano una mini-dashboard.
Se il motore workspace sa gia selezionare e comprimere, la pagina deve rispettare quel contratto.

## UI Grammar

### Case card

Ogni card deve rispondere in 2 secondi a:

1. perche la vedo;
2. quanto e urgente;
3. cosa faccio adesso.

La grammatica target e:

- badge `kind`;
- badge `severity`;
- titolo;
- `reason line`;
- poche meta utili;
- una CTA primaria;
- uno stato `selected` inequivocabile.

### Detail panel

La grammatica target e:

- CTA primaria e secondarie vicine;
- spiegazione del trigger;
- contesto navigabile;
- timeline ridotta e leggibile.

### Copy

La copy deve essere piu secca e piu operativa:

- meno saluto/briefing;
- piu linguaggio da collega operativo;
- nessuna estetica da pagina demo.

## Responsive Contract

### Desktop

- queue dominante;
- detail sticky;
- agenda strip compatta;
- nessun hero voluminoso sopra la fold.

### Tablet

- preservare il feeling `workspace`, non ridurlo a una dashboard impilata;
- mantenere split queue/detail quando regge davvero;
- se si stacka, il caso selezionato deve restare evidente e vicino al suo dettaglio.

### Mobile

- queue prima;
- detail subito dopo il caso selezionato o in una sezione chiaramente associata;
- niente pila indifferenziata di pannelli equivalenti;
- i bucket devono restare leggibili e toccabili;
- l'agenda non deve generare rumore sopra il lavoro reale.

## Implementation Phasing

### Phase 1 - Shell refactor on existing contracts

- sostituire il backbone `session-prep` con il backbone workspace read-only;
- ricostruire `/oggi` come `queue + detail`;
- mantenere l'agenda subordinata;
- nessuna mutation.

### Phase 2 - State continuity

- valutare persistenza minima di caso selezionato e bucket in URL;
- garantire continuita di ritorno da cliente/contratto quando serve.

### Phase 3 - Skill validation loop

Dopo la prima implementazione reale, fare review esplicita con 3 domande:

1. la skill `operational-workspace-design` ha prodotto una queue davvero dominante?
2. la skill `responsive-adaptive-ui` ha preservato la logica `queue -> detail` su tablet/mobile?
3. l'agent routing e stato sufficiente o ha ancora un bias da dashboard?

Solo dopo questa review si autorizza il tuning delle skill.

## Acceptance Criteria

- Funzionale:
  - `Oggi v3` e definito sopra i contratti workspace esistenti, non sopra `session-prep`;
  - la struttura `queue + detail + agenda subordinata` e chiaramente bloccata;
  - esiste una regola esplicita per la selezione del caso iniziale.
- UX:
  - la pagina target non comunica piu "pagina test" o "seconda dashboard";
  - la queue e il centro visivo e cognitivo;
  - il detail panel e canonico e spiegabile;
  - il responsive target preserva l'identita workspace.
- Governance:
  - la spec definisce come usare `Oggi` per validare o correggere il nuovo pacchetto skill.

## Verification Plan

Questo microstep e docs-only.

Verifiche richieste:

- review manuale di:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/hooks/useWorkspace.ts`
  - `docs/upgrades/specs/UPG-2026-03-09-02-operational-workspace-home-v1.md`
  - `docs/upgrades/specs/UPG-2026-03-09-07-workspace-oggi-frontend-shell-v1.md`
  - `docs/upgrades/specs/UPG-2026-03-09-08-workspace-oggi-v2-stack-refactor.md`
  - `docs/upgrades/specs/UPG-2026-03-09-11-workspace-ranking-and-dominance-matrix-v1.md`
- grep mirato su:
  - `useSessionPrep`
  - `useWorkspaceToday`
  - `WorkspaceCaseCard`
  - `WorkspaceDetailPanel`
  - `WorkspaceAgendaPanel`
- `git diff --check`

## Risks and Mitigation

- Rischio 1: la futura implementazione fa solo un restyling e non il cambio di backbone.
  - Mitigazione 1: la spec blocca esplicitamente i hook e la struttura da usare.
- Rischio 2: `Oggi` resta troppo specialistico sul solo preflight sessione.
  - Mitigazione 2: la spec forza il ritorno alla logica `workspace today`.
- Rischio 3: il responsive tradisce ancora il desktop archetype.
  - Mitigazione 3: la validazione della skill responsive e parte della spec, non un optional.
- Rischio 4: si faccia tuning prematuro delle skill senza prova pratica.
  - Mitigazione 4: tuning autorizzato solo dopo review dell'implementazione reale di `Oggi v3`.

## Rollback Plan

Se l'implementazione futura di `Oggi v3` non regge:

- mantenere `/oggi` come route secondaria;
- conservare la dashboard attuale come home;
- tornare temporaneamente a un shell piu stretto, ma sempre basato sul contratto workspace vero.

## Notes

- Questa spec non dichiara ancora `Oggi` come home post-login finale. Dichiara pero che `Oggi`
  deve diventare il primo workspace capace di guadagnarselo.
- `Oggi` viene trattato esplicitamente come proving ground del nuovo skill pack CRM.
