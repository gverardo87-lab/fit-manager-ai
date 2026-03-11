# UPG-2026-03-11-11 — Trusted Devices Clarity + Field Validation Alignment

## Contesto

Dopo la validazione reale sul PC di Chiara, il progetto ha ora evidenza concreta di:

- installazione pulita riuscita su macchina Windows non-dev;
- launcher funzionante con browser aperto correttamente;
- login produzione riuscito;
- accesso remoto `trusted_devices` via Tailscale riuscito da dispositivo esterno.

E' emerso pero' un punto di confusione UX/documentale: il trainer puo' interpretare
il profilo `Dispositivi fidati` come se l'accesso remoto non richiedesse alcuna
autenticazione aggiuntiva sul device remoto.

Il comportamento corretto e':

1. il device remoto deve avere Tailscale installato e loggato nello stesso tailnet;
2. raggiunta la pagina `http://100.x.x.x:3000` o `http://<dns-ts>.ts.net:3000`,
   il trainer deve comunque eseguire il login applicativo FitManager su quel browser;
3. il Funnel pubblico resta riservato alle route pubbliche (anamnesi), non al CRM completo.

## Obiettivo

Allineare con precisione chirurgica:

- checklist di rilascio;
- guida Tailscale/Funnel;
- `CLAUDE.md`;
- copy del wizard `Connettivita`;

cosi' il prodotto e i documenti dicano la stessa cosa su `trusted_devices` e sui test
reali gia' superati.

## Ambito

### Docs

- `docs/RELEASE_CHECKLIST.md`
- `docs/TAILSCALE_FUNNEL_SETUP.md`
- `CLAUDE.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

### Frontend

- `frontend/src/components/settings/system-status-utils.ts`
- `frontend/src/components/settings/connectivity-wizard-panels.tsx`

## Non-obiettivi

- Nessuna nuova API backend
- Nessun cambio di sicurezza o sessione
- Nessuna automazione di login Tailscale o login FitManager
- Nessun test Funnel pubblico finale da smartphone se non gia' eseguito

## Verifica attesa

- lint frontend verde sui file toccati
- `git diff --check`
- review manuale delle checklist e guide aggiornate

## Rischio Residuo

Resta aperto il test finale del percorso pubblico cliente:

- generazione link anamnesi reale;
- apertura da smartphone senza Tailscale;
- invio form end-to-end.
