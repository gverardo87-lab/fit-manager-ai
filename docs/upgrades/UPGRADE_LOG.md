# Upgrade Log

Registro unico degli upgrade tecnici e UX.

| ID | Date | Area | Type | Impact | Risk | Branch / Commit | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| UPG-2026-03-03-01 | 2026-03-03 | Workout Builder | UX + Decision Support | Save UX migliorata + sostituzione esercizio context-aware con reason breve | Medium | `codex_01` / `df6b677` | done | Build frontend verde (`npx next build`) |
| UPG-2026-03-03-02 | 2026-03-03 | Workout Builder | Reliability + UX | Pre-save validator con issue list actionable (blocchi vuoti, dati non validi) | Medium | `codex_01` / _pending_ | planned | Spec: `docs/upgrades/specs/UPG-2026-03-03-02-builder-pre-save-validator.md` |

## Uso rapido

1. Prima della patch: aggiungi riga con stato `planned`.
2. Durante la patch: aggiorna in `in_progress` se utile.
3. A fine patch: aggiungi commit, test, note e stato `done`.
