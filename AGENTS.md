# AGENTS.md - FitManager AI Studio

Questo file e' il contratto operativo unico per gli agenti che lavorano nel repository.
Obiettivo: mantenere velocita di consegna alta senza perdere affidabilita', privacy e chiarezza.

## 1) Fonti autorevoli

Quando le istruzioni confliggono, usare questo ordine:

1. system/developer/runtime constraints
2. `AGENTS.md`
3. `MANIFESTO.md`
4. `LAUNCH_SCOPE.md`
5. `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md` solo per il layer toccato
6. `POSTMORTEMS.md`
7. runbook, upgrade docs e altra documentazione solo quando servono

File legacy da non usare come nuova fonte di regole:

- `CLAUDE.md`
- `codex.md`
- `docs/ai-sync/MULTI_AGENT_SYNC.md`

Servono solo come compatibilita' e redirect.

## 2) Delivery Loop

Per ogni task:

1. scrivere un impact map breve:
   - obiettivo
   - file/layer toccati
   - invarianti da preservare
2. fare un microstep utile alla volta
3. verificare subito il microstep
4. riportare:
   - cosa e' cambiato
   - cosa e' stato verificato
   - rischi/gap emersi
   - prossimo passo minimo

Non nascondere i rischi. Se emergono, esplicitarli presto.

## 3) Principi non negoziabili

- Privacy-first nelle viste visibili al cliente.
- Dati finanziari confinati nei contesti finance dedicati.
- Multi-tenant safety: mai bypassare ownership checks.
- Auditabilita' per operazioni critiche.
- Determinismo nei flussi business-critical.
- Nessun path assoluto hardcoded.
- Dati persistenti solo in `data/`.
- Il CRM core deve restare usabile senza dipendenza AI obbligatoria.

## 4) Guardrail ingegneristici

### Backend

- Preservare Bouncer Pattern e Deep Relational IDOR checks.
- Prevenire mass assignment.
- Tenere atomiche le operazioni multi-entita'.
- Mantenere audit log coerenti sulle transizioni critiche.

### Frontend

- Tenere il type sync con `frontend/src/types/api.ts`.
- Invalidare le query in modo simmetrico sulle operazioni inverse.
- Gestire sempre loading/error/empty state.
- Evitare dati sensibili nelle overview di default.
- Applicare la skill piu' specifica disponibile per il surface toccato.
- Usare skill responsive/mobile solo se il task impatta davvero il layout adattivo.
- Usare skill guide/help solo per superfici guida.
- Riferimento rapido:
  - dashboard overview -> `fitmanager-dashboard-crm-design`
  - workspace operativi -> `fitmanager-operational-workspace-design`
  - record page CRM -> `fitmanager-crm-record-page-design`
  - responsive/mobile -> `fitmanager-responsive-adaptive-ui`
  - guide/help -> `fitmanager-guide-content-architecture`
  - assets guida illustrati -> `fitmanager-guide-illustrated-playbook`

### Cross-layer

- Nessuna nuova policy di prodotto inventata nei docs o nel codice.
- I documenti storici non devono diventare regole operative.
- Per assistant/help routing usare `fitmanager-assistant-guide-linking` con guardrail API/frontend.
- Preferire la soluzione piu' semplice e robusta compatibile con il launch scope.
- Evitare refactor larghi, nuove astrazioni o nuova documentazione se non richiesti dal task.

## 5) Collaborazione e documentazione

Quando la task tocca codice condiviso, piu' file o governance/processo, il claim su `docs/ai-sync/WORKBOARD.md` e' obbligatorio:

1. claim su `docs/ai-sync/WORKBOARD.md` prima di editare
2. `Locked files` aggiornati ai path reali
3. nessun edit su file lockato senza handoff esplicito
4. a fine task: checks reali, rilascio lock, note sui rischi

Sincronizzare `docs/upgrades/*` solo quando cambia comportamento, architettura, processo o workflow di delivery.
`WORKBOARD.md` e `UPGRADE_LOG.md` sono ledger operativi/storici, non sorgenti di verita' per le regole del prodotto.

## 6) Quality Gates

Baseline:

- eseguire lint/test rilevanti per lo scope toccato

Quando rilevante:

- DB/schema -> migrazione + test backend pertinenti
- cash/ledger -> controlli mirati di integrita' contabile
- safety engine -> QA clinica dedicata
- backup/installer -> backup -> mutate -> restore
- guide/help -> audit copertura + link integrity + responsive pass
- docs/process -> review manuale di coerenza cross-doc

Mai dichiarare "done" senza evidenza di verifica.

## 7) Commit Standard

Commit solo di unita' coese e verificabili.
Formato messaggio:

- `dashboard: ...`
- `api: ...`
- `docs: ...`
- `installer: ...`

Ogni commit deve lasciare il branch rilasciabile per il proprio scope.
