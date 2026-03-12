# UPG-2026-03-12-26 - Frontend Visual Governance Refactor

## Metadata

- Upgrade ID: `UPG-2026-03-12-26`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Visual System + Architecture`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Il primo layer intermedio introdotto con `UPG-2026-03-12-25` era corretto ma ancora troppo vicino a `globals.css`.

Problema residuo:

- `globals.css` continuava a mescolare fondazione globale e recipe di prodotto;
- il dialetto visivo di `/oggi` restava dentro la root authority;
- la gerarchia di autorita' visiva non era ancora netta abbastanza per impedire nuove isole bespoke.

Questo microstep non ridisegna pagine.
Ristruttura la governance visiva in livelli piu' leggibili e scalabili.

## Target Hierarchy

### 1. Global Foundation

Governo: `frontend/src/app/globals.css`

Qui vivono solo:

- vendor overrides globali (`react-big-calendar`, print, spotlight);
- theme tokens e semantic variables root/dark;
- motion globale riusabile (`shimmer`, `mesh-float`, `spotlight-pulse`);
- base layer (`body`, border/ring defaults).

Qui non devono vivere:

- surface roles di prodotto;
- shell roles di pagina;
- dialetti visivi di feature.

### 2. Shared Product Recipes

Governo: `frontend/src/styles/product-recipes.css`

Qui vivono:

- shell roles condivisi (`bg-mesh-login`, `bg-mesh-app`);
- surface roles (`page`, `hero`, `dossier`, `context`, `signal`, `chart`);
- semantic chip roles;
- shared interaction pattern minimale delle surface (`interactive`).

Qui non vivono:

- semantica business;
- ranking/priority logic;
- layout di pagina.

### 3. Component Primitives / Adapters

Governo: `frontend/src/components/ui/*` e `frontend/src/components/ui/surface-role.ts`

Qui vivono:

- primitive UI;
- adapter ergonomici per consumare i recipe condivisi via CVA.

Qui non vivono:

- stilizzazioni feature-specifiche;
- metafore di pagina.

### 4. Feature / Page-local Composition

Governo: route e componenti locali, per questo microstep:

- `frontend/src/app/(dashboard)/oggi/page.tsx`
- `frontend/src/app/(dashboard)/oggi/oggi-workspace.css`

Qui vivono solo:

- orchestration locale;
- layout locale;
- dialetto visuale strettamente feature-specifico.

Qui non devono vivere:

- nuovi token;
- recipe condivisi ri-definiti;
- shell roles globali.

## What Changed

- Estratti da `globals.css` i shell roles condivisi e i surface/chip recipes in `frontend/src/styles/product-recipes.css`.
- Estratto da `globals.css` il blocco feature-specifico `/oggi` in `frontend/src/app/(dashboard)/oggi/oggi-workspace.css`.
- Import chiariti:
  - `frontend/src/app/layout.tsx` importa `globals.css` + `product-recipes.css`
  - `frontend/src/app/(dashboard)/oggi/page.tsx` importa `oggi-workspace.css`
- `frontend/src/components/workspace/OggiTimeline.tsx` usa ora surface/chip roles condivisi per shell ed empty state; il resto del dialetto operativo resta confinato nel CSS locale della route.

## Outcome

- `globals.css` torna ad essere una root authority piu' neutra;
- il layer intermedio non e' piu' implicito: ha un file dedicato e un path di consumo chiaro;
- `/oggi` smette di far trapelare il proprio dialetto dentro la fondazione globale;
- per nuovi componenti e' piu' naturale consumare `product-recipes.css` via `surface-role.ts` che copiare gradienti o border bespoke.

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/layout.tsx" "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiTimeline.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `git diff --check`

## Residual Risks

- `workspace-ui.ts` resta ancora un punto ibrido tra semantica dominio e toni visuali;
- altre isole locali (`dashboard`, `clienti`, `agenda`) non sono ancora migrate;
- `PREFLIGHT_META` in `OggiTimeline` conserva ancora parte del mapping visuale locale, anche se la shell principale ora consuma recipe condivisi.
