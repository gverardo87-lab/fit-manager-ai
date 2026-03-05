# UPG-2026-03-05-02 - Dashboard Privacy-Safe Overview

## Metadata

- Upgrade ID: UPG-2026-03-05-02
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: pre-launch final rush

## Problem

La dashboard veniva lasciata aperta anche in presenza del cliente, ma mostrava metriche economiche
(entrate, uscite, margine, saldo, scaduto/in-arrivo) non adatte a un contesto client-facing.

## Desired Outcome

Rendere la dashboard una vista operativa neutra, utile al chinesiologo durante la sessione e priva
di dati economici sensibili.

## Scope

- In scope:
  - rimozione KPI economici dalla dashboard;
  - rimozione sezione "Orizzonte Finanziario";
  - filtro alert economici (`overdue_rates`);
  - sostituzione quick action economica con azione operativa.
- Out of scope:
  - redesign completo dashboard;
  - modifiche backend a endpoint finanziari;
  - pagine Cassa/Contratti.

## Impact Map

- Files/modules toccati:
  - `frontend/src/app/(dashboard)/page.tsx`
- Layer coinvolti: `frontend`
- Invarianti da preservare:
  - routing esistente;
  - alert sheet operative non finanziarie;
  - empty/loading/error state dashboard.

## Acceptance Criteria

- Funzionale:
  - dashboard non espone importi o KPI cassa;
  - restano KPI operativi (clienti attivi, appuntamenti oggi);
  - quick action verso cassa rimossa dalla home dashboard.
- UX:
  - layout coerente (2 colonne operative);
  - alert panel mantiene severita/CTA per categorie non economiche.
- Tecnico:
  - nessun import/hook economico non usato nella pagina dashboard;
  - lint pulito sul file modificato.

## Test Plan

- Unit/Integration:
  - N/A (patch UI mirata).
- Manual checks:
  - apertura dashboard con/senza dati;
  - verifica assenza importi economici a schermo.
- Build/Lint gates:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`

## Risks and Mitigation

- Rischio 1: riduzione eccessiva del contesto per operatori che usano la dashboard per la cassa.
- Mitigazione 1: mantenere pagina Cassa invariata e facilmente raggiungibile da sidebar.

## Rollback Plan

- Ripristinare commit precedente della dashboard (`git revert b353ec8`) se emergono regressioni UX.

## Notes

- Commit implementativo: `b353ec8`
