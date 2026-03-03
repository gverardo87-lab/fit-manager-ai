# FitManager AI Studio - Metodo Codex

Questo file definisce il metodo operativo tra te e Codex per sviluppare con standard senior, mantenendo velocita e qualita.

## 1. Gerarchia delle regole

Fonti di verita (ordine di priorita):
1. `CLAUDE.md` (root)
2. `api/CLAUDE.md`
3. `frontend/CLAUDE.md`
4. `core/CLAUDE.md`
5. `docs/ai-sync/MULTI_AGENT_SYNC.md` (coordinamento multi-agente)
6. `codex.md` (questo file)

Se c'e conflitto, prevalgono i file `CLAUDE.md`.

## 2. Obiettivo del metodo

- Consegnare feature complete, non patch parziali
- Ridurre regressioni tramite verifiche sistematiche
- Rendere ogni handoff chiaro, tracciabile e riusabile

## 3. Ciclo operativo per ogni task

1. Allineamento
- Chiarire obiettivo, vincoli, Definition of Done
- Identificare layer impattati (`api/`, `frontend/`, `core/`, `tools/`)

2. Impact Map
- Elencare file da toccare
- Elencare invarianti da preservare (sicurezza, integrita dati, UX, type sync)

3. Implementazione
- Cambi minimi ma completi
- Nessun refactor laterale non richiesto
- Aderenza ai pattern esistenti del progetto

4. Verifica
- Eseguire i controlli tecnici adeguati (vedi sezione 5)
- Controllare edge cases e regressioni plausibili

5. Handoff
- Spiegare cosa e stato fatto, file cambiati, test eseguiti, rischi residui

## 4. Invarianti non negoziabili

Backend:
- Bouncer Pattern e Deep Relational IDOR dove richiesto
- Mass assignment prevention
- Atomicita su operazioni multi-entita
- Audit trail coerente

Frontend:
- Type sync rigoroso con `frontend/src/types/api.ts`
- Invalidazione query simmetrica su operazioni inverse
- Gestione loading/error/empty state

Cross-layer:
- Niente path assoluti hardcoded
- Dati persistenti in `data/`
- Nessuna dipendenza AI obbligatoria per il core CRM

## 5. Quality Gate per tipo di modifica

Baseline (sempre):
- `bash tools/scripts/check-all.sh`

Se cambia schema DB:
- `bash tools/scripts/migrate-all.sh`
- test backend pertinenti

Se cambia logica backend:
- `pytest tests/ -v` (o subset motivato)

Se cambia logica frontend critica:
- test frontend pertinenti (se presenti)

Se cambia pipeline safety/condizioni (`condition_rules.py`, `populate_conditions.py`):
- `python -m tools.admin_scripts.populate_conditions --db both`
- `python -m tools.admin_scripts.verify_qa_clinical --lotto all` (150 check, 0 FAIL atteso)
- Severita' clinica: avoid > modify > caution (MAI invertire modify/caution)

## 6. Formato richieste consigliato

Per lavorare veloce e bene, usa questo template:

```md
Task:
Contesto:
Vincoli:
Definition of Done:
```

Parole chiave utili:
- `ANALISI` -> solo analisi, niente patch
- `IMPLEMENTA` -> patch + verifiche
- `REVIEW` -> findings prima, ordinati per severita
- `HOTFIX` -> fix minimo, test mirati

## 7. Definition of Done Codex

Una task e completata solo se:
- build/lint verdi
- type sync allineato
- invalidazioni query coerenti
- nessun rischio critico aperto non dichiarato
- handoff finale chiaro

## 8. Handoff standard

Ogni consegna finale include:
- Sintesi soluzione
- File modificati
- Test/comandi eseguiti
- Rischi residui (se presenti)
- Prossime mosse consigliate

## 9. Governance upgrade (nuovo)

Per tenere traccia degli upgrade e migliorare la sinergia nel tempo:

1. Spec pre-patch
- usare `docs/upgrades/specs/PATCH_SPEC_TEMPLATE.md`

2. Ledger unico
- registrare ogni upgrade in `docs/upgrades/UPGRADE_LOG.md`

3. Checklist operativa
- usare `docs/upgrades/checklists/DOR_DOD_CHECKLIST.md` prima e dopo la patch

4. Decisioni architetturali
- quando serve, creare ADR in `docs/adr/` partendo da `docs/adr/ADR_TEMPLATE.md`

Regola pratica:
- patch piccola: spec breve + log
- patch media/alta: spec completa + log + checklist
- decisione strutturale: aggiungere ADR

## 10. Coordinamento multi-agente

Quando lavoriamo in parallelo con piu agenti AI (es. Codex + Claude Code), il protocollo operativo comune e:

- `docs/ai-sync/MULTI_AGENT_SYNC.md` (regole e flusso)
- `docs/ai-sync/WORKBOARD.md` (stato lavori e lock file)

Regole obbligatorie:
1. Claim task sul workboard prima di toccare codice.
2. Dichiarare i file in lock (soft lock) prima dell'editing.
3. Evitare editing concorrente sugli stessi file senza handoff esplicito.
4. A fine task: aggiornare workboard, UPG log e rilasciare lock.

## 11. Tracciabilita' Contabile (Nuovo)

Per qualunque modifica che tocca movimenti denaro (`movimenti_cassa`, saldo, forecast, spese ricorrenti):

1. Semantica unica cross-layer
- `saldo_attuale`, `saldo_previsto`, KPI mensili e grafici devono restare coerenti tra loro.
- Uno storno spesa fissa (`categoria="STORNO_SPESA_FISSA"`) e' una rettifica di uscita, non un'entrata operativa.

2. Rettifiche sempre possibili
- La chiusura spesa ricorrente deve essere idempotente e rettificabile anche se la spesa e' gia' disattivata.
- Le rettifiche non cancellano lo storico reale: usano storni attivi/disattivati con audit.

3. Audit obbligatorio
- Ogni effetto economico deve lasciare traccia in `audit_log` (CREATE/UPDATE/DELETE/RESTORE quando applicabile).
- Vietato introdurre scorciatoie che aggiornano saldi o KPI senza movimento tracciabile.

4. Quality gate minimo per patch contabili
- Test mirati su scenario reale + regressione grafico/KPI.
- Verifica esplicita di idempotenza (stessa azione ripetuta non genera duplicati).
- Aggiornamento `docs/upgrades/UPGRADE_LOG.md` con commit e stato finale.

5. Deep-link audit affidabile
- I link dal registro modifiche verso `/cassa` devono applicare stato interno (tab, filtri, focus) anche su stessa route, senza dipendere dal reload pagina.
- Per i movimenti ledger usare `focus_movement` e, quando disponibile, range `da/a` sul giorno del movimento.
- Distinguere link cross-page (es. `/contratti/...`) da link intra-page (`/cassa?...`) con gestione esplicita lato UI.

Riferimenti UPG (cash-critical):
- `UPG-2026-03-03-06`, `UPG-2026-03-03-07`, `UPG-2026-03-03-09`, `UPG-2026-03-03-10` in `docs/upgrades/UPGRADE_LOG.md`.

---

Obiettivo operativo: mantenere ritmo da startup con disciplina da team senior.
