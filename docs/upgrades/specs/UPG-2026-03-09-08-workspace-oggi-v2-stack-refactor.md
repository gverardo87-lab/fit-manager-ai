# UPG-2026-03-09-08 - Workspace Oggi v2 Stack Refactor

## Metadata

- Upgrade ID: `UPG-2026-03-09-08`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace Frontend + Information Architecture + CRM UX`
- Priority: `high`
- Target release: `codex_02`

> Historical implementation note: this v2 stack refactor is not active layout guidance for `/oggi`.
> Keep it only as history. For new design work, start from current route reality plus the active workspace skills.

## Problem

Il primo shell frontend di `Oggi` introdotto in `UPG-2026-03-09-07` era funzionale ma concettualmente ancora troppo vicino alla dashboard:

- troppi centri di gravita contemporanei;
- focus hero separato dalla queue;
- agenda ancora troppo prominente;
- sensazione di "seconda dashboard" invece che di collega operativo.

Questo generava conflitto UX con la dashboard esistente, proprio nel punto piu sensibile del workspace.

## Desired Outcome

Rifondare `/oggi` senza toccare la dashboard:

- header minimo;
- stack operativo come centro assoluto della pagina;
- agenda ridotta a supporto leggero;
- detail panel sticky come chiarificatore;
- linguaggio piu vicino a un collega operativo e meno a una board informativa.

## Scope

- In scope:
  - refactor della route `/oggi`;
  - semplificazione dei componenti `WorkspaceCaseCard`, `WorkspaceAgendaPanel`, `WorkspaceDetailPanel`;
  - nuova grammatica `stack -> detail`;
  - microcopy operativo e deterministico.
- Out of scope:
  - modifica dashboard `/`;
  - cutover home post-login;
  - mutation workspace;
  - persistenza URL-state per bucket/case;
  - shell dei workspace `Onboarding`, `Programmi`, `Rinnovi & Incassi`.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
  - `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
  - `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
  - `frontend/src/components/workspace/workspace-ui.ts`
  - `docs/upgrades/specs/UPG-2026-03-09-08-workspace-oggi-v2-stack-refactor.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend` | `docs`
- Invarianti da preservare:
  - dashboard invariata;
  - nessuna esposizione finance completa in `Oggi`;
  - nessuna nuova mutation;
  - consumo reale delle API workspace gia introdotte.

## What Changed

- `Oggi` e stato rifondato da layout multi-focus a layout `stack + detail`
- rimossi i blocchi che competevano con la queue:
  - hero focus separato
  - griglia KPI invasiva
  - agenda come pannello principale
- introdotti:
  - header minimale con brief deterministico
  - 3 pill compatte: `Adesso`, `Oggi`, `Puo aspettare`
  - stack operativo con 3 sezioni:
    - `Adesso`
    - `Oggi`
    - `Puo aspettare` collapsible
  - detail panel sticky come spiegazione del caso selezionato
- `WorkspaceCaseCard` ora usa una grammatica piu secca:
  - titolo
  - reason line
  - impact line
  - CTA primaria
  - dettaglio
- `WorkspaceAgendaPanel` ora e una strip compatta dei prossimi slot, non un modulo dominante
- `WorkspaceDetailPanel` ora apre da:
  - azione consigliata
  - perche ora
  - contesto collegato
  - timeline sintetica

## Acceptance Criteria

- Funzionale:
  - `/oggi` continua a consumare `today`, `cases` e `cases/{case_id}`;
  - il primo caso utile della queue guida davvero la pagina;
  - il detail panel si aggiorna sulla selezione nello stack.
- UX:
  - la queue e il vero centro visivo;
  - l'agenda non compete piu con la coda operativa;
  - la pagina non comunica piu "seconda dashboard".
- Sicurezza/privacy:
  - nessun importo completo in `Oggi`;
  - nessuna nuova superficie write-capable.

## Test Plan

- Frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/WorkspaceAgendaPanel.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/components/workspace/workspace-ui.ts"`

## Verification Outcome

- lint frontend sui file toccati: `PASS`
- nessun test runtime/UI automatico eseguito in questo microstep

## Risks and Mitigation

- Rischio 1: `Oggi` resta ancora una route separata, quindi l'adozione reale va verificata.
  - Mitigazione 1: refactor concentrato su identita propria, senza toccare la dashboard.
- Rischio 2: manca ancora memoria locale tipo `snooze/seen`.
  - Mitigazione 2: il nuovo layout prepara bene quel layer senza appesantire il primo shell.
- Rischio 3: `Puo aspettare` accorpa per ora i bucket futuri senza piu distinzione fine.
  - Mitigazione 3: accettato per ridurre il rumore cognitivo della prima vista.

## Rollback Plan

- revert del solo refactor frontend di `/oggi` e componenti workspace;
- il shell v1 e la dashboard restano recuperabili senza toccare API o dati.

## Notes

- Questo microstep corregge il conflitto concettuale iniziale: `Oggi` non deve vincere per quantita di moduli, ma per chiarezza decisionale.
- Prossimo step consigliato:
  - introdurre `brief` piu intelligente e memoria locale (`seen`, `snoozed`, `managed externally`) senza LLM.
