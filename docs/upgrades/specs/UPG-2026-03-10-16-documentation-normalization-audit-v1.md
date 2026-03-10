# UPG-2026-03-10-16 - Documentation Normalization Audit v1

## Contesto

Dopo i microstep di launch hardening (`support snapshot`, `proxy`, logging locale, test licensing,
runbook supporto) la documentazione era funzionalmente avanzata ma non ancora del tutto coerente.

I drift principali emersi nell'audit:
- `frontend/CLAUDE.md` e `docs/TAILSCALE_FUNNEL_SETUP.md` continuavano a parlare di `middleware.ts`
  invece del boundary reale `src/proxy.ts`;
- i layer guide non citavano ancora i nuovi artefatti di sistema (`system.py`, `system_runtime.py`,
  `logging_config.py`, `useSystemHealth`, `useSystemSupport`, card impostazioni);
- il piano operativo `UPG-2026-03-10-09` descriveva correttamente il backlog iniziale, ma senza
  distinguere chiaramente tra stato storico del piano e stato corrente gia chiuso;
- il manifesto root non esponeva ancora tra i checkpoint pre-distribuzione gli artefatti ormai centrali
  del supporto locale (`Stato installazione`, `Snapshot diagnostico`, logging locale, support runbook).

## Obiettivo

Riallineare i documenti autorevoli e i runbook principali al prodotto reale del 10 marzo 2026,
senza riscrivere la storia degli upgrade chiusi.

## Non obiettivi

- nuove feature runtime;
- modifiche a codice applicativo;
- chiusura dei gate manuali ancora aperti (rete, macchina pulita, prova `/licenza` su installazione reale).

## File toccati

- `CLAUDE.md`
- `frontend/CLAUDE.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `docs/DEPLOYMENT_PLAN.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/upgrades/specs/UPG-2026-03-10-09-launch-operations-plan-v1.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Decisioni chiave

1. La terminologia ufficiale passa ovunque a `proxy` quando il riferimento e il boundary Next 16.
2. Il piano `UPG-2026-03-10-09` conserva il suo valore storico, ma ottiene un `Progress Update`
   esplicito per non sembrare fermo allo stato iniziale.
3. I `CLAUDE.md` layer-specifici devono menzionare i nuovi mattoni architetturali introdotti dai
   microstep di launch hardening.
4. La checklist release distingue ora meglio il test negativo licensing automatico gia coperto
   dalla prova manuale ancora richiesta su installazione reale.

## Verifica prevista

- review manuale dei documenti toccati
- grep mirato su:
  - `middleware.ts`
  - `proxy.ts`
  - `SUPPORT_RUNBOOK`
  - `support snapshot`
  - `logging locale`

## Rischi residui

1. Restano entry storiche con `_pending_` fuori dallo scope immediato di questo audit.
2. Alcuni documenti storici piu vecchi presentano ancora testo legacy o encoding non perfetto.
3. Il riallineamento documentale non sostituisce la validazione manuale dei gate rete/macchina pulita.

## Next step

Dopo questo audit, il prossimo microstep corretto non e piu documentale ma operativo:
- validazione manuale LAN / Tailscale / Funnel
- installazione pulita su macchina Windows non-dev
