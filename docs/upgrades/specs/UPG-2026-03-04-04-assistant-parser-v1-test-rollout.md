# UPG-2026-03-04-04 - Assistant Test, QA, Rollout Plan (V1)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: QA / Rollout
- Priority: high
- Target release: test_react

## Goal

Definire processo metodico di validazione e rilascio per introdurre assistant parser senza regressioni sui flussi core CRM.

## Test Strategy

### 1) Unit Tests (Parser Engine)

Suite suggerita:

- `tests/test_assistant_normalizer.py`
- `tests/test_assistant_intent_classifier.py`
- `tests/test_assistant_entity_resolution.py`
- `tests/test_assistant_confidence.py`
- `tests/test_assistant_ambiguity.py`

Copertura minima:

- 90% su package parser.

### 2) Integration Tests (API Assistant)

Suite suggerita:

- `tests/test_assistant_parse_api.py`
- `tests/test_assistant_commit_api.py`
- `tests/test_assistant_security_guards.py`

Casi:

- happy path per ogni intent V1;
- parse senza side effects;
- commit con ownership fail -> 404/422 coerente;
- conflitti dominio propagati in modo corretto.

### 3) Contract Tests (FE/BE)

- Verifica type sync `frontend/src/types/api.ts`.
- Snapshot JSON parse/commit responses.
- Verifica enum `domain`/`action` allineati.

### 4) Manual QA Scenarios

Checklist minima:

- agenda: crea evento con data relativa e ora;
- cassa: registra uscita con metodo pagamento;
- misurazione: inserisci 2 metriche in frase unica;
- anamnesi: aggiorna campo con cliente attivo;
- workout log: registra sessione completata;
- ambiguita': due clienti omonimi.

## Gold Corpus and Regression

File consigliato:

- `tests/fixtures/assistant_gold_corpus.json`

Schema:

- `input_text`
- `expected_operations`
- `expected_status`
- `expected_domain_action`

Target iniziale:

- 300 frasi curate;
- regressione eseguita ad ogni PR assistant.

## Quality Gates

- parser unit: pass al 100%.
- integration assistant: pass al 100%.
- nessun test esistente regressivo nel dominio finanziario/agenda.
- frontend lint/typecheck sui file toccati.

## Rollout Plan

### Phase 0 - Documentation + Feature Flag

- introdurre flag: `assistant_v1_enabled=false`.
- nessun impatto utente.

### Phase 1 - Shadow Parse (No Commit)

- flag parse-only.
- raccogli metriche parse latency + ambiguity rate.
- durata consigliata: 5-7 giorni su ambiente test.

### Phase 2 - Limited Commit Domains

- abilita commit solo per:
  - `agenda.create_event`
  - `movement.create_manual`
  - `measurement.create`
- monitor error rate per dominio.

### Phase 3 - Full V1 Commit

- abilita tutti intent V1.
- mantieni guardrail su delete non assistito.

## Monitoring KPIs

- parse latency p95/p99.
- parse success rate.
- commit success rate.
- ambiguity rate.
- user correction rate (quante volte modifica preview prima di commit).

Soglie di allerta iniziali:

- parse p95 > 120ms
- commit error rate > 5%
- ambiguity rate > 35% su intent semplici

## Incident Playbook

In caso regressione:

1. disabilita `assistant_v1_enabled`;
2. conserva log con `correlation_id`;
3. analizza categoria errore (classifier/entity/slot/domain);
4. patch parser + aggiungi caso al corpus gold;
5. riattiva gradualmente.

## Rollback

- rollback immediato: feature flag OFF.
- rollback completo: revert commit assistant router/service/UI.
- nessuna migrazione distruttiva prevista per V1.
