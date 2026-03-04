# UPG-2026-03-04-04 - Assistant CRM Deterministico (V1)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: Command Palette + API Assistant + CRM Core Flows
- Priority: high
- Target release: test_react

## Problem

L'app deve offrire esperienza "copilot-like" su hardware clienti non performante (CPU-only, RAM limitata), senza introdurre dipendenze AI pesanti lato runtime.

I flussi CRM principali (agenda, clienti, contratti, cassa, anamnesi/misurazioni, log allenamenti) sono gia' presenti e solidi, ma oggi richiedono navigazione manuale tra schermate e form separati.

## Desired Outcome

Un assistente testuale integrato in Command Palette che:

- interpreta frasi naturali in italiano (anche compatte) con latenza molto bassa;
- mostra una preview strutturata e verificabile prima del salvataggio;
- salva solo su conferma esplicita utente;
- preserva invarianti di sicurezza/multi-tenancy e integrita' contabile/clinica.

## Scope

- In scope:
  - Nuovo modulo Assistant deterministico lato API (`parse` + `commit`).
  - Integrazione Command Palette con preview/confirm/disambiguazione.
  - Intent V1:
    - agenda: crea evento, aggiorna stato evento;
    - clienti: crea cliente, aggiorna cliente;
    - contratti: crea contratto base;
    - cassa: crea movimento manuale;
    - anamnesi: patch campi anamnesi cliente;
    - misurazioni: crea sessione misurazione;
    - allenamento: crea workout log.
  - Matrice invalidazione React Query per ogni operazione.
  - Telemetria parser (senza PII in chiaro nei log applicativi).
  - Specifiche di test, rollout graduale, fallback.
- Out of scope:
  - LLM locale o cloud in V1.
  - Delete distruttivi via linguaggio naturale libero.
  - Creazione completa scheda allenamento multi-sessione via NL complesso.
  - Automazioni "silent write" in background.

## Impact Map

- Files/modules da toccare (implementazione successiva):
  - `api/main.py` (inclusione router assistant)
  - `api/routers/assistant.py` (nuovo)
  - `api/schemas/assistant.py` (nuovo)
  - `api/services/assistant_parser/` (nuovo package)
  - `frontend/src/components/layout/CommandPalette.tsx`
  - `frontend/src/types/api.ts`
  - eventuali hook dedicati: `frontend/src/hooks/useAssistant.ts` (nuovo)
  - test API/integrazione: `tests/test_assistant_*.py` (nuovi)
- Layer coinvolti: `api`, `frontend`, `tests`
- Invarianti da preservare:
  - trainer ownership via bouncer/deep IDOR su endpoint finali;
  - mass assignment prevention (nessun `trainer_id` da input assistant);
  - ledger integrity sui movimenti cassa;
  - human-in-the-loop: nessun write su `parse`;
  - compatibilita' con query invalidation e toasts esistenti.

## Architecture Summary

Paradigma V1:

- parser NLP deterministico, composto da:
  - normalizzazione testo;
  - intent classification rule-based;
  - entity extraction regex + dizionari;
  - entity resolution (exact + fuzzy);
  - confidence scoring + ambiguity detection;
  - output operazioni normalizzate.
- flusso a due fasi:
  - `parse` read-only;
  - `commit` esplicito e validato.

Nessun modello neurale richiesto in runtime.

## Domain Coverage V1

Mappatura intent -> endpoint target:

- `agenda.create_event` -> `POST /api/events`
- `agenda.update_event_status` -> `PUT /api/events/{event_id}`
- `client.create` -> `POST /api/clients`
- `client.update` -> `PUT /api/clients/{client_id}`
- `contract.create` -> `POST /api/contracts`
- `movement.create_manual` -> `POST /api/movements`
- `anamnesi.patch` -> `PUT /api/clients/{client_id}` (campo `anamnesi`)
- `measurement.create` -> `POST /api/clients/{client_id}/measurements`
- `workout_log.create` -> `POST /api/clients/{client_id}/workout-logs`

## Performance and Reliability Targets

- Parse latency p95 <= 80ms su dataset medio locale.
- Parse latency p99 <= 150ms.
- Zero side effect su `parse`.
- Commit atomico per singola operazione.
- In caso multi-operazione, esecuzione sequenziale con report per-item (partial success esplicito).

## Security and Data Integrity

- `parse` non accede mai in scrittura.
- `commit` passa sempre dagli endpoint esistenti (nessun bypass logiche dominio).
- Rifiuto automatico di campi sensibili non previsti.
- Tracciamento `correlation_id` per audit debugging.

## Acceptance Criteria

- Funzionale:
  - Frasi naturali comuni producono preview coerente e salvabile.
  - Ambiguita' esplicitate con suggerimenti risolutivi.
  - Commit esegue operazione giusta sul dominio giusto.
- UX:
  - Preview immediata in palette.
  - Conferma esplicita obbligatoria.
  - Errori comprensibili e azionabili.
- Tecnico:
  - Type sync FE/BE.
  - Invalidazioni query corrette per dominio.
  - Test parser + integrazione endpoint verdi.

## Test Plan

- Unit:
  - tokenizzazione/normalizzazione;
  - date parsing;
  - regex extraction;
  - confidence scoring;
  - ambiguity rules.
- Integration:
  - parse -> commit per ogni intent V1;
  - negative path (ambiguita', dati mancanti, ownership fail).
- Manual:
  - flusso completo da Command Palette con keyboard-only.
- Gates:
  - pytest target assistant;
  - lint/typecheck frontend su componenti toccati.

## Risks and Mitigation

- Rischio 1: eccessiva ambiguita' con nomi cliente simili.
- Mitigazione 1: soglia fuzzy conservativa + disambiguazione obbligatoria.

- Rischio 2: scope creep su intent avanzati.
- Mitigazione 2: freeze taxonomy V1 e backlog V2 separato.

- Rischio 3: regressioni UX Command Palette.
- Mitigazione 3: feature flag + rollout graduale shadow mode.

## Rollback Plan

- Feature flag `assistant_v1_enabled` disattivabile.
- Esclusione router assistant da `api/main.py` in hotfix.
- Revert dei file assistant + UI integration senza impattare i moduli CRM esistenti.

## Notes

- Sottospecifiche collegate:
  - `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-api-contract.md`
  - `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-intents-grammar.md`
  - `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-frontend-ux.md`
  - `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-test-rollout.md`
  - `docs/upgrades/specs/UPG-2026-03-04-04-assistant-parser-v1-implementation-plan.md`
