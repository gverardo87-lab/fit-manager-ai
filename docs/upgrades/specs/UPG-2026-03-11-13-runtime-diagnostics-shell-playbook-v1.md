# UPG-2026-03-11-13 - Runtime Diagnostics Shell Playbook

## Contesto

Durante il rollout sul PC del trainer e' emerso un caso operativo importante:

- FitManager sembrava rotto dopo reinstall/upgrade;
- `localhost:3000` rispondeva;
- `localhost:8000/health` segnalava licenza mancante;
- il problema reale non era il setup, ma la `license.key` spostata fuori da `data\`.

Questa diagnosi e' stata possibile solo usando comandi shell semplici e ripetibili.

## Obiettivo

Salvare in un artefatto stabile:

- i comandi PowerShell esatti;
- la lettura corretta delle porte `3000` e `8000`;
- la matrice decisionale minima;
- il controllo fisico di `data\license.key`;
- i comandi su processi/log da usare prima di restore o reinstallazione.

Il documento deve essere riusabile per:

- supporto tecnico;
- guida utente;
- manuale di prodotto;
- monografia di lancio.

## Ambito

### Nuovo documento

- `docs/RUNTIME_DIAGNOSTICS_PLAYBOOK.md`

### Collegamenti aggiornati

- `docs/SUPPORT_RUNBOOK.md`
- `docs/UPGRADE_PROCEDURE.md`

### Governance

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Non-obiettivi

- nessun cambio runtime applicativo;
- nessuna nuova API;
- nessuna automazione shell in-app;
- nessun cambio alla policy licenza o restore.

## Verifica attesa

- review manuale del playbook e dei collegamenti;
- grep mirato su `3000`, `8000`, `curl.exe`, `license.key`, `Test-Path`, `netstat`;
- `git diff --check`.

## Rischio Residuo

Il playbook resta operativo/manuale: aiuta a distinguere piu velocemente le classi di guasto,
ma non sostituisce ancora una diagnosi automatica guidata dentro il prodotto.
