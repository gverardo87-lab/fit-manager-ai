# UPG-2026-03-09-12 - Workspace Dominance and Viewport Runtime Pass v1

## Metadata

- Upgrade ID: `UPG-2026-03-09-12`
- Date: `2026-03-09`
- Owner: `Codex`
- Area: `Workspace Runtime + Oggi UX`
- Priority: `high`
- Target release: `codex_02`

## Problem

Dopo la fase di analisi e la formalizzazione della matrice v1, `Oggi` soffriva ancora di due problemi concreti:

- i casi forti non dominavano davvero quelli deboli sullo stesso contesto;
- la pagina restava troppo lunga anche con soli 6 `case_kind` runtime.

In particolare:

- una `session_imminent` non assorbiva ancora i blocker onboarding dello stesso cliente;
- un `payment_overdue` conviveva in `today` con il relativo `contract_renewal_due`;
- `client_reactivation` restava troppo aggressivo nella giornata;
- lo stack mostrava troppe righe alte sopra la fold.

## Desired Outcome

Applicare il primo pass runtime della matrice senza allargare il perimetro:

- nessun nuovo `case_kind`;
- nessun nuovo endpoint;
- dominanza concreta sui 6 casi gia esistenti;
- budget visivo reale nella pagina `Oggi`;
- card piu compatte senza rifare la UI.

## Scope

- In scope:
  - dominanza `session_imminent -> onboarding_readiness`;
  - dominanza `payment_overdue -> contract_renewal_due` in `today`;
  - bucket piu conservativo per `client_reactivation`;
  - budget visivo `2 now / 4 today` nel frontend `Oggi`;
  - compressione verticale di `WorkspaceCaseCard`;
  - test backend aggiornati.
- Out of scope:
  - nuovi segnali workspace;
  - nuovi `case_kind`;
  - memoria locale (`seen`, `snooze`);
  - refactor del detail panel;
  - nuove pagine workspace native.

## Impact Map

- Files/modules touched:
  - `api/services/workspace_engine.py`
  - `tests/test_workspace_today.py`
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
  - `docs/upgrades/specs/UPG-2026-03-09-12-workspace-dominance-and-viewport-runtime-pass-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `api` | `frontend` | `tests` | `docs`
- Invarianti da preservare:
  - nessun leak finance in `today`;
  - nessun cambio contratto API;
  - nessun nuovo `case_kind`;
  - i casi dominati restano accessibili nei workspace nativi dove esistono.

## What Changed

### Backend

- `workspace_engine.py` ora calcola la readiness una sola volta nello snapshot e la usa anche per le sessioni del giorno;
- una `session_imminent` con cliente non pronto:
  - assorbe i blocker onboarding nel `reason`;
  - incrementa `signal_count`;
  - mostra segnali preview readiness;
  - nasconde il corrispondente `onboarding_readiness` da `today`, lasciandolo pero disponibile nel workspace `onboarding`;
- un `payment_overdue` sul contratto ora spinge il relativo `contract_renewal_due` fuori da `today`, ma non lo elimina dal workspace `renewals_cash`;
- `client_reactivation` e stata spostata su bucket piu conservativo:
  - `today` solo se molto forte;
  - altrimenti `upcoming_7d`.

### Detail

- il detail di una `session_imminent` ora include anche i blocker readiness del cliente collegato, cosi il caso dominato non sparisce senza contesto.

### Frontend

- `Oggi` ora rende:
  - massimo `2` casi in `Adesso`
  - massimo `4` casi in `Oggi`
- `WorkspaceCaseCard` e stata compressa:
  - padding ridotto
  - rimossa `impact line`
  - stessa grammatica, meno altezza verticale

## Acceptance Criteria

- un cliente con sessione vicina e onboarding incompleto non genera due casi paralleli in `today`;
- un contratto con rate scadute non mostra anche il rinnovo nello stack di `today`;
- la riattivazione non compare piu come lavoro di giornata salvo casi forti;
- la viewport iniziale di `Oggi` e piu corta senza nuove superfici o nuovi moduli;
- nessun cambio API/type sync richiesto.

## Test Plan

- backend lint:
  - `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`
- frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx"`
- backend pytest mirato:
  - `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py -p no:cacheprovider`

## Verification Outcome

- `ruff` sui file backend toccati: `PASS`
- `eslint` sui file frontend toccati: `PASS`
- `pytest` mirato workspace: `BLOCKED`
  - motivo: il `venv` locale continua a risolvere verso il launcher Python del Microsoft Store

## Risks and Mitigation

- Rischio 1: `todo_manual` resta ancora un caso abbastanza rumoroso se il trainer ne accumula molti.
  - Mitigazione 1: non e stato toccato in questo pass per non nascondere lavoro manuale senza una workspace alternativa dedicata.
- Rischio 2: il budget visivo vive per ora nel frontend `Oggi`, non ancora nel motore come policy universale.
  - Mitigazione 2: il pass e volutamente minimo; se il risultato convince, il prossimo step puo portare il budget nel layer engine.
- Rischio 3: `client_reactivation` non ha ancora una vista nativa separata.
  - Mitigazione 3: e ancora accessibile in `today`, ma meno aggressiva.

## Notes

- Questo step applica la matrice dove serviva davvero: nei casi gia esistenti.
- Non introduce nessuna nuova famiglia o segnali freshness in `Oggi`.
- Il prossimo passo corretto, se il risultato piace, e portare parte del budget nel motore e non aggiungere nuove feature.
