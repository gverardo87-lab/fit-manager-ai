# UPG-2026-03-07-39 - FitManager Collaboration Contract v1

## Metadata

- Upgrade ID: `UPG-2026-03-07-39`
- Date: 2026-03-07
- Owner: Codex
- Area: Governance + AI Workflow
- Priority: medium
- Target release: immediato, pre-filone SMART

## Problem

Il progetto ha gia' una buona baseline di governance (`AGENTS.md`, `CLAUDE.md`,
skill, workboard), ma il prossimo filone SMART richiede un livello di
preallineamento superiore:

- task lunghi e multi-layer
- rischio di conversazioni troppo libere e poco verificabili
- necessita' di distinguere brainstorming, analisi, patch e review
- necessita' di proteggere i task scientifici da ambiguita' e cambi di scope

Con il passaggio operativo a `gpt-5.4`, il punto non e' "riscrivere le skill",
ma definire un protocollo di collaborazione piu' rigoroso tra utente e agente.

## Desired Outcome

Avere un contratto operativo corto, riusabile e repo-tracked che:

- riduca ambiguita' nei task
- standardizzi input utente e output Codex
- imponga decision gate sui task architetturali
- prepari il filone SMART a un lavoro piu' scientifico, deterministico e auditabile

## Scope

- In scope:
  - nuovo documento operativo in `docs/ai-sync/`
  - sync `UPGRADE_LOG.md`
  - sync `docs/upgrades/README.md`
  - sync `docs/ai-sync/WORKBOARD.md`
- Out of scope:
  - modifiche al runtime dell'app
  - cambi a `AGENTS.md` o `CLAUDE.md`
  - nuove skill o refactor delle skill esistenti

## Impact Map

- Files/modules da toccare:
  - `docs/ai-sync/FITMANAGER_COLLABORATION_CONTRACT_V1.md`
  - `docs/upgrades/specs/UPG-2026-03-07-39-fitmanager-collaboration-contract-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `docs`
- Invarianti da preservare:
  - nessun cambio di comportamento runtime
  - rispetto della gerarchia di governo esistente
  - allineamento con il metodo microstep-first

## Acceptance Criteria

- Funzionale:
  - esiste un contratto operativo v1 chiaro e utilizzabile
  - il contratto copre mode, task brief, output atteso, decision gate, handoff
  - il contratto contiene un addendum SMART/Training Science
- UX:
  - il documento e' breve, leggibile e pronto da copiare/incollare
- Tecnico:
  - `WORKBOARD.md` tracciato
  - `UPGRADE_LOG.md` e `README.md` sincronizzati
  - nomenclatura e ID cronologicamente coerenti

## Test Plan

- Unit/Integration:
  - non applicabile, patch solo documentale
- Manual checks:
  - verifica coerenza tra contratto, spec, log e workboard
  - verifica percorsi file e ID upgrade/work ID
- Build/Lint gates:
  - non applicabile

## Risks and Mitigation

- Rischio 1:
  - il contratto diventa troppo teorico e poco usabile
- Mitigazione 1:
  - mantenere formato operativo, con template copiabili e regole brevi

- Rischio 2:
  - sovrapposizione con `AGENTS.md` e `MULTI_AGENT_SYNC.md`
- Mitigazione 2:
  - posizionare il contratto come protocollo user-Codex, non come sostituto della governance base

- Rischio 3:
  - il filone SMART venga comunque avviato senza preflight tecnico
- Mitigazione 3:
  - includere addendum SMART con invarianti e verifiche minime obbligatorie

## Rollback Plan

- Rimuovere `docs/ai-sync/FITMANAGER_COLLABORATION_CONTRACT_V1.md`
- eliminare l'entry `UPG-2026-03-07-39` dal log e dal README
- chiudere il work item come superseded o rolled back

## Notes

- Deliverable pensato per essere usato subito prima del refactor SMART/SSoT.
- Nessun impatto runtime; change set interamente documentale.
