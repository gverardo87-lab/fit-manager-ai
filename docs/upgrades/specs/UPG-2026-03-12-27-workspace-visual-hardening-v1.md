# UPG-2026-03-12-27 - Workspace Visual Hardening

## Metadata

- Upgrade ID: `UPG-2026-03-12-27`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace System + Visual Architecture`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo il refactor di governance visiva del frontend, il prossimo punto debole era il layer workspace condiviso:

- `workspace-ui.ts` mescolava labels di dominio e stringhe visuali;
- `WorkspaceCaseCard.tsx` dipendeva ancora dal dialetto `/oggi` e da shell bespoke;
- `WorkspaceDetailPanel.tsx` portava ancora palette finance hardcoded e costruzione locale di shell/pill/box.

Questo microstep non ridisegna pagine.
Rende piu' netto il confine tra semantica business e consumo del visual layer condiviso.

## Decision

La separazione minima scelta e':

1. `frontend/src/components/workspace/workspace-ui.ts`
   - solo semantica dominio e formatter:
     - labels bucket / severity / case kind
     - formatter date/importi
     - copy business (`getCaseDueLabel`, `getCaseImpactLine`, `getFinanceSummary`)
2. `frontend/src/components/workspace/workspace-visuals.ts`
   - adapter leggero per il workspace:
     - tone mapping per bucket / severity / case kind
     - shell helpers sopra `surface-role`
     - chip helpers sopra `surface-role`
3. componenti shared
   - `WorkspaceCaseCard.tsx`
   - `WorkspaceDetailPanel.tsx`
   consumano il layer shared via `workspace-visuals.ts` invece di hex/gradienti/local shells.

## What Changed

- `workspace-ui.ts`
  - rimossi i tone string e i token finance bespoke
  - aggiunti helper di label puri (`getWorkspaceCaseKindLabel`, `getWorkspaceSeverityLabel`, `getFinanceAmountLabel`)
- `workspace-visuals.ts`
  - nuovo file con visual mapping workspace sopra `surface-role`
  - nessuna semantica business dentro il layer visuale
- `WorkspaceCaseCard.tsx`
  - rimosso il coupling con `oggi-lift` / `oggi-glow-*`
  - rimosse le shell inline `oklch()` / gradient
  - CTA e shell ora consumano surface/chip shared
- `WorkspaceDetailPanel.tsx`
  - rimossi token finance hardcoded e palette hex locali
  - header, action panel, section box e chip ora consumano il layer shared
  - i bottoni tornano sulle primitive `Button`

## Outcome

- il workspace shared non dipende piu' dal CSS locale di `/oggi`
- `workspace-ui.ts` non e' piu' un ibrido dominio+look
- il consumo di `surface-role` diventa il percorso naturale per card e dossier workspace
- il numero di colori/gradienti locali nei file toccati scende a zero

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/workspace-ui.ts" "src/components/workspace/workspace-visuals.ts" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- grep mirato su `#|oklch\\(|linear-gradient|bg-\\[linear-gradient|shadow-\\[|border-\\[#|text-\\[#|bg-\\[#` nei 4 file toccati
- `git diff --check`

## Residual Risks

- `OggiQueue.tsx` resta ancora un piccolo punto di drift locale, separato da questo microstep
- `workspace-visuals.ts` e' un adapter leggero ma nuovo: va tenuto sobrio e non deve riassorbire copy o logica business
- il visual grouping per `case kind` usa ora un set piu' compatto di toni condivisi, quindi alcune sfumature cromatiche storiche dei finance case vengono semplificate intenzionalmente
