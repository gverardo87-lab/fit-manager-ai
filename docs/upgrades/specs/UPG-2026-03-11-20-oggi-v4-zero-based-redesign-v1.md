# UPG-2026-03-11-20 - Oggi v4 Zero-Based Redesign

## Metadata

- Upgrade ID: `UPG-2026-03-11-20`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `Frontend Workspace UX + CRM Launch Experience`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

> Historical implementation snapshot, not current source of truth.
> The current `/oggi` route no longer matches this spec closely enough for it to guide new redesign work directly.

## Why This Exists

Dopo il benchmark `UPG-2026-03-11-19`, il verdetto e stato esplicito:

- il problema di `Oggi` non era solo di densita;
- la grammatica stessa restava troppo vicina a una dashboard a card;
- serviva un redesign massiccio ripartendo da zero.

Questo microstep applica quella decisione e sostituisce la grammatica precedente con una nuova
surface operativa piu vicina alle best practice osservate nei CRM top:

- un solo feed di lavoro;
- filtri forti e pochi;
- righe dossier invece di card alte;
- un dossier unico a destra;
- contesto cliente mantenuto ma ricondotto a un passaporto sessione piu leggibile.

## Benchmark Inputs

Fonti ufficiali gia usate nel microstep precedente e confermate come base decisionale:

- HubSpot `Sales Workspace` e `Prospecting Queue`
- monday CRM `Timeline Overview` e quick actions mobile
- Pipedrive `Pulse`
- Salesforce `Sales Cloud / Activity Management / Pipeline Management`

Traduzione pratica per FitManager:

- una sola home operativa;
- queue dominante;
- preview/dossier a lato;
- meno sezioni stacked;
- meno browsing, piu prossima mossa.

## Scope

- In scope:
  - redesign completo della page shell di `/oggi`;
  - nuova grammatica `feed + dossier`;
  - filtri vista `Focus / Linea completa / Backlog`;
  - refactor visuale dei componenti `WorkspaceCaseCard`, `WorkspaceDetailPanel`,
    `WorkspaceAgendaPanel`, `OggiClientContextPanel`;
  - unificazione del rail destro in una sola superficie forte;
  - mantenimento e affinamento del contesto cliente/sessione.
- Out of scope:
  - nuove mutation (`snooze`, `mark managed`, `quick note`);
  - persistenza URL di filtri/selezione;
  - nuove API backend;
  - cambio della home post-login da `/` a `/oggi`.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
  - `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
  - `frontend/src/components/workspace/OggiClientContextPanel.tsx`
  - `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
  - `docs/upgrades/specs/UPG-2026-03-11-20-oggi-v4-zero-based-redesign-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `frontend` | `docs`
- Skills applicate:
  - `fitmanager-operational-workspace-design`
  - `fitmanager-responsive-adaptive-ui`
  - `fitmanager-frontend-safety`
  - `fitmanager-microstep-delivery`
  - `fitmanager-upgrade-doc-sync`

## Locked Decisions

- `Oggi` smette di essere una pila di sezioni-card e diventa una board con feed unico.
- La queue usa pochi filtri persistenti in memoria (`Focus`, `Linea completa`, `Backlog`) invece di
  bucket stacked apri/chiudi.
- La grammatica di default dei casi e `row dossier`, non `standalone card`.
- Il rail destro torna a essere una superficie unica forte:
  - sopra dossier caso;
  - sotto passaporto cliente/sessione.
- Le informazioni utili della vecchia `session prep` restano, ma vengono compattate e rese piu
  leggibili.

## Visual / IA Outcome

### 1. Masthead corto

Il top della pagina diventa un `newsdesk strip`:

- titolo + data;
- brief in una riga;
- counters inline;
- agenda integrata nella stessa fascia invece che in una card separata.

### 2. Queue come feed

La queue non e piu un insieme di box narrativi.

Ora usa:

- header unico;
- tre filtri forti;
- lane header compatti;
- righe dossier dense con:
  - tipo;
  - severita;
  - scadenza;
  - titolo;
  - reason;
  - contesto cliente raffinato;
  - una CTA primaria.

### 3. Dossier unificato

Il rail destro non presenta piu pannelli che competono tra loro.

La surface e:

- un solo contenitore alto controllato;
- detail case sopra;
- context cliente/sessione sotto;
- scroll interno per evitare crescita verticale infinita.

### 4. Session passport

Il vecchio contesto cliente resta importante e non viene perso.

Pero cambia forma:

- stat compatte;
- alert clinici leggibili;
- checklist rapida prioritaria;
- hints limitati e piu utili;
- link rapidi finali.

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/WorkspaceCaseCard.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/WorkspaceDetailPanel.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/OggiClientContextPanel.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/WorkspaceAgendaPanel.tsx"`
- `git diff --check`

Nota ambiente:

- il primo tentativo con `npm` via PowerShell e fallito per policy locale su `npm.ps1`;
- la verifica reale e stata rilanciata con `npm.cmd`.

## Risks Found

1. Il redesign cambia radicalmente la grammatica di `Oggi`, ma non persiste ancora `queueView` e
   `selectedCaseId` nell'URL.
2. Il matching tra `OperationalCase` e `SessionPrepItem` resta euristico lato frontend
   (`event_id / client_id`).
3. Non e ancora stato eseguito un pass manuale visuale a `390px / 768px / 1024px`, quindi la
   verifica responsive resta solo parziale rispetto ai quality gate ideali.

## Recommended Next Step

Il prossimo microstep corretto non e un altro redesign totale.

E:

- review visuale reale di `Oggi` su desktop/tablet/mobile;
- poi tuning mirato di skills/agents solo sui punti in cui il nuovo risultato resta ancora sotto
  il livello atteso.
