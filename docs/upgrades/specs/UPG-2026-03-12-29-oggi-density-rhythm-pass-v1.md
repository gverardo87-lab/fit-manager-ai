# UPG-2026-03-12-29 - Oggi Density Rhythm Pass v1

## Metadata

- Upgrade ID: `UPG-2026-03-12-29`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Oggi Runtime`
- Priority: `medium`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

Dopo i pass architetturali sul workspace, i due componenti realmente visibili di `/oggi` avevano ancora un margine netto di miglioramento non sul "look", ma sulla disciplina visiva:

- densita'
- type scale
- shell rhythm

I punti critici erano:

- header e group spacing della timeline ancora leggermente alti;
- righe sessione con piu' aria del necessario;
- `OggiCommandCenter` ancora troppo verticale in padding, gap, tile depth e breakpoint della composizione laterale.

## Decision

Pass PRO+ strettamente limitato a:

- compattare ritmo, padding e altezze percepite;
- rendere la type scale piu' gerarchica e meno dispersiva;
- ridurre la verticalita' del command center senza cambiare grammatica, palette o page promise.

Nessuna nuova superficie, nessun nuovo colore, nessuna nuova grammatica locale.

## Changes

### `OggiTimeline.tsx`

- header piu' compatto e meno alto
- group labels e counters piu' densi
- `TimelineRow` piu' stretta in gap, padding, colonna oraria e chip
- empty state alleggerito

### `OggiCommandCenter.tsx`

- ridotti outer padding, gap verticali e altezze dei blocchi
- type scale riallineata per titolo, copy, tile e helper text
- `ContextTile` e `PrepNotesField` piu' compatti
- composizione laterale anticipata a `xl` per ridurre altezza su desktop largo
- sezioni `Da verificare adesso` e `Contesto seduta` rese piu' serrate senza cambiare contenuto

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/workspace/OggiTimeline.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `git diff --check`

## Residual Risks

- Il pass migliora molto la densita' su desktop e desktop largo, ma il ritmo complessivo della route resta ancora condizionato dalla shell di pagina e da `OggiHero`.
- Il prossimo collo di bottiglia non e' piu' la spaziatura interna dei due componenti, ma la coerenza di densita' cross-surface tra `OggiHero`, `OggiTimeline` e `OggiCommandCenter`.
