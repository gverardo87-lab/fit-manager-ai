# FitManager AI Studio - Metodo Codex

Questo file definisce il metodo operativo tra te e Codex per sviluppare con standard senior, mantenendo velocita e qualita.

## 1. Gerarchia delle regole

Fonti di verita (ordine di priorita):
1. `CLAUDE.md` (root)
2. `api/CLAUDE.md`
3. `frontend/CLAUDE.md`
4. `core/CLAUDE.md`
5. `codex.md` (questo file)

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

---

Obiettivo operativo: mantenere ritmo da startup con disciplina da team senior.
