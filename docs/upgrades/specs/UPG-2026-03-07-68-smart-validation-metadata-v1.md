# UPG-68 — Validation Metadata (Phase E, Runtime Translation Plan)

**Data**: 2026-03-07
**Fase**: Phase E di UPG-64 (Runtime Translation Plan)
**Stato**: DONE
**Dipendenze**: UPG-65 (registry scaffold), UPG-66 (constraint adapter), UPG-67 (feasibility engine)

---

## Obiettivo

Rendere ogni `plan-package` **auditabile**: dato un output, e' possibile ricostruire
esattamente quali regole, registri e motori lo hanno prodotto.

Ogni sottosistema che contribuisce al package dichiara una versione stringa.
`ValidationMetadata` le raccoglie tutte in un envelope immutabile con timestamp UTC.

## Architettura

```
ValidationMetadata.build(protocol_id, constraint_profile_id, validation_case_ids)
    |
    +-- PROTOCOL_REGISTRY_VERSION   (da protocol_registry.py)
    +-- CONSTRAINT_ENGINE_VERSION   (da constraint_engine.py)
    +-- EVIDENCE_REGISTRY_VERSION   (da evidence_types.py)
    +-- FEASIBILITY_ENGINE_VERSION  (da feasibility_engine.py)
    +-- validation_case_refs        (da protocol.validation_case_ids)
    +-- generated_at                (UTC ISO 8601, seconds precision)
```

## File modificati

| File | Modifica |
|------|----------|
| `constraints/constraint_engine.py` | Aggiunta costante `CONSTRAINT_ENGINE_VERSION` |
| `registry/evidence_types.py` | Aggiunta costante `EVIDENCE_REGISTRY_VERSION` |
| `runtime/feasibility_engine.py` | Aggiunta costante `FEASIBILITY_ENGINE_VERSION` |
| `runtime/validation_metadata.py` | **NUOVO** — dataclass `ValidationMetadata` + factory `build()` |
| `api/schemas/training_science.py` | Aggiunto `TSValidationMetadata` + campo `validation` in `TSPlanPackage` |
| `runtime/plan_package_service.py` | Costruzione `validation` via `ValidationMetadata.build().__dict__` |
| `frontend/src/types/api.ts` | Mirror `TSValidationMetadata` + campo `validation` in `TSPlanPackage` |

## Dettaglio implementazione

### validation_metadata.py (~50 LOC)

- `@dataclass(frozen=True)` — immutabile
- `build()` static factory — raccoglie le 4 costanti di versione + timestamp UTC
- `validation_case_refs` come `tuple[str, ...]` (coercito a `list` da Pydantic nel transport)
- Bridge pattern: `**ValidationMetadata.build().__dict__` converte dataclass → kwargs per Pydantic

### Costanti di versione

| Sottosistema | Costante | Valore |
|-------------|----------|--------|
| Protocol Registry | `PROTOCOL_REGISTRY_VERSION` | `smart-protocol-registry-v1` |
| Constraint Engine | `CONSTRAINT_ENGINE_VERSION` | `smart-constraint-v1` |
| Evidence Registry | `EVIDENCE_REGISTRY_VERSION` | `smart-evidence-v1` |
| Feasibility Engine | `FEASIBILITY_ENGINE_VERSION` | `smart-feasibility-v1` |

### Schema Pydantic (TSValidationMetadata)

8 campi con validazione Field:
- `protocol_id`, `constraint_profile_id`: max 80 char
- 4 version string: max 50 char
- `validation_case_refs`: `list[str]`
- `generated_at`: ISO 8601 string, max 30 char

## Note

- `PROTOCOL_REGISTRY_VERSION` esisteva gia' in UPG-65 (scaffold)
- Le costanti sono posizionate DOPO gli import per rispettare ruff E402
- La Phase E e' read-only: non modifica il flusso di generazione,
  aggiunge solo metadata di tracciabilita'
