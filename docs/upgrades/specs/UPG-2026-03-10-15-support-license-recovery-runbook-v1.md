# UPG-2026-03-10-15 - Support / License / Recovery Runbook v1

## Contesto

Il piano operativo pre-lancio aveva ancora un vuoto critico: le procedure di supporto
esistevano gia, ma disperse tra documenti diversi (`DEPLOYMENT_PLAN`, `RELEASE_CHECKLIST`,
`TAILSCALE_FUNNEL_SETUP`, `backup.py`, pagina `/licenza`, support snapshot).

Per un prodotto locale commercializzato sulla promessa di affidabilita, questo e un problema:
se l'operatore deve ricordare a memoria l'ordine di intervento, il supporto non e ancora scalabile.

## Obiettivo

Produrre un runbook unico e operativo che copra:
- raccolta evidenze standard;
- gestione licenza;
- backup e restore;
- recovery post-update;
- criteri chiari di escalation.

## Non obiettivi

- nuove API o automazioni runtime;
- redesign UI;
- workflow di rinnovo licenza in-app;
- code signing;
- runbook rete dettagliato completo (resta in `TAILSCALE_FUNNEL_SETUP.md`).

## Deliverable

- nuovo documento operativo:
  - `docs/SUPPORT_RUNBOOK.md`
- aggiornamento checklist release per rendere il runbook parte esplicita della readiness
- sync governance:
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`

## Decisioni chiave

1. Il runbook parte sempre da `Stato installazione` + `Snapshot diagnostico` + log locale.
2. La licenza viene trattata come problema operativo distinto, con mappa stati -> azioni.
3. Il restore corretto passa solo dal flusso ufficiale di backup v2; niente overwrite manuali del DB.
4. Il recovery post-update viene normalizzato: raccogliere evidenze, usare `pre_update`, poi rollback.
5. I problemi rete/Funnel vengono solo instradati; il runbook specialistico resta separato.

## File toccati

- `docs/SUPPORT_RUNBOOK.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Verifica prevista

- review manuale di coerenza con:
  - `docs/DEPLOYMENT_PLAN.md`
  - `docs/RELEASE_CHECKLIST.md`
  - `docs/TAILSCALE_FUNNEL_SETUP.md`
  - `api/routers/backup.py`
  - `frontend/src/app/licenza/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`

## Rischi residui

1. Il runbook resta manuale: la prova installata `rimuovi license.key -> /licenza` non viene sostituita dal documento.
2. Il problema ambiente della venv locale continua a limitare alcune prove pytest focused.
3. I log sono disponibili ma non ancora richiamati direttamente dalla UI.

## Next step

Dopo il runbook, il prossimo P0 corretto resta la validazione manuale di rete e macchina pulita:
- LAN tablet/smartphone
- Tailscale VPN
- Funnel smartphone
- installazione pulita Windows
