# Multi-Agent Workboard

Tabella operativa condivisa tra agenti AI.
Aggiornare prima di iniziare e alla chiusura di ogni task.

## Active

| Work ID | Owner | Branch | Scope | Locked files | Status | Started (UTC) | Updated (UTC) | Handoff / Notes |
|---|---|---|---|---|---|---|---|---|
| AGT-2026-03-04-06 | Codex | `codex_01` | UPG-2026-03-04-06 S1.1 licensing core backend + test | `api/services/license.py`, `tests/test_license_service.py`, `docs/upgrades/specs/UPG-2026-03-04-06-launch-market-readiness-roadmap.md`, `docs/upgrades/UPGRADE_LOG.md`, `docs/ai-sync/WORKBOARD.md` | in_progress | 2026-03-04 16:45 | 2026-03-04 16:53 | S0.1 chiuso (commit/push). S1.1 implementato e validato, pronto commit intermedio |

## Completed

| Work ID | Owner | Branch | Scope | Commit | Checks | Closed (UTC) | Notes |
|---|---|---|---|---|---|---|---|
| AGT-2026-03-03-08 | Claude Code | `codex_01` | Riallineamento Safety Engine — 80 pattern rules, 0 condizioni morte, severity avoid>modify>caution | `43e5010` | check-all.sh green, verify_qa_clinical 150 PASS 0 FAIL | 2026-03-03 | populate_conditions.py + safety_engine.py + RiskBodyMap.tsx + seed/verify QA |
| AGT-2026-03-03-11 | Claude Code | `codex_01` | Smart Programming Engine tuning 3 round: language mismatch, accessori 2-pass affinita', credito diluted, safety actionable, naming PPL | `97ab0a1, 82bf14f, 77e9961` | check-all.sh green | 2026-03-03 | smart-programming.ts + SmartAnalysisPanel.tsx |
| AGT-2026-03-03-06 | Codex | `codex_01` | Protezione Cassa + fix flusso spese fisse (reale vs previsto) | `54aa785, 9477fc0, 9735b29, 7739d8e` | check-all.sh green | 2026-03-03 | UPG-2026-03-03-06 + UPG-2026-03-03-07 |
| AGT-2026-03-04-01 | Claude Code | `codex_01` | Dual-DB architecture + Backup v2.0 bank-grade (5 pilastri) + restore fix WAL | `818e602` | check-all.sh green, test dev+prod PASS | 2026-03-04 | 14 file: database.py, config.py, backup.py, exercises.py, safety_engine.py, measurements.py, goals.py, main.py, types/api.ts, useBackup.ts, impostazioni/page.tsx |
| AGT-2026-03-04-02 | Codex | `codex_01` | Export clinico schede: file scaricabile HTML->PDF con logo cliente + foto esercizi embedded, mantenendo anteprima separata | `d49b3d0` | eslint frontend file toccati | 2026-03-04 | ExportButtons + WorkoutPreview + export-workout-pdf + persistenza logo trainer |
| AGT-2026-03-04-03 | Codex | `codex_01` | Hardening stampa clinico: paginazione A4, colori print, riduzione densita foto/padding per meno pagine | `2cf8cd4, a502f71` | `npm --prefix frontend run lint -- "src/lib/export-workout-pdf.ts"` | 2026-03-04 | Fix page-break blocchi + compattazione proporzioni media |

## Quick rules

1. `Locked files` deve riflettere i file realmente in editing.
2. Se la task si blocca, usare stato `blocked` + nota chiara.
3. Alla chiusura, spostare la riga da `Active` a `Completed`.
