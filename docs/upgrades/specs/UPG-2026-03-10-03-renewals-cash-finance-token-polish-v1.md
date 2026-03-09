# UPG-2026-03-10-03 - Rinnovi & Incassi finance token polish v1

## Summary

Rifinitura dei token visuali finance-native del workspace `Rinnovi & Incassi`:

- badge `case kind` e `severity` separati dal lessico shared del workspace
- micro-pill e chip del dossier riallineati alla palette `pearl + petrol + clay`
- eliminazione dei toni `rose/amber/system default` che mantenevano la pagina in una grammatica visiva troppo generica

## Goal

Portare la surface finance verso un linguaggio piu coerente e premium senza:

- cambiare logica runtime
- cambiare query
- cambiare struttura della pagina

## Scope

### Included

- `frontend/src/components/workspace/workspace-ui.ts`
- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`

### Excluded

- nessun cambio backend
- nessun cambio al workspace `Oggi`
- nessun redesign addizionale del layout

## Design decisions

### 1. Finance-specific semantic badges

`payment_overdue`, `payment_due_soon`, `contract_renewal_due` e `recurring_expense_due` usano ora badge dedicati:

- piu editoriali
- meno saturi
- coerenti con il tono professionale chiaro della pagina

### 2. Severity non piu system-like

Le severity `critical/high/medium/low` nel workspace finance abbandonano:

- rose aggressivo
- amber standard
- blue generico

e passano a una scala piu adulta:

- clay per criticita
- ochre per alta priorita
- petrol per media
- taupe/slate per bassa

### 3. Micro-token coerenti nel dossier

I piccoli elementi del pannello destro ora condividono token dedicati:

- pill neutre per tempo/scadenza
- chip contesto piu caldi e meno “UI kit”
- signal card piu sottili e integrate

## Verification

- `npm --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/components/workspace/workspace-ui.ts"`

## Residual risks

- il lessico cromatico finance e ora coerente, ma se la page dovesse ancora risultare “vecchia” il problema residuo non sara nei token: sara nella grammatica strutturale `queue + detail`
- i componenti shared restano inevitabilmente doppi (`default` vs finance); bisogna evitare che il variant finance si allarghi ad altre surface senza una decisione esplicita
