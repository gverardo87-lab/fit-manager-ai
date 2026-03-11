# Patch Spec - Installer Loopback Rewrite Hardening

## Metadata

- Upgrade ID: UPG-2026-03-11-08
- Date: 2026-03-11
- Owner: Codex
- Area: Installer + Frontend Shell + Release Engineering
- Priority: high
- Status: done

## Objective

Trovare e correggere il bug che rende la nuova installazione sul PC di Chiara inutilizzabile
anche con dati e licenza presenti: il frontend standalone buildato nell'installer sta
proxyando `/api`, `/health` e `/media` verso un host di sviluppo (`192.168.1.23:8000`)
congelato dentro `server.js`, invece che verso il backend locale co-installato.

## Root Cause

`frontend/next.config.ts` usava `process.env.NEXT_PUBLIC_API_URL` per costruire i rewrite
server-side. Nel build standalone, Next serializza il risultato dentro
`frontend/.next/standalone/server.js`. Se l'ambiente di build contiene un URL LAN/Tailscale,
quel valore viene baked nell'artefatto distribuito e il frontend installato sul PC cliente
prova a chiamare la macchina di sviluppo.

## Scope

### Runtime / packaging

- `frontend/next.config.ts`
- `tools/build/build-frontend.sh`

### Release docs / governance

- `CLAUDE.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Implementation

1. Rewrite same-origin forzati a `http://127.0.0.1:${backendPort}` lato server standalone.
2. Rimosso l'uso di `NEXT_PUBLIC_API_URL` dai rewrite server-side.
3. Aggiunto un guard di build in `build-frontend.sh` che fallisce se `server.js` contiene
   destinazioni HTTP non-loopback.
4. Formalizzato il pitfall nei documenti di rilascio.

## Verification

- Ispezione del `server.js` buildato rotto: rewrite baked verso `http://192.168.1.23:8000`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "next.config.ts"`
- `git diff --check`

## Result

- Root cause identificata in modo deterministico.
- Sorgente corretta per i prossimi build installer.
- Aggiunto un guardrail che impedisce di produrre di nuovo un artefatto con rewrite
  puntati a un host di sviluppo.

## Residual Risks

1. L'artefatto `dist/FitManager_Setup_1.0.1.exe` gia costruito prima del fix resta invalido
   per redistribuzione.
2. Serve un rebuild del setup prima di riprovare l'upgrade sul PC di Chiara.
3. Il bug e' di packaging, quindi non viene dimostrato chiuso finche non si ricostruisce
   davvero il bundle standalone/installer.

## Next Smallest Step

Ricostruire il setup dopo il fix, produrre un nuovo hash e ripetere l'upgrade in-place sul PC
di Chiara seguendo `docs/UPGRADE_PROCEDURE.md`.
