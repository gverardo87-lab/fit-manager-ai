# Multi-Agent Sync Protocol

Protocollo operativo unico per sviluppo parallelo con piu agenti AI
(es. Codex + Claude Code) sulla stessa codebase.

## 1. Scopo

- prevenire conflitti da editing concorrente
- mantenere handoff tracciabile e riusabile
- garantire allineamento tra codice, test e documentazione

## 2. Priorita regole

Ordine di riferimento obbligatorio:
1. `AGENTS.md`
2. `CLAUDE.md` (root + layer)
3. `codex.md`
4. questo file
5. `docs/ai-sync/WORKBOARD.md`

In caso di conflitto, prevale la regola con priorita piu alta e piu restrittiva su safety/qualita.

## 3. Contratto Workboard

Ogni task deve avere un `Work ID` unico (`AGT-YYYY-MM-DD-XX`) in `WORKBOARD.md`.

Campi minimi richiesti in `Active`:
- `Work ID`
- `Owner` (`Codex` o `Claude Code`)
- `Branch`
- `Scope`
- `Status` (`in_progress`, `blocked`, `review`)
- `Locked files`
- `Started (UTC)`
- `Handoff / Notes`

Campi minimi richiesti in `Completed`:
- `Commit`
- `Checks`
- `Closed (UTC)`
- `Notes` con rischi residui o next step

## 4. Workflow standard

### 4.1 Start

1. Verifica branch attivo e `git status`.
2. Crea/riusa `Work ID`.
3. Aggiungi riga in `Active` con lock file iniziali prima del primo edit.

### 4.2 During

1. Aggiorna `Locked files` appena cambia lo scope reale.
2. Aggiorna stato (`in_progress` -> `review` o `blocked`) senza ritardi.
3. Se serve passaggio tra agenti, compila `Handoff / Notes` prima del trasferimento.

### 4.3 End

1. Esegui i check rilevanti per la scope.
2. Sposta la riga in `Completed` con commit e verifiche.
3. Rilascia lock (in `Active` non deve restare alcun file bloccato per quel Work ID).
4. Sincronizza `docs/upgrades/*` quando la patch cambia comportamento o governance.

## 5. Lock policy

- Lock granularita path file (es. `frontend/src/app/(dashboard)/guida/page.tsx`).
- Nessun edit su file lockato da altro owner senza handoff esplicito.
- Lock condiviso consentito solo su file docs di coordinamento (`WORKBOARD.md`, `UPGRADE_LOG.md`) e con update atomico.

## 6. Handoff packet minimo

Ogni handoff tra agenti deve includere:
- stato attuale della task
- file modificati e file ancora lockati
- check eseguiti con esito
- rischi aperti e prossima micro-azione consigliata

## 7. Gestione blocchi

Se un agente deve intervenire su file lockato:
1. fermarsi
2. impostare stato `blocked` su workboard
3. chiedere riallineamento (handoff o decisione utente)

Regola: meglio pausa di coordinamento che regressioni da merge conflict.
