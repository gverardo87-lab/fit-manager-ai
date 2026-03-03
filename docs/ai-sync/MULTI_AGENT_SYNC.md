# Multi-Agent Sync Protocol

Protocollo unico di coordinamento quando lavoriamo con piu agenti AI in parallelo
(es. Codex + Claude Code) sulla stessa codebase.

## 1. Scopo

- evitare conflitti e regressioni da editing concorrente
- mantenere handoff tracciabile tra agenti
- tenere allineati sviluppo, test e documentazione

## 2. Fonti comuni obbligatorie

Prima di iniziare una task ogni agente deve leggere:

1. `CLAUDE.md` (root)
2. `codex.md`
3. questo file (`docs/ai-sync/MULTI_AGENT_SYNC.md`)
4. `docs/ai-sync/WORKBOARD.md`

## 3. Regole operative (mandatory)

1. Claim task nel workboard prima di editare.
2. Dichiarare `Locked files` nel workboard prima di toccarli.
3. Nessun editing sugli stessi file gia lockati da altro agente senza handoff esplicito.
4. Un agente per task: evitare patch parallele sullo stesso Work ID.
5. A fine task aggiornare sempre:
   - `docs/ai-sync/WORKBOARD.md`
   - `docs/upgrades/UPGRADE_LOG.md` (se rilevante)
   - eventuale spec in `docs/upgrades/specs/`

## 4. Workflow standard

## 4.1 Start

1. Verifica branch attivo e `git status`.
2. Crea/usa un `Work ID` (es. `AGT-2026-03-03-01`).
3. Aggiungi riga in `WORKBOARD.md` con:
   - owner (Codex/Claude)
   - scope breve
   - file lockati
   - stato `in_progress`

## 4.2 During

1. Mantieni i lock aggiornati quando cambi file target.
2. Se la scope cambia, aggiorna la riga del workboard.
3. Se serve sub-handoff, usa il campo `Handoff / Notes`.

## 4.3 End

1. Esegui i check minimi richiesti dalla task.
2. Aggiorna workboard con:
   - stato `done`
   - commit hash
   - test eseguiti
   - rischi residui
3. Rilascia i lock (campo `Locked files` vuoto o `-`).

## 5. Stato task consentiti

- `planned`
- `in_progress`
- `blocked`
- `review`
- `done`

## 6. Policy conflitti

Se un agente trova file lockati su cui deve intervenire:

1. fermarsi
2. aggiornare workboard con stato `blocked`
3. chiedere riallineamento (handoff o decisione utente)

Regola: meglio una pausa di coordinamento che una merge conflict con regressioni.

## 7. Criterio di qualita handoff

Un handoff e valido solo se include:

- cosa e stato fatto
- file toccati
- test eseguiti
- cosa resta da fare
- eventuali rischi aperti
