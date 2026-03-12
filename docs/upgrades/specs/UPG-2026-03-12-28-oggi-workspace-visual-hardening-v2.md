# UPG-2026-03-12-28 - Oggi Workspace Visual Hardening v2

## Metadata

- Upgrade ID: `UPG-2026-03-12-28`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace System + Oggi Local Components`
- Priority: `medium`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo `UPG-2026-03-12-27`, i drift piu' evidenti nel workspace locale di `/oggi` erano rimasti in due componenti:

- `frontend/src/components/workspace/OggiQueue.tsx`
- `frontend/src/components/workspace/OggiClientContextPanel.tsx`

Entrambi continuavano a costruirsi shell, chip e toni in modo troppo locale, riducendo il valore del layer condiviso `surface-role` + `workspace-visuals`.

## Decision

Hardening architetturale minimo, non redesign:

- `OggiQueue` e `OggiClientContextPanel` restano responsabili solo della composizione locale della route;
- shell, chip e tone passano il piu' possibile da `surface-role.ts` e `workspace-visuals.ts`;
- `workspace-visuals.ts` riceve solo due mapping visuali aggiuntivi (`bucket marker` e `bucket rail`) coerenti con il suo ruolo di adapter leggero;
- nessuna nuova semantica business entra nel layer visuale.

## Changes

### `workspace-visuals.ts`

- aggiunti `getWorkspaceBucketMarkerClass(...)`
- aggiunti `getWorkspaceBucketRailClass(...)`

### `OggiQueue.tsx`

- rimossa la shell bespoke con `style={{...}}` e `oggi-glow-neutral`
- header, empty state e tab view riallineati ai surface/chip shared
- lane marker e rail bucket-driven passano dal visual adapter, non da branch locali inline

### `OggiClientContextPanel.tsx`

- root shell riallineata a `getWorkspacePanelClassName(...)`
- card stat, note, alert, checklist e hint passano da `surfaceRoleClassName(...)` / `getWorkspaceSectionClassName(...)`
- chip header e CTA finali passano da `getWorkspaceChipClassName(...)` / `Button`
- il mapping clinico locale resta locale solo come semantica (`health check status -> tone/icon`)

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/OggiQueue.tsx" "src/components/workspace/OggiClientContextPanel.tsx" "src/components/workspace/workspace-visuals.ts"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `rg -n "oklch\\(|linear-gradient|#[0-9A-Fa-f]{3,8}|shadow-\\[|bg-\\[linear-gradient|border-\\[#|text-\\[#|bg-\\[#|oggi-" frontend/src/components/workspace/OggiQueue.tsx frontend/src/components/workspace/OggiClientContextPanel.tsx frontend/src/components/workspace/workspace-visuals.ts`
- `git diff --check`

## Residual Risks

- `OggiQueue.tsx` e `OggiClientContextPanel.tsx` non sono oggi nel render path diretto di `frontend/src/app/(dashboard)/oggi/page.tsx`; il microstep rafforza l'architettura locale del workspace, ma non cambia la route runtime attuale.
- La semantica visuale session-prep (`health check`, `readiness`) resta locale ai componenti, ed e' corretto cosi' finche non emerge una riutilizzazione reale cross-workspace.
