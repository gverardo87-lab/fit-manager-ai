# UPG-2026-03-11-10 - License Key Upgrade Guardrails v1

## Context

Durante la validazione reale sul PC di Chiara, FitManager risultava:

- raggiungibile su `localhost:3000`
- con backend vivo su `localhost:8000`
- ma con pagine apparentemente "in errore"

Il root cause non era un bug del nuovo setup o un problema dati: la `license.key`
era stata spostata fuori dalla cartella `data\` attiva durante reinstallazione/prove.

Questo microstep non cambia il runtime. Rafforza la procedura operativa e la documentazione
per evitare che un problema di file placement venga scambiato per un guasto applicativo.

## Objective

Rendere obbligatorio e tracciabile il controllo fisico di:

- `<cartella installazione>\data\license.key`

prima di:

- rifare un restore;
- classificare il problema come bug runtime;
- eseguire una nuova reinstallazione.

## Changes

### 1. Upgrade Procedure

Aggiornare `docs/UPGRADE_PROCEDURE.md` per:

- introdurre il controllo del percorso finale di `license.key` nella checklist pre-upgrade;
- aggiungere una verifica esplicita del file nella sezione primo avvio post-upgrade;
- rendere piu rigorosa la procedura "Se la licenza non viene rilevata";
- inserire `license.key` nella checklist finale di accettazione.

### 2. Support Runbook

Aggiornare `docs/SUPPORT_RUNBOOK.md` per:

- aggiungere un controllo fisico obbligatorio del file licenza in `5.2a`;
- documentare il caso reale `3000 ok / 8000 health missing license`;
- chiarire che restore e reinstallazione non sono la prima risposta in questo scenario;
- aggiungere il controllo `data/license.key` nella recovery post-update.

### 3. Release Checklist

Aggiornare `docs/RELEASE_CHECKLIST.md` con un item esplicito:

- verifica manuale post-install/post-upgrade della presenza di `data/license.key`
  nella cartella installata finale.

### 4. CLAUDE.md Pitfalls

Aggiungere il caso reale al catalogo pitfall per fissare la lezione appresa:

- pagine tutte in errore con runtime sano;
- root cause: `data/license.key` spostata.

## Verification

- review manuale di `docs/UPGRADE_PROCEDURE.md`
- review manuale di `docs/SUPPORT_RUNBOOK.md`
- review manuale di `docs/RELEASE_CHECKLIST.md`
- review manuale del pitfall aggiunto in `CLAUDE.md`
- `git diff --check`

## Residual Risks

- Questo microstep non automatizza ancora la diagnosi in-app della licenza spostata.
- Il prodotto continua a dipendere dal file fisico `data/license.key`; in futuro si puo
  valutare una surface diagnostica ancora piu esplicita nel wizard/install status.

## Next Step

Usare la nuova procedura irrigidita durante i prossimi upgrade reali sul PC di Chiara
e nel rollout del setup `1.0.2`.
