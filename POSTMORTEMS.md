# POSTMORTEMS.md - FitManager AI Studio

Questa non e' una fonte di regole nuove.
Raccoglie solo lezioni concrete da errori gia' emersi, per evitare che la memoria orale torni a guidare il progetto.

## 2026-03-11 - Governance sprawl

Problema:
- regole vive, roadmap, release notes e memoria storica erano finite negli stessi documenti

Lezione:
- un agente deve poter trovare in pochi minuti:
  - come lavorare
  - cosa non puo' violare
  - cosa conta per il lancio
- il resto va trattato come storico o riferimento locale, non come legge

## 2026-03-11 - `license.key` fuori da `data/`

Problema:
- su macchina installata l'app sembrava rotta, ma il runtime era sano
- la licenza era stata spostata fuori da `data/license.key`

Lezione:
- prima di classificare un caso come bug runtime, controllare la presenza fisica della licenza nella cartella dati attiva

## 2026-03-11 - Rewrite standalone contaminati da host di sviluppo

Problema:
- il bundle installer puntava ancora a un host dev baked nel frontend standalone

Lezione:
- i rewrite server-side devono restare loopback-safe
- il build deve fallire se congela destinazioni HTTP non ammesse

## 2026-03-11 - Ambiguita' su `trusted_devices`

Problema:
- alcune guide facevano sembrare `trusted_devices` equivalente a accesso senza login applicativo

Lezione:
- l'accesso di rete e l'autenticazione FitManager sono due passaggi distinti
- il Funnel pubblico serve solo per route pubbliche come l'anamnesi

## 2026-03-10 - Documenti storici scambiati per stato corrente

Problema:
- piani e snapshot vecchi sembravano ancora prescrittivi

Lezione:
- i numeri e i freeze temporanei devono vivere nel ledger upgrade o nei runbook dedicati
- i documenti autorevoli devono contenere solo cio' che resta vero oltre il microstep
