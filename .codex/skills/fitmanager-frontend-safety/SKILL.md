---
name: fitmanager-frontend-safety
description: Use when editing Next.js frontend code in FitManager. Enforces state integrity, query invalidation quality, privacy-safe UI defaults, and reliable UX fallback states.
---

# FitManager Frontend Safety

## When To Use

Use this skill for changes under `frontend/src/`, especially:

- App Router pages/layouts
- domain components
- React Query hooks
- navigation/state behavior

## Core Guardrails

- keep loading/error/empty states explicit;
- keep API contract aligned with `frontend/src/types/api.ts`;
- keep query invalidation symmetric across inverse operations;
- avoid exposing financial-sensitive data in default client-facing views.

## Checklist Before Merge

1. Data/state:
   - no duplicated local/server state
   - URL-state sync remains stable
2. UX:
   - no broken responsive behavior
   - no inaccessible critical action
3. Safety:
   - no sensitive data leak in overview surfaces
4. Quality:
   - lint passes on touched files

## Recommended Commands

- `npm --prefix frontend run lint -- "<touched-file>"`
- optional targeted tests in `frontend/src/__tests__/` for high-risk behavior changes

## Red Flags

- optimistic UI without rollback path
- mutation without required invalidations
- quick-fix that bypasses existing design/system patterns
