# UPG-2026-03-09-29 - Rinnovi & Incassi premium ledger redesign v1

## Summary

Secondo pass visuale su `Rinnovi & Incassi`, piu radicale del redesign iniziale:

- la queue finance smette di presentarsi come lista di card standard e passa a righe ledger dense
- la variante `finance` evolve verso una grammatica da ledger operativo premium
- importi ed esposizione diventano il dato dominante
- il pannello dettaglio si comporta piu come dossier economico che come pannello UI generico
- l'azione `Dettaglio` diventa affordance reale verso il dossier, non semplice selezione passiva della riga

## Goal

Portare il workspace finance fuori dall'estetica "dashboard SaaS a card" e avvicinarlo a:

- scrivania economica privata
- blotter operativo
- dossier decisionale

senza toccare:

- ranking
- case engine
- query
- policy di visibilita

## Scope

### Included

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- `frontend/src/components/workspace/WorkspaceCaseCard.tsx`
- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
- `frontend/src/components/workspace/workspace-ui.ts`

### Excluded

- nessuna modifica backend
- nessun nuovo endpoint
- nessun cambio `Oggi`

## Design decisions

### 1. Dense ledger queue, non generic cards

La pagina `Rinnovi & Incassi` ora:

- non usa piu la grammatica a card alte per la queue principale
- espone righe compatte con colonne stabili `caso -> tempo -> importo -> azione`
- riduce lo spazio morto verticale e rende il backlog comprimibile con molto meno scroll
- usa una palette molto piu scura e contrastata, meno beige/editoriale e piu console privata finance

### 2. Finance rows, not decorative cards

La variante `finance` e la nuova row grammar:

- mostra l'importo come dato dominante
- sposta CTA e dettaglio dentro un modulo action-oriented dedicato
- tratta titolo/ragione come contesto, non come centro visivo unico

### 3. Detail as dossier

Il pannello destro finance:

- evidenzia subito l'esposizione economica
- mantiene action area, segnali, contesto e timeline
- ma con gerarchia piu vicina a un dossier privato che a un pannello generico

### 4. Monetary formatting centralized

`workspace-ui.ts` introduce `formatFinanceAmount()`:

- una sola regola locale per la resa EUR
- nessuna logica duplicata tra card e detail

### 5. Detail action as real navigation affordance

Il bottone `Dettaglio` nella ledger row:

- non e piu solo un alias visivo della selezione riga
- sui layout stacked porta attivamente il viewport al pannello dettaglio
- mantiene la semantica di dossier senza introdurre routing o URL-state aggiuntivo

## Verification

- `npm --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceCaseCard.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/components/workspace/workspace-ui.ts"`

## Residual risks

- la queue resta bucketed e non e ancora un ledger unico con colonne persistenti cross-section
- la validazione finale del tono visivo richiede review headful in browser
- se questo linguaggio viene approvato, il prossimo passo corretto e rifinire solo `Rinnovi & Incassi`, non propagarlo automaticamente agli altri workspace
