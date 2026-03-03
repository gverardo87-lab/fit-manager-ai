# Upgrade Log

Registro unico degli upgrade tecnici e UX.

| ID | Date | Area | Type | Impact | Risk | Branch / Commit | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| UPG-2026-03-03-01 | 2026-03-03 | Workout Builder | UX + Decision Support | Save UX migliorata + sostituzione esercizio context-aware con reason breve | Medium | `codex_01` / `df6b677` | done | Build frontend verde (`npx next build`) |
| UPG-2026-03-03-02 | 2026-03-03 | Workout Builder | Reliability + UX | Pre-save validator con issue list actionable (blocchi vuoti, dati non validi) | Medium | `codex_01` / `62e364e` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-02-builder-pre-save-validator.md` |
| UPG-2026-03-03-03 | 2026-03-03 | Workout Preview | Reliability + Testability | Estrazione KPI metrics in utility pura + test Vitest dedicati | Low | `codex_01` / `d8b7629` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-03-preview-metrics-hardening.md` |
| UPG-2026-03-03-04 | 2026-03-03 | Workout Builder | UX + Navigability | Save issue center espandibile + jump rapido al primo punto da correggere | Low | `codex_01` / `7533f61` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-04-save-issue-center-navigation.md` |
| UPG-2026-03-03-05 | 2026-03-03 | Process | Governance | Protocollo condiviso multi-agente + workboard centralizzato | Low | `codex_01` / _pending_ | in_progress | Spec: `docs/upgrades/specs/UPG-2026-03-03-05-multi-agent-alignment-protocol.md` |
| UPG-2026-03-03-06 | 2026-03-03 | Cassa | Reliability + UX | Protezione cassa (saldo reale vs previsto) + hardening spese ricorrenti (cleanup ledger opzionale) | High | `codex_01` / `54aa785, 9477fc0, 9735b29, 7739d8e` | done | Spec: `docs/upgrades/specs/UPG-2026-03-03-06-cash-protection-and-recurring-hardening.md` |
| UPG-2026-03-03-07 | 2026-03-03 | Cassa | Accounting Integrity | Chiusura spese fisse rettificabile/idempotente + netting storni su KPI/grafico + regressioni dedicate | High | `codex_01` / `477b035` | done | Test: `tests/test_sync_recurring.py` + `tests/test_soft_delete_integrity.py` |
| UPG-2026-03-03-08 | 2026-03-03 | Safety Engine | Clinical Accuracy | Riallineamento severita' clinica: 80 pattern rules (da 19), 0 condizioni morte (da 10), gerarchia avoid>modify>caution, QA 150 check | High | `codex_01` / `43e5010` | done | Script: `seed_qa_clinical.py` + `verify_qa_clinical.py`. Mapping: ~3600 (da ~1956), avoid 12%, modify 45%, caution 43% |
| UPG-2026-03-03-09 | 2026-03-03 | Cassa | Auditability + UX | Registro modifiche cassa consultabile con filtri, timeline, diff before/after, correlation id e link contestuali | High | `codex_01` / `770b308, f927e8d` | done | Test: `tests/test_cash_audit_log.py` |
| UPG-2026-03-03-10 | 2026-03-03 | Cassa | Navigability + Integrity | Deep-link audit verso cassa affidabile: focus movimento, range data, gestione same-route senza reload | High | `codex_01` / `76743bb, 42bd5bb` | done | Verifica: `venv\\Scripts\\python.exe -m pytest -q tests/test_cash_audit_log.py` + `npm --prefix frontend run lint -- src/components/movements/CashAuditSheet.tsx 'src/app/(dashboard)/cassa/page.tsx'` |

## Uso rapido

1. Prima della patch: aggiungi riga con stato `planned`.
2. Durante la patch: aggiorna in `in_progress` se utile.
3. A fine patch: aggiungi commit, test, note e stato `done`.
