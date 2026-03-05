# API Override - FitManager

These rules apply to work under `api/` and override generic guidance when needed.

## Focus

- Preserve data integrity and tenant isolation first.
- Keep business behavior deterministic and auditable.

## Security and Ownership

- Enforce trainer ownership checks on every business entity access.
- Preserve Deep Relational IDOR protections.
- Never trust client-provided ownership fields (`trainer_id`, related foreign keys).

## Data Integrity

- Keep multi-entity mutations atomic.
- Protect against mass assignment and silent partial writes.
- Validate domain invariants close to commit boundaries.

## Accounting and Audit

- For cash/ledger-related changes, keep semantic consistency across:
  - ledger entries
  - computed balances
  - dashboard/summary aggregates
- Critical operations must remain audit-traceable.

## API Contract Discipline

- Keep response/request schema compatibility with frontend type sync.
- If contract changes, update:
  - Pydantic/response models
  - `frontend/src/types/api.ts`
  - docs upgrade log/spec
