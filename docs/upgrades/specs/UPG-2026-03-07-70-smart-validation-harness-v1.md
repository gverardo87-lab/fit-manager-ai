# UPG-70 — Validation Harness v1

**Data**: 2026-03-07
**Stato**: DONE
**Dipendenze**: UPG-60 (validation matrix spec), UPG-64 (runtime translation plan), UPG-69 (demand layer)

---

## Obiettivo

Implementare il layer `validation/` che definisce i 6 benchmark cases della
Validation Matrix v1 e i check functions per verificare il plan-package output.

Questo layer separa:
- `catalog` -> cosa testare (casi, fixture, aspettative)
- `contracts` -> come verificare (invariant, snapshot, tolerance)

## Architettura

```
validation/
  __init__.py              — re-export pubblico
  validation_catalog.py    — 6 benchmark (VM-001..006) + 5 client fixtures + 6 request fixtures
  validation_contracts.py  — 20 check functions + runner + warning policy
```

## File creati

| File | LOC | Responsabilita' |
|------|-----|-----------------|
| `validation_catalog.py` | ~275 | ValidationCase, ClientFixture, RequestFixture, ScoreBand, WarningPolicy |
| `validation_contracts.py` | ~400 | Invariant (7), Snapshot (7), Tolerance (8), Warning policy, runner |
| `__init__.py` | ~40 | Re-export |

## Dettaglio

### 6 Benchmark Cases

| Case | Protocol | Client | Split | Score >= | Focus |
|------|----------|--------|-------|----------|-------|
| VM-001 | PRT-001 | CFG-A (beginner) | full_body | 70 | Volume low_mav, no advanced |
| VM-002 | PRT-002 | CFG-A (beginner) | full_body | 72 | Full body ABC, recovery overlap |
| VM-003 | PRT-003 | CFG-C (intermediate) | upper_lower | 78 | Push/pull ratio, mid/high_mav |
| VM-004 | PRT-004 | CFG-D (performance) | upper_lower | 78 | Strength bias, compound priority |
| VM-005 | PRT-005 | CFG-E (advanced) | push_pull_legs | 80 | High volume controlled |
| VM-006 | PRT-006 | CFG-B (clinical) | full_body | 75 | Low-skill, zero ballistic, clinical overlay |

### 5 Client Fixtures (CFG-A..E)

- **CFG-A**: Minimal beginner (legacy anamnesi, nessuna specializzazione)
- **CFG-B**: Beginner clinical low-skill (spalla/lombare sensitive)
- **CFG-C**: Intermediate general (buona tolleranza, no vincoli clinical)
- **CFG-D**: Intermediate performance (forza relativa, readiness alta)
- **CFG-E**: Advanced hypertrophy (alta tolleranza volume)

### 3 Livelli di Check

**Invariant (7 check)** — hard gate, non possono fallire:
- `protocol_selection_correct`: protocollo selezionato = atteso
- `split_family_correct`: split coerente col protocollo
- `no_advanced_draft_exercise`: no esercizi avanzati in profili beginner
- `no_ceiling_exceeded`: demand vector sotto ceiling protocollo
- `no_hard_constraint_fail`: zero hard fail nel constraint report
- `no_ballistic_impact_draft`: zero ballistic/impact in clinical
- `demand_shoulder_lumbar_contained`: costo spalla/lombare nel ceiling

**Snapshot (7 check)** — contratti comportamentali stabili:
- `session_count_matches_frequenza`: numero sessioni = frequenza
- `session_roles_full_body/upper_lower`: ruoli sessione coerenti
- `pattern_exposure_balanced`: pattern principali rappresentati
- `compound_priority_high`: compound prima nelle sessioni (forza)
- `advanced_suitability_allowed`: profilo avanzato non gate-bloccato
- `clinical_overlay_dominant`: mode clinical attivo

**Tolerance (8 check)** — ammessi entro range dichiarato:
- `score_above_band`: score composito >= minimo protocollo
- `push_pull_ratio_in_band`: ratio 0.6..1.5
- `volume_in_low_mav/mid_high_mav/high_controlled/conservative`: volume per fascia
- `recovery_overlap_below_threshold`: max 2 recovery warnings
- `strength_bias_present`: >= 30% slot con rep <= 6 (forza)

### Warning Policy

Per ogni caso: `required`, `allowed`, `forbidden` warnings.
Il runner verifica che i required siano presenti e i forbidden assenti.

### Runner

`run_validation_case(case, package)` → `ValidationReport`:
- Esegue tutti i check dichiarati nel caso
- Produce `overall_pass`, `hard_fail_count`, `soft_fail_count`
- `run_full_matrix(packages)` esegue tutti i 6 casi

### Smoke Test

```
VM-001 (PRT-001 beginner 3x):
  INV: 5/5 pass
  SNP: 2/2 pass
  TOL: 2/2 pass
  WRN: 3/3 pass (forbidden assenti)
  overall_pass: True
```

## Note

- I check usano il `demand/` layer per verificare ceiling (no_ceiling_exceeded)
- Il harness e' read-only: non modifica il flusso di generazione
- Ogni check produce `failure_class` per classificazione regressione
- I check `skip` per check non implementati o senza dati

## Fonti

NSCA-2016, ACSM-2009, Schoenfeld-2017 (UPG-60 sezione 17).
