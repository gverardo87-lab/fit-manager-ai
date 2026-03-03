# Upgrade Log

Registro unico degli upgrade tecnici e UX.

| ID | Date | Area | Type | Impact | Risk | Branch / Commit | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| UPG-2026-03-03-01 | 2026-03-03 | Workout Builder | UX + Decision Support | Save UX migliorata + sostituzione esercizio context-aware con reason breve | Medium | `codex_01` / `df6b677` | done | Build frontend verde (`npx next build`) |
| UPG-2026-03-03-02 | 2026-03-03 | Workout Builder | Reliability + UX | Pre-save validator con issue list actionable (blocchi vuoti, dati non validi) | Medium | `codex_01` / `62e364e` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-02-builder-pre-save-validator.md` |
| UPG-2026-03-03-03 | 2026-03-03 | Workout Preview | Reliability + Testability | Estrazione KPI metrics in utility pura + test Vitest dedicati | Low | `codex_01` / `d8b7629` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-03-preview-metrics-hardening.md` |
| UPG-2026-03-03-04 | 2026-03-03 | Workout Builder | UX + Navigability | Save issue center espandibile + jump rapido al primo punto da correggere | Low | `codex_01` / _pending_ | in_progress | Spec: `docs/upgrades/specs/UPG-2026-03-03-04-save-issue-center-navigation.md` |

## Uso rapido

1. Prima della patch: aggiungi riga con stato `planned`.
2. Durante la patch: aggiorna in `in_progress` se utile.
3. A fine patch: aggiungi commit, test, note e stato `done`.
