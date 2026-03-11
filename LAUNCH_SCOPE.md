# LAUNCH_SCOPE.md - FitManager AI Studio

Questo documento definisce cosa conta davvero per arrivare al lancio.
Non e' un changelog e non e' un backlog totale.

## Obiettivo

Portare FitManager a un lancio credibile come software locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA,
con installazione ripetibile, supporto gestibile e flussi core affidabili.

## In scope ora

- installazione locale con licenza, setup wizard e runtime health leggibile
- core CRM operativo:
  - clienti
  - contratti e pagamenti
  - agenda
  - cassa
  - schede/workout
  - misurazioni/anamnesi
- backup, restore e diagnostica locale
- connettivita' guidata per:
  - `local_only`
  - `trusted_devices`
  - `public_portal`
- portale pubblico per anamnesi cliente
- runbook di supporto e procedura di upgrade realmente eseguibili

## Criteri di passaggio al launch

Prima del lancio allargato servono evidenze su:

- installazione o upgrade su macchina Windows non-dev
- percorso negativo licenza (`/licenza`) verificato
- backup e restore riusciti con dati reali
- validazione reale LAN / Tailscale / Funnel
- artefatto di rilascio ripetibile, versionato e tracciabile
- issue note e fallback di supporto chiari

## Fuori scope fino a dopo il launch

- cloud sync o trasformazione in SaaS
- app mobile native
- chat/messaging in-app
- modulo nutrizione completo
- multi-operatore/team workflow
- nuove macro-feature AI non necessarie al CRM core
- redesign trasversali che non spostano affidabilita' o supportabilita'

## Regole anti-scope-creep

- Nessuna nuova macro-feature entra se rallenta installazione, supporto, licenza, backup o connettivita'.
- La UI puo' migliorare, ma non a costo di regressioni nei flussi core del trainer.
- La documentazione di launch deve restare corta: decisioni vive qui, dettagli storici nel ledger upgrade.

## Riferimenti operativi

Per la procedura concreta usare:

- `docs/SUPPORT_RUNBOOK.md`
- `docs/UPGRADE_PROCEDURE.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `docs/RELEASE_CHECKLIST.md`

Per la storia dettagliata dei microstep:

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`
- `docs/upgrades/specs/UPG-2026-03-04-06-launch-market-readiness-roadmap.md`
