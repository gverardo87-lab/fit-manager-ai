# UPG-69 — Demand Layer v1 (Biomechanical Cost Vector)

**Data**: 2026-03-07
**Stato**: DONE
**Dipendenze**: UPG-59 (demand vector spec), UPG-65 (registry scaffold), UPG-58 (protocol definitions)

---

## Obiettivo

Implementare il layer `demand/` che descrive il **costo biomeccanico-funzionale**
di ogni esercizio su 10 dimensioni ordinali (0..4) e dichiara **ceiling per protocollo**.

Questo layer separa:
- `pattern` → cosa allena
- `muscle contribution` → quanto stimola
- `demand vector` → quanto costa eseguirlo

## Architettura

```
demand/
  __init__.py            — re-export pubblico
  demand_types.py        — ExerciseDemandVector, DemandCeiling, DemandFamily, EvidenceClass
  demand_registry.py     — pattern defaults (18 pattern × 3 diff) + 6 protocol ceilings
  demand_policy.py       — check_demand_ceiling() → DemandPolicyResult
```

## File creati

| File | LOC | Responsabilita' |
|------|-----|-----------------|
| `demand_types.py` | ~100 | Dataclass `ExerciseDemandVector` (10 dim + metadata) + `DemandCeiling` |
| `demand_registry.py` | ~230 | 54 vettori default (18 pattern × 3 difficolta') + 6 ceiling PRT-001..006 |
| `demand_policy.py` | ~110 | `check_demand_ceiling()` puro e deterministico |
| `__init__.py` | ~25 | Re-export |

## Dettaglio

### 10 Dimensioni del Demand Vector

| Dimensione | Uso principale |
|-----------|----------------|
| `skill_demand` | Gate beginner, filtro clinical low-skill |
| `coordination_demand` | Esercizi formalmente fattibili ma troppo complessi |
| `stability_demand` | Budget recupero, clinical modes |
| `ballistic_demand` | Ceiling hard beginner/clinical |
| `impact_demand` | Protocolli low-impact |
| `axial_load_demand` | Profili lumbar-sensitive |
| `shoulder_complex_demand` | Overlay clinico spalla/cuffia |
| `lumbar_load_demand` | Costo lombare locale |
| `grip_demand` | Overlap e recovery upper pull |
| `metabolic_demand` | Budget seduta, densita' principiante |

### 8 Demand Families

`low_skill_general`, `high_skill_upper`, `ballistic_lower`, `high_axial_loading`,
`shoulder_overhead_heavy`, `lumbar_bracing_heavy`, `grip_limited`, `metabolic_dense`.

### Protocol Ceilings (PRT-001..006)

- **PRT-001** (Beginner General): skill/coord ≤2, ballistic/impact ≤1
- **PRT-002** (Intermediate General): skill/coord ≤3, tutto ≤3
- **PRT-003** (Intermediate Hypertrophy): ballistic/impact ≤1 (ipertrofia non balistico)
- **PRT-004** (Intermediate Strength): axial_load ≤4 (forza permette carico alto)
- **PRT-005** (Advanced Hypertrophy): tutto ≤4 (research_only)
- **PRT-006** (Clinical Conservative): skill/coord ≤1, ballistic/impact =0, tutto ≤2

### Policy Engine

`check_demand_ceiling(vector, ceiling)` produce:
- `DemandPolicyResult` con `overall_verdict` (pass/ceiling_exceeded/family_discouraged/family_excluded)
- `dimension_findings`: per-dimensione pass/fail
- `family_findings`: per-family discouraged/excluded
- `is_hard_fail` property per gate rapido

### Smoke Test

```
Squat beginner vs PRT-001: pass, violations=0
Squat advanced vs PRT-001: ceiling_exceeded, violations=2
Squat advanced vs PRT-006: ceiling_exceeded, violations=4
  (skill, coordination, axial_load, lumbar_load)
```

## Note

- I vettori sono *default per pattern*: il mapping per-esercizio sara' raffinato
  in un futuro Catalog Mapping pass
- Pattern complementari (warmup/stretch/mobility) non sono in `PatternMovimento` →
  usano il fallback vector conservativo
- Il layer e' read-only: non modifica il flusso di generazione attuale.
  Sara' integrato nel feasibility engine come gate aggiuntivo

## Fonti

NSCA-2016, ACSM-2009, Sahrmann-2002, Alentorn-Geli-2009 (UPG-59 sezione 15).
