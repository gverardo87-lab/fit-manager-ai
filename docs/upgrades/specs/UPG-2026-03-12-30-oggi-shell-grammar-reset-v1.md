# UPG-2026-03-12-30 - Oggi Shell Grammar Reset v1

## Metadata

- Upgrade ID: `UPG-2026-03-12-30`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Oggi Runtime`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo il cleanup architetturale e i pass di densita', `/oggi` soffriva ancora di un bug di prodotto piu' profondo:

- timeline sticky a sinistra;
- hero con spotlight duplicata;
- command center a destra come dettaglio pesante;
- percezione finale `lista + dettaglio` con tono troppo dossier/clinico.

Questo schema era ancora troppo vicino a:

- record viewer;
- gestionale clinico-amministrativo;
- master-detail retro.

Non era la grammatica giusta per chinesiologi, personal trainer e professionisti fitness a P.IVA.

## Decision

La route passa da `lista + dettaglio` a una grammatica in tre atti:

1. `day brief`
2. `focus attivo`
3. `flusso della giornata`

Decisioni chiave:

- `OggiHero` smette di comportarsi come una seconda scheda cliente e diventa briefing operativo della giornata;
- `OggiCommandCenter` resta l'unico focus della seduta attiva e viene rinominato/composto come stage, non come dossier subordinato;
- `OggiTimeline` smette di essere una rail sticky a righe e diventa una board di flusso con fasce `da sbloccare / in linea / altri slot`;
- la shell pagina smette di basarsi su due colonne concorrenti e torna a una progressione verticale controllata: overview breve -> stage dominante -> flow board.

## Changes

### `page.tsx`

- rimossa la shell `timeline sticky a sinistra + hero/command center a destra`
- nuova sequenza: `OggiHero` -> alert non bloccante -> `OggiCommandCenter` -> `OggiTimeline`
- rimossi gli ultimi alert/error container con styling inline bespoke
- il runtime di `/oggi` non importa piu' `oggi-workspace.css`

### `OggiHero.tsx`

- eliminata la spotlight card della seduta prioritaria
- l'hero diventa un `day brief` con direzione del momento, supporto giornata e KPI operativi
- ridotta la duplicazione con il focus stage

### `OggiCommandCenter.tsx`

- la seduta selezionata resta il focus unico della pagina
- copy e gerarchia spostati da tono `scheda/record` a tono `focus attivo`
- empty/internal state riallineati alla nuova grammatica

### `OggiTimeline.tsx`

- eliminata la timeline a righe sticky con colonna oraria da rail
- introdotta una board `flusso della giornata` con tre fasce compatte
- le sedute vengono lette come regia operativa, non come elenco record
- selezione e ranking restano invariati nel comportamento, ma cambiano shell e percezione

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiHero.tsx" "src/components/workspace/OggiTimeline.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- grep mirato su `oklch\\(|linear-gradient|#[0-9A-Fa-f]{3,8}|shadow-\\[|oggi-` nei 4 file runtime toccati -> nessuna occorrenza
- `git diff --check`

## Residual Risks

- La grammatica nuova rompe il master-detail retro, ma il tuning finale di viewport/breakpoint richiede ancora una review browser reale.
- `OggiCommandCenter` resta il blocco visivo piu' alto della route; il prossimo pass utile non e' un altro redesign, ma un hardening mirato su `densita' + shell rhythm` cross-surface se emergono differenze su schermi reali.
