# Patch Spec - Next Proxy Migration v1

## Metadata

- Upgrade ID: UPG-2026-03-10-12
- Date: 2026-03-10
- Owner: Codex
- Area: Frontend Shell + Launch Hardening
- Priority: high
- Status: done

## Problem

La shell Next.js era ancora basata sulla convenzione `middleware.ts`, che in Next.js 16 e'
deprecata in favore di `proxy.ts`. Il comportamento runtime era corretto, ma la build continuava
a portarsi dietro un warning strutturale proprio sul boundary piu sensibile della distribuzione:
protezione route, redirect auth e proxying same-origin verso il backend FastAPI.

Nel piano di lancio questo warning era gia classificato come P0: prima del pilot la shell deve
restare pulita, prevedibile e senza convenzioni deprecate.

## Desired Outcome

- La shell frontend usa la convenzione Next 16 corretta (`src/proxy.ts`).
- La logica di protezione non cambia:
  - stesse `PUBLIC_ROUTES`
  - stesse `AUTH_ONLY_PAGES`
  - stesso `config.matcher`
  - stessi redirect 307
- `next build` non deve piu segnalare il warning sulla vecchia convenzione `middleware`.

## Scope

- In scope:
  - migrazione `frontend/src/middleware.ts -> frontend/src/proxy.ts`
  - mantenimento integrale della semantica auth/proxy esistente
  - aggiornamento dei riferimenti autorevoli nel manifesto e nei documenti di tracking
- Out of scope:
  - redesign auth
  - refactor `AuthGuard`
  - nuove route pubbliche
  - modifiche ai rewrite di `next.config.ts`

## Implementation

### Frontend Runtime

- `frontend/src/proxy.ts`
  - nuova entrypoint conforme a Next.js 16;
  - export `proxy()` al posto di `middleware()`;
  - commenti aggiornati alla nuova terminologia;
  - conservati senza variazioni `TOKEN_COOKIE`, `PUBLIC_ROUTES`, `AUTH_ONLY_PAGES` e `config.matcher`.
- `frontend/src/middleware.ts`
  - rimosso.

### Governance / Documentation

- `CLAUDE.md`
  - aggiornati i due pitfalls autorevoli che parlavano ancora di `middleware`.
- `docs/ai-sync/WORKBOARD.md`
  - chiusura task attivo `AGT-2026-03-10-13`.
- `docs/upgrades/UPGRADE_LOG.md`
  - aggiunta riga `UPG-2026-03-10-12`.
- `docs/upgrades/README.md`
  - riallineato l'ultimo stato del piano di lancio: warning chiuso, prossimo P0 = logging locale.

## Verification

- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/proxy.ts"`
- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build`

## Risks / Residuals

1. `AuthGuard.tsx` contiene ancora commenti storici che citano la vecchia terminologia e il file ha
   un debt lint preesistente (`react-hooks/set-state-in-effect`). Non e' stato incluso per non
   allargare questo microstep runtime.
2. Restano modifiche locali non correlate nel working tree. Il commit finale dovra includere solo i
   file del microstep `UPG-2026-03-10-12`.

## Next Smallest Step

Aprire il P0 successivo del launch plan: logging locale governato in `data/logs/`, con rotazione
base e supportabilita reale post-installazione.
