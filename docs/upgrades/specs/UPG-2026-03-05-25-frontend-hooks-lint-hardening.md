# UPG-2026-03-05-25 - Frontend Hooks Lint Hardening (Agenda + Unsaved Changes)

## Metadata

- Upgrade ID: UPG-2026-03-05-25
- Date: 2026-03-05
- Owner: Codex
- Area: Frontend (Agenda + Hooks)
- Priority: medium
- Target release: codex_02

## Problem

Lint su file critici frontend segnalava 2 errori bloccanti React Hooks:

- `setState` sincrono dentro `useEffect` in `agenda/page.tsx` (rischio cascading renders);
- update di `ref.current` durante render in `useUnsavedChanges.ts` (pattern non conforme).

In aggiunta erano presenti warning `exhaustive-deps` legati a `events` non stabilizzato.

## Desired Outcome

Portare i file critici in stato lint-clean senza modificare la logica business di agenda o protezione draft.

## Scope

- In scope:
  - bootstrap deep-link agenda tramite stato iniziale (no setState dentro effect);
  - pulizia URL deep-link post-bootstrap;
  - stabilizzazione riferimento `events` con `useMemo`;
  - sync di `dirtyRef` dentro `useEffect` e autosave draft con dipendenze esplicite.
- Out of scope:
  - cambi API/backend;
  - redesign UX agenda;
  - modifica semantica del flusso di salvataggio eventi.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/agenda/page.tsx`
  - `frontend/src/hooks/useUnsavedChanges.ts`
  - `docs/upgrades/specs/UPG-2026-03-05-25-frontend-hooks-lint-hardening.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend` + `docs`
- Invarianti da preservare:
  - deep-link `?newEvent=1&clientId=X` continua ad aprire sheet con cliente predefinito;
  - protezione `beforeunload` su dirty state invariata;
  - auto-save draft continua a dipendere da `dirty + draftKey + draftData`.

## Acceptance Criteria

- Technical:
  - lint targeted passa sui file toccati senza errori.
- Functional:
  - comportamento agenda e hook resta equivalente lato utente.

## Test Plan

- `npm --prefix frontend run lint -- "src/app/(dashboard)/agenda/page.tsx" "src/hooks/useUnsavedChanges.ts"`

## Risks and Mitigation

- Risk 1: parsing deep-link in bootstrap iniziale potrebbe divergere su edge-case URL.
- Mitigation 1: parsing limitato a `newEvent`/`clientId` e fallback safe (`undefined`).

## Rollback Plan

- Revert dei due file frontend al commit precedente se emergono regressioni su apertura sheet o draft guard.
