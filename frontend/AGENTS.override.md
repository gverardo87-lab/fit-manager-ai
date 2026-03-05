# Frontend Override - FitManager

These rules apply to work under `frontend/` and override generic guidance when needed.

## Focus

- Deliver fast, clinically useful UX with predictable behavior.
- Prioritize reliability of state transitions over visual embellishments.

## Mandatory Checks

For any non-trivial frontend patch:

- run lint on touched files;
- verify loading, error, and empty states;
- verify React Query invalidation symmetry for create/update/delete inverse paths;
- verify type alignment with `src/types/api.ts`.

## State and Data Integrity

- Avoid local state duplication when server state already exists in React Query.
- Keep URL/state synchronization stable for deep links and back navigation.
- Do not expose sensitive financial data in client-facing default surfaces.

## UI/UX Constraints

- Preserve existing design language unless the task explicitly asks for redesign.
- Keep interactions responsive on desktop and mobile.
- Prefer incremental UI changes over large rewrites.

## Dashboard-Specific Guardrail

- Dashboard is privacy-first and client-safe.
- Financial metrics belong to dedicated finance views (`/cassa`) or explicitly private contexts.
