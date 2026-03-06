# UPG-2026-03-06-32 - Clienti MyPortal Readiness Board

## Metadata

- Upgrade ID: UPG-2026-03-06-32
- Date: 2026-03-06
- Owner: Codex
- Area: Clienti UX
- Priority: medium
- Target release: codex_02

## Problem

La dashboard mostra gia la coda Clinical Readiness, ma manca una pagina dedicata sotto l'area Clienti per il lavoro quotidiano di completamento dati.

Chiara ha bisogno di vedere in un solo punto, cliente per cliente:

- stato anamnesi;
- presenza misurazioni baseline;
- presenza scheda allenamento;
- next-action immediata.

## Desired Outcome

Introdurre `MyPortal` come pagina dedicata sotto Clienti, con layout operativo CRM e stessa fonte dati/calcolo della dashboard (`/dashboard/clinical-readiness`), senza duplicare logica backend.

## Scope

- In scope:
  - nuova route frontend `GET /clienti/myportal` (App Router page);
  - tabella operativa per cliente con stato `anamnesi / misurazioni / scheda`, priorita e CTA;
  - filtri rapidi (da completare/tutti/pronti) + ricerca cliente;
  - accesso rapido da pagina Clienti e voce sidebar sotto sezione Clienti.
- Out of scope:
  - nuovi endpoint API;
  - modifiche algoritmo readiness;
  - analisi clinico-scientifica avanzata (fase successiva).

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/clienti/myportal/page.tsx`
  - `frontend/src/app/(dashboard)/clienti/page.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
  - `docs/upgrades/specs/UPG-2026-03-06-32-clienti-myportal-readiness-board.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - nessun dato finanziario in overview;
  - nessun endpoint nuovo o query aggiuntiva lato API;
  - fonte di verita unica: readiness dashboard.

## Acceptance Criteria

- Functional:
  - route `clienti/myportal` disponibile e navigabile;
  - ogni riga cliente espone stato anamnesi, misurazioni, scheda + CTA coerente;
  - filtri e ricerca riducono la lista senza ricarichi custom.
- UX:
  - loading/error/empty espliciti;
  - mobile con card compatte e desktop con tabella.
- Technical:
  - lint verde sui file frontend toccati;
  - nessuna modifica backend necessaria.

## Test Plan

- Frontend lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/clienti/myportal/page.tsx" "src/app/(dashboard)/clienti/page.tsx" "src/components/layout/Sidebar.tsx"`

## Risks and Mitigation

- Risk 1: disallineamento tra dashboard e pagina dedicata.
- Mitigation 1: riuso `useClinicalReadiness` senza logica parallela.
- Risk 2: sovraccarico cognitivo su mobile.
- Mitigation 2: vista card mobile semplificata con 3 stati chiave e singola CTA.

## Rollback Plan

- Revert mirato:
  - `frontend/src/app/(dashboard)/clienti/myportal/page.tsx`
  - `frontend/src/app/(dashboard)/clienti/page.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
