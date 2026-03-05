---
name: fitmanager-api-integrity
description: Use when changing FastAPI endpoints, services, or schemas in FitManager. Enforces ownership safety, transaction integrity, auditability, and stable API contracts.
---

# FitManager API Integrity

## When To Use

Use this skill for modifications in:

- `api/routers/*.py`
- `api/services/*.py`
- request/response schemas
- mutations with side effects

## Core Guardrails

- enforce tenant ownership and Deep Relational IDOR checks;
- prevent mass assignment;
- keep multi-entity writes atomic;
- preserve auditable transitions on critical operations.

## API Contract Discipline

If API contract changes, update together:

1. backend schemas/models
2. `frontend/src/types/api.ts`
3. impacted frontend hooks/components

Do not leave contract drift.

## Verification Checklist

1. run relevant pytest subset for touched domain;
2. verify negative-path behavior (not found, forbidden, invalid input);
3. verify no silent partial-write on failure paths.

## Red Flags

- ownership inferred from client payload
- writes across entities without transaction safety
- contract change merged without frontend type update
