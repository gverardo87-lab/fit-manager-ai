# UPG-2026-03-11-12 - Dashboard Connectivity Onboarding Promotion

## Contesto

Il workstream `Connectivity Setup Wizard` e' ora completo dentro `Impostazioni`:

- stato runtime read-only;
- apply guidato della configurazione;
- verify dell'origine pubblica;
- validazione funzionale del link anamnesi;
- stepper prodotto.

Dopo la validazione reale sul PC di Chiara, il problema residuo non e' piu tecnico ma
di discoverability: il trainer puo' completare installazione, login e uso locale del CRM
senza accorgersi che il setup di connettivita' e' gia pronto o quasi pronto.

## Obiettivo

Promuovere il wizard `Connettivita` nel punto piu naturale del prodotto: la dashboard
post-login.

Il microstep introduce una card onboarding leggera, non bloccante e dismissibile che:

1. compare solo quando il profilo non e' ancora `public_portal`;
2. propone il passo successivo corretto:
   - `local_only` -> `Dispositivi fidati`
   - `trusted_devices` -> `Portale pubblico`
3. porta direttamente a `Impostazioni#connettivita`.

## Ambito

### Frontend

- `frontend/src/components/dashboard/connectivity-onboarding.ts`
- `frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`
- `frontend/src/app/(dashboard)/page.tsx`
- `frontend/src/app/(dashboard)/impostazioni/page.tsx`
- `frontend/src/__tests__/dashboard/connectivity-onboarding.test.ts`

### Governance

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Non-obiettivi

- nessuna nuova API backend;
- nessun wizard globale/modale al login;
- nessuna mutazione automatica della configurazione;
- nessuna sostituzione del wizard in `Impostazioni`.

## Verifica attesa

- lint frontend verde sui file toccati;
- Vitest dedicato sul mapping del prompt onboarding;
- `git diff --check`.

## Rischio Residuo

Questo microstep migliora la discoverability ma non crea ancora un vero
`first-run gate` globale. Se il trainer ignora o dismissa la card, il wizard
resta comunque raggiungibile solo da dashboard e `Impostazioni`.
