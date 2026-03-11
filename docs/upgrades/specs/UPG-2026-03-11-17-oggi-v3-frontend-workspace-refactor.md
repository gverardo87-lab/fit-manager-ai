# UPG-2026-03-11-17 - Oggi v3 Frontend Workspace Refactor

## Metadata

- Upgrade ID: `UPG-2026-03-11-17`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `Frontend Workspace UX + CRM Operations + Launch Readiness`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Problem

La spec `UPG-2026-03-11-16` ha chiarito che `Oggi` non poteva piu restare una pagina
`session-prep-first`.

Il problema concreto della route reale era triplo:

1. il centro di gravita era `useSessionPrep()` e non il contratto workspace read-only;
2. la pagina mostrava informazioni cliente ricche, ma dentro una grammatica troppo vicina a una
   surface di test/specialistica;
3. il trainer non vedeva subito una queue dominante con detail panel stabile.

Allo stesso tempo, buttare via la ricchezza della vecchia pagina sarebbe stato un errore:
`readiness`, `health checks`, `alert clinici`, `piano attivo`, `crediti` e scorciatoie cliente sono
 informazioni utili e vanno conservate.

## Outcome

`/oggi` viene rifondato come vero workspace `queue + detail`, ma senza perdere il valore della
vecchia vista.

Decisione chiave del microstep:

- `useWorkspaceToday()` e `useWorkspaceCaseDetail()` diventano la shell primaria;
- `useWorkspaceCases()` entra come fetch additivo per il bucket `waiting` espanso;
- `useSessionPrep()` sopravvive solo come layer secondario di contesto cliente/sessione;
- le informazioni ricche del vecchio `session prep` non governano piu la pagina, ma arricchiscono:
  - la card del caso in queue;
  - il rail destro del caso selezionato.

## Scope

- In scope:
  - refactor di `frontend/src/app/(dashboard)/oggi/page.tsx`;
  - nuova grammatica `queue + detail`;
  - contesto cliente/sessione raffinato per il caso selezionato;
  - support line nelle queue card;
  - bucket `waiting` caricato on-demand con `useWorkspaceCases()`;
  - sync documentale completa del microstep.
- Out of scope:
  - nuove API o nuove mutation workspace;
  - persistenza URL di `selectedCase` / espansione `Puo aspettare`;
  - unificazione backend del contratto `workspace today` e `session prep`;
  - change della home post-login da `/` a `/oggi`;
  - tuning finale delle skill prima della review reale della pagina.

## Implementation Summary

### 1. Shell primaria workspace

La route `frontend/src/app/(dashboard)/oggi/page.tsx` ora usa come spina dorsale:

- `useWorkspaceToday()`
- `useWorkspaceCaseDetail()`
- `useWorkspaceCases()` per il backlog `waiting` quando il trainer lo espande

La logica di selezione e stata riallineata a un criterio piu sano:

1. caso esplicitamente selezionato se ancora visibile;
2. `focus_case` se presente nella queue visibile;
3. primo caso disponibile nella queue renderizzata.

### 2. Queue dominante, agenda subordinata

La pagina torna ad avere:

- header breve con data + tono della giornata;
- agenda strip subordinata;
- stack operativo come vero centro di gravita;
- detail panel sticky sulla destra.

I bucket sopra la linea di galleggiamento restano:

- `Adesso`
- `Oggi`
- `Puo aspettare`

Dentro `Puo aspettare`, la pagina distingue:

- `Entro 3 giorni`
- `Entro 7 giorni`
- `In attesa`

### 3. Informazioni cliente conservate e raffinate

Il layer `session-prep` non viene rimosso: viene ricontestualizzato.

Nuovo componente:

- `frontend/src/components/workspace/OggiClientContextPanel.tsx`

Responsabilita:

- mostrare `readiness`;
- mostrare check rapidi cliente con eventuale CTA `Aggiorna`;
- mostrare `alert clinici`;
- mostrare `piano attivo`, `crediti`, ultime sessioni e note appuntamento;
- offrire link veloci a `Profilo cliente` e `Misurazioni`.

In parallelo, `WorkspaceCaseCard` guadagna:

- `supportingLine`
- `hrefTransform`

Questo permette di conservare un riassunto rapido del contesto cliente direttamente nella queue,
senza ricadere in card gigantiste.

### 4. Matching tra caso operativo e contesto sessione

Il matching del contesto `session-prep` avviene lato frontend con euristica esplicita:

1. match per `event_id` quando il caso root e un `event`;
2. fallback a match per `client_id` quando il caso ha entity cliente.

Questo e sufficiente per la fase launch, ma non e ancora un contratto canonico backend.

## Files Touched

- `frontend/src/app/(dashboard)/oggi/page.tsx`
- `frontend/src/components/workspace/OggiClientContextPanel.tsx`
- `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `docs/upgrades/specs/UPG-2026-03-11-17-oggi-v3-frontend-workspace-refactor.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiClientContextPanel.tsx" "src/components/workspace/WorkspaceCaseCard.tsx"`
- review manuale di:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/OggiClientContextPanel.tsx`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `git diff --check`

## Risks Found

### 1. Matching `session-prep` ancora euristico

Il pannello contestuale cliente dipende ancora da un match frontend `event_id -> client_id`.

Rischio:

- alcuni casi non sessione potrebbero non trovare il contesto corretto anche se esiste una
  relazione business piu precisa.

Next smallest corrective step:

- aggiungere nel payload workspace un riferimento canonico opzionale al `session_prep_context`
  oppure un `client_context_key` esplicito.

### 2. Stato pagina non persistito in URL

`selectedCase` e `showLater` restano locali alla route.

Rischio:

- navigazione avanti/indietro o refresh non preservano il punto operativo del trainer.

Next smallest corrective step:

- serializzare `case`, `later`, ed eventuale bucket nell'URL, seguendo lo stesso approccio usato in
  `Rinnovi & Incassi`.

### 3. Copertura test ancora assente

Il microstep e stato verificato con lint mirato e review manuale, ma non ha ancora test frontend
dedicati.

Rischio:

- piccoli drift di selezione caso o matching contesto potrebbero riapparire in refactor successivi.

Next smallest corrective step:

- aggiungere almeno un test focused su selection fallback e support line per i casi con
  `session-prep` disponibile.

## Decision

Il nuovo pacchetto skill regge un primo caso reale:

- `fitmanager-operational-workspace-design` ha spinto la pagina verso `queue dominance`;
- `fitmanager-responsive-adaptive-ui` non ha forzato un ritorno a dashboard/card grid generiche;
- il layer informativo della vecchia pagina e stato salvato senza lasciargli il controllo della
  surface.

Questo non chiude il tuning delle skill, ma fornisce finalmente una base reale su cui giudicarle.
