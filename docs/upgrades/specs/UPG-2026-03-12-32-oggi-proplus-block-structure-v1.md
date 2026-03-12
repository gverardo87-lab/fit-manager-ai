# UPG-2026-03-12-32 - Oggi PRO+ Block Structure v1

## Metadata

- Upgrade ID: `UPG-2026-03-12-32`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Oggi Runtime`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo il redesign runtime-first e i pass di densita', `/oggi` era piu' utile ma non ancora percepito come una superficie premium:

- top bar troppo "soft" e poco autorevole;
- timeline ancora letta come stack di card, non come regia temporale;
- dossier destro corretto nei contenuti ma ancora troppo simmetrico e poco dominante;
- `Note pre-seduta` troppo vicine alla grammatica di una textarea disattivata.

Lo screenshot reale della pagina ha confermato che il collo di bottiglia non era la logica, ma la struttura visiva a blocchi.

## Decision

Pass PRO+ strutturale in tre blocchi:

1. `command bar premium`
2. `timeline rail`
3. `focus dossier autorevole`

La logica dati, i contratti API e la promessa operativa della pagina restano invariati. Cambia invece la grammatica visuale della route, con il ritorno intenzionale di un CSS locale dedicato per dare a `/oggi` un materiale piu' deciso senza contaminare il layer shared globale.

## Changes

### `frontend/src/app/(dashboard)/oggi/page.tsx`

- importa esplicitamente `oggi-workspace.css`
- passa a `OggiHero` segnali di trust runtime (`lastUpdatedAt`, `isRefreshing`)
- riequilibra la shell a favore del dossier destro sul desktop largo

### `frontend/src/components/workspace/OggiHero.tsx`

- il variant `compact` diventa una command bar vera, non una strip informativa
- aggiunti segnale di sync, supporto contestuale e blocchi summary piu' densi
- mantenuta la logica di lettura giornaliera senza trasformare la pagina in una dashboard KPI

### `frontend/src/components/workspace/OggiTimeline.tsx`

- la timeline passa da gruppo di card a `rail` con asse verticale implicito
- le lane vuote collassano in strip compatte
- la selezione diventa piu' strutturale con rail laterale, card attiva e continuita' visiva

### `frontend/src/components/workspace/OggiCommandCenter.tsx`

- il pannello focus viene ristrutturato come dossier dominante
- il blocco `Prima di entrare in sala` rompe la simmetria e promuove il caso principale
- il blocco note viene rifatto come scratchpad operativo leggibile
- aggiunto clock locale derivato per il countdown, evitando `setState` sincrono in effect

### `frontend/src/app/(dashboard)/oggi/oggi-workspace.css`

- nuova authority locale della route per command bar, rail, dossier e note
- materiali piu' netti e meno "pastello diffuso"
- reintrodotto un dialetto locale controllato per dare a `/oggi` un'identita' premium specifica

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiHero.tsx" "src/components/workspace/OggiTimeline.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `git diff --check`

## Residual Risks

- Manca ancora una review browser reale post-patch sul primo viewport e sui breakpoint principali; il build e il lint confermano il runtime, non il tuning pixel-level finale.
- Il nuovo dialetto locale di `/oggi` e' intenzionale, ma va tenuto confinato alla route per non riaprire drift sul sistema visivo shared.
