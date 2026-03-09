# UPG-2026-03-10-04 - Rinnovi & Incassi return context v1

## Summary

Hardening della continuita di navigazione del workspace `Rinnovi & Incassi`:

- stato minimale della page serializzato in URL (`filter`, `case`, `waiting`)
- link rapidi decorati con `returnTo`
- pagine `contratto` e `cliente` rese consapevoli del ritorno al workspace

## Goal

Evitare la distruzione del flusso operativo quando il trainer:

- apre un contratto dal workspace finance
- naviga verso il profilo cliente dal contratto
- usa il back context-aware della pagina di destinazione

Il ritorno deve riportare al punto operativo di partenza, non alla lista clienti o a una pagina neutra.

## Scope

### Included

- `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx`
- `frontend/src/components/workspace/WorkspaceDetailPanel.tsx`
- `frontend/src/app/(dashboard)/contratti/[id]/page.tsx`
- `frontend/src/app/(dashboard)/clienti/[id]/page.tsx`
- `frontend/src/components/clients/ClientProfileHeader.tsx`

### Excluded

- nessun cambio backend
- nessun cambio ranking workspace
- nessun cambio visivo strutturale

## Design decisions

### 1. URL state minima ma sufficiente

Il workspace finance serializza solo lo stretto necessario:

- `filter`
- `case`
- `waiting`

Questo basta per ripristinare il punto di lavoro senza introdurre uno state machine piu complesso.

### 2. `returnTo` come contratto di navigazione

I link rapidi verso pagine interne del CRM aggiungono un `returnTo` relativo e sicuro.

Regole:

- solo path interni che iniziano con `/`
- niente URL esterni
- nessuna dipendenza dal browser history implicito

### 3. Destination-aware back

Le pagine `contratto` e `cliente` usano `returnTo` come priorita di back navigation:

- freccia indietro
- banner contestuale
- redirect dopo delete del contratto

### 4. Propagazione della catena

Se entro nel contratto dal workspace e poi apro il cliente:

- il contratto propaga `returnTo` al profilo cliente
- il profilo cliente puo riportarmi allo stesso workspace finance

## Verification

- `npm --prefix frontend run lint -- "src/app/(dashboard)/rinnovi-incassi/page.tsx" "src/components/workspace/WorkspaceDetailPanel.tsx" "src/app/(dashboard)/contratti/[id]/page.tsx" "src/app/(dashboard)/clienti/[id]/page.tsx" "src/components/clients/ClientProfileHeader.tsx"`

## Residual risks

- il ripristino del punto di lavoro e limitato al set minimo `filter/case/waiting`; se in futuro il workspace acquisisce piu stato locale, dovra essere esplicitamente serializzato
- altri deep-link dal profilo cliente non propagano ancora automaticamente `returnTo`; per ora il microstep chiude il percorso critico `workspace -> contratto -> cliente -> ritorno`
