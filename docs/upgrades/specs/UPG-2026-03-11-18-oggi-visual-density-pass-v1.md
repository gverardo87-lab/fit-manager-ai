# UPG-2026-03-11-18 - Oggi Visual Density Pass

## Metadata

- Upgrade ID: `UPG-2026-03-11-18`
- Date: `2026-03-11`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Visual Design + Responsive Density`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

> Historical implementation note: this density pass is preserved for traceability only.
> It should not freeze the next visual direction of `/oggi`.

## Problem

Dopo `UPG-2026-03-11-17`, `Oggi` aveva finalmente la struttura giusta ma non ancora il livello
grafico corretto.

I limiti reali emersi in review erano questi:

- troppa altezza consumata da header, header di sezione e wrapper;
- queue card ancora troppo vicine alla grammatica storica `card SaaS`;
- pannello cliente destro utile ma troppo report-like;
- agenda concettualmente duplicata tra strip alta e card finale destra.

Il rischio non era funzionale ma di percezione prodotto:

- pagina ordinata, si;
- pagina inevitabile e premium, non ancora.

## Outcome

`Oggi` riceve un pass esplicitamente grafico e di densita, senza cambiare il contratto logico.

Decisioni chiave del microstep:

- la queue default smette di usare una grammatica card alta e passa a una grammatica
  `row-dossier` piu densa;
- header e bucket header vengono compressi;
- il pannello cliente destro diventa piu corto e meno report-like;
- la card finale agenda viene rimossa per evitare duplicazione verticale.

## Scope

- In scope:
  - compattazione di `frontend/src/app/(dashboard)/oggi/page.tsx`;
  - redesign densita di `frontend/src/components/workspace/WorkspaceCaseCard.tsx` per il variant
    default;
  - compattazione di `frontend/src/components/workspace/OggiClientContextPanel.tsx`;
  - compattazione di `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`;
  - sync docs del microstep.
- Out of scope:
  - modifiche al contratto API workspace;
  - refactor del `WorkspaceDetailPanel` shared;
  - persistenza URL di stato pagina;
  - tuning formale delle skill in questo stesso microstep.

## Implementation Summary

### 1. Header e bucket meno narrativi

`frontend/src/app/(dashboard)/oggi/page.tsx` riduce la verticale in tre modi:

- header pagina meno hero e piu workspace masthead;
- `HeaderPill` piu compatte;
- `QueueSection` con helper text compatto e allineato, non piu come mini-blocco narrativo.

### 2. Case card come riga operativa

`frontend/src/components/workspace/WorkspaceCaseCard.tsx` cambia grammatica per il variant
default:

- densita piu orizzontale;
- severity rail sempre visibile;
- meta compatte;
- CTA primaria unica;
- rimozione del bottone `Dettaglio` ridondante, visto che l'intera card e gia selezionabile.

Il variant finance resta sostanzialmente invariato per non sporcare `Rinnovi & Incassi`.

### 3. Rail destro piu corto

`frontend/src/components/workspace/OggiClientContextPanel.tsx` viene compattato:

- stat tile piu piccole;
- chip piu strette;
- checklist e hint piu dense;
- copy piu corta;
- sezioni meno “report”.

### 4. Agenda con un solo proprietario

`frontend/src/components/workspace/WorkspaceAgendaPanel.tsx` viene compressa e resa piu tesa.

In parallelo, la card finale “Serve piu contesto di agenda?” viene rimossa da `/oggi`.

Decisione chiave:

- l'agenda ha gia il suo proprietario visivo nella strip alta;
- non va ribadita anche nel fondo del rail destro.

## Files Touched

- `frontend/src/app/(dashboard)/oggi/page.tsx`
- `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `frontend/src/components/workspace/OggiClientContextPanel.tsx`
- `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
- `docs/upgrades/specs/UPG-2026-03-11-18-oggi-visual-density-pass-v1.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/OggiClientContextPanel.tsx" "src/components/workspace/WorkspaceAgendaPanel.tsx"`
- review manuale di:
  - `frontend/src/app/(dashboard)/oggi/page.tsx`
  - `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
  - `frontend/src/components/workspace/OggiClientContextPanel.tsx`
  - `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
- `git diff --check`

## Risks Found

### 1. Detail panel shared ora sembra il blocco piu alto della pagina

Dopo aver compattato queue, agenda e rail cliente, il prossimo collo di bottiglia visivo diventa
`WorkspaceDetailPanel`.

Rischio:

- il rail destro puo ancora apparire piu lungo del necessario per il variant default.

Next smallest corrective step:

- fare un microstep dedicato di compattazione del `WorkspaceDetailPanel` solo per il variant
  default, senza toccare finance.

### 2. `Puo aspettare` resta ancora stack-based

La densita e migliorata, ma il blocco backlog continua ad accumulare sottosezioni verticali.

Rischio:

- quando i bucket laterali crescono, la pagina puo tornare a consumare altezza.

Next smallest corrective step:

- trasformare `Puo aspettare` in una lane con tab/segmented switch tra `3g`, `7g`, `waiting`.

### 3. Nessun pass visuale live su viewport

Il microstep e verificato con lint e review manuale del codice, ma non con pass live
390px / 768px / 1024px.

Rischio:

- parte del guadagno di densita potrebbe essere sbilanciato su uno dei tre breakpoint.

Next smallest corrective step:

- aprire un pass visuale esplicito solo responsive su `Oggi`.

## Decision

Questo pass non cambia la logica di `Oggi`, ma cambia la sua percezione:

- meno “dashboard card pack”;
- piu “workspace operativo premium”;
- meno duplicate utility surfaces;
- migliore rapporto tra viewport occupata e casi realmente visibili.
