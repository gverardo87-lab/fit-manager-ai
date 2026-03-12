# UPG-2026-03-12-33 - Oggi PRO+ Regression Rollback v1

## Metadata

- Upgrade ID: `UPG-2026-03-12-33`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Oggi Runtime`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Il pass `UPG-2026-03-12-32` ha alzato la firma visiva, ma ha introdotto una regressione operativa reale:

- troppe sezioni percepite come righe full-width;
- breakpoint desktop troppo tardo (`xl`) rispetto alla larghezza utile della route con sidebar;
- scroll verticale eccessivo;
- perdita della sensazione di cockpit compatto.

Il feedback utente e' stato esplicito: grande passo indietro sul comportamento della pagina.

## Decision

Rollback mirato della grammatica introdotta nel pass precedente:

1. il layout `2 colonne` torna ad attivarsi a `lg`, non a `xl`;
2. le griglie che si erano spezzate in verticale tornano in una disposizione piu' orizzontale su desktop;
3. timeline e dossier ricevono altezza controllata con scroll interno desktop;
4. il dossier destro riduce stacking e torna piu' compatto.

Nessun cambio ai contratti dati o alla logica di selezione.

## Changes

### `frontend/src/app/(dashboard)/oggi/page.tsx`

- shell principale riportata a `lg:grid-cols-*`
- timeline e dossier con `max-height` desktop e `overflow-y-auto`

### `frontend/src/components/workspace/OggiHero.tsx`

- command bar piu' bassa
- composizione heading/stats orizzontale gia' da `lg`
- summary stats in singola riga desktop

### `frontend/src/components/workspace/OggiTimeline.tsx`

- righe piu' compatte
- gap ridotti tra lane e card
- header meno alto

### `frontend/src/components/workspace/OggiCommandCenter.tsx`

- stats grid a 4 colonne da `lg`
- griglia interna del dossier anticipata a `lg`
- note pre-seduta piu' compatte
- ridotta la verticalita' complessiva del pannello

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiHero.tsx" "src/components/workspace/OggiTimeline.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `git diff --check`

## Residual Risks

- Serve ancora una review visuale reale nel browser per capire se il compromesso `max-height + scroll interno` va rifinito su laptop bassi.
- Il CSS locale di `/oggi` resta piu' espressivo del layer shared; va tenuto sotto controllo per non reintrodurre drift.
