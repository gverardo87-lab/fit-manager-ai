# UPG-2026-03-09-07 - Workspace Oggi Frontend Shell v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-07`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace Frontend + CRM UX + Navigation`
- Priority: `high`
- Target release: `codex_02`

## Problem

Dopo `UPG-2026-03-09-06`, il contratto API del workspace e completo lato read-only:

- `GET /api/workspace/today`
- `GET /api/workspace/cases`
- `GET /api/workspace/cases/{case_id}`

Ma il trainer non ha ancora una superficie frontend reale che li consumi insieme.

Questo lascia aperti tre rischi:

- il contratto API non viene validato nel flusso utente reale;
- `Oggi` resta solo un concetto documentato, non una home mentale navigabile;
- il team non puo ancora testare la densita informativa della queue, del focus case e del detail panel.

## Desired Outcome

Introdurre il primo shell frontend di `Oggi` come route dedicata e additiva:

- route `/oggi` dentro il dashboard;
- hero header con summary operativa;
- focus case che consuma davvero `today.focus_case`;
- agenda live che consuma `today.agenda`;
- coda bucketizzata che consuma `cases` lato server;
- pannello dettaglio che consuma `cases/{case_id}`;
- link esplicito in sidebar, senza ancora cambiare la home `/`.

## Scope

- In scope:
  - nuova pagina `frontend/src/app/(dashboard)/oggi/page.tsx`;
  - componenti UI dedicati per queue, agenda e detail panel;
  - wiring reale con `useWorkspaceToday()`, `useWorkspaceCases()`, `useWorkspaceCaseDetail()`;
  - navigazione sidebar verso `/oggi`;
  - loading/error/empty states espliciti.
- Out of scope:
  - cutover della home post-login da `/` a `/oggi`;
  - UI dei workspace `Onboarding`, `Programmi`, `Rinnovi & Incassi`;
  - mutation workspace (`snooze`, `mark managed`, `convert todo`);
  - persistence URL-state di bucket/case selezionato;
  - test frontend E2E o visual regression.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/workspace-ui.ts`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
  - `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
  - `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
  - `docs/upgrades/specs/UPG-2026-03-09-07-workspace-oggi-frontend-shell-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend` | `docs`
- Invarianti da preservare:
  - dashboard `/` resta invariata e privacy-safe;
  - `Oggi` usa solo il workspace `today` e non espone importi completi;
  - nessuna mutation o side effect aggiunta;
  - la nuova route deve restare leggibile su desktop/tablet/mobile senza overflow evidente.

## What Changed

- aggiunta la nuova route `frontend/src/app/(dashboard)/oggi/page.tsx`
  - header operativo con metriche `Da fare ora`, `Oggi`, `Entro 7 giorni`, `Completati oggi`
  - focus case hero collegato a `today.focus_case`
  - agenda live collegata a `today.agenda`
  - coda bucketizzata collegata a `GET /api/workspace/cases?workspace=today&bucket=*`
  - detail panel collegato a `GET /api/workspace/cases/{case_id}?workspace=today`
- introdotti componenti dedicati:
  - `WorkspaceCaseCard`
  - `WorkspaceAgendaPanel`
  - `WorkspaceDetailPanel`
  - helper visuali condivisi in `workspace-ui.ts`
- aggiunto l'accesso dalla sidebar con nuova voce `Oggi`
- mantenuto il posizionamento additivo:
  - `/oggi` e navigabile subito
  - `/` resta la dashboard classica attuale

## Acceptance Criteria

- Funzionale:
  - il trainer puo aprire `/oggi` da sidebar;
  - i bucket cambiano davvero la query `cases`;
  - la selezione di un caso aggiorna davvero il detail panel;
  - focus case e agenda usano il payload `today`, non fetch legacy separati.
- UX:
  - loading, error e empty state sono espliciti;
  - la coda operativa e il dettaglio restano leggibili anche con molti item;
  - la pagina non sembra una copia della dashboard, ma una surface operativa distinta.
- Sicurezza/privacy:
  - `Oggi` continua a vedere finance solo redatta;
  - nessun importo completo appare in questa route.

## Test Plan

- Frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/WorkspaceAgendaPanel.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/components/workspace/workspace-ui.ts" "src/components/layout/Sidebar.tsx"`

## Verification Outcome

- lint frontend sui file toccati: `PASS`
- nessun test runtime/UI automatico eseguito in questo microstep

## Risks and Mitigation

- Rischio 1: `Oggi` e ancora una route separata, non la vera home post-login.
  - Mitigazione 1: scelta intenzionale per validare il carico cognitivo prima del cutover di `/`.
- Rischio 2: la coda `today` non copre ancora `programmi`.
  - Mitigazione 2: shell limitato al perimetro realmente alimentato dalle API MVP.
- Rischio 3: stato bucket/case non persistito in URL.
  - Mitigazione 3: accettato per il primo shell; prossimo step possibile se la pagina viene adottata come home reale.

## Rollback Plan

- revert dei soli file frontend shell:
  - route `/oggi`
  - componenti `components/workspace/*`
  - link sidebar `Oggi`
- le API workspace restano intatte e riusabili.

## Notes

- Questo microstep e il primo momento in cui il workspace `Oggi` esiste come esperienza utente reale.
- Prossimo step consigliato:
  - rifinitura UX del shell con switcher workspace, persistenza selection state e possibile cutover controllato della home `/`.
