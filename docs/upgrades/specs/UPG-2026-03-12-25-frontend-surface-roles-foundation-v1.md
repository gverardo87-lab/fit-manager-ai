# UPG-2026-03-12-25 - Frontend Surface Roles Foundation

## Metadata

- Upgrade ID: `UPG-2026-03-12-25`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Visual System + Workspace UX`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

L'audit del frontend ha mostrato una base buona ma incompleta:

- `globals.css` e le primitive `components/ui` sono solide;
- molte superfici prodotto premium o operative si stilizzano ancora localmente nei TSX;
- manca un layer intermedio autorevole tra token/primitives e pagine.

Questo microstep introduce quel layer minimo senza rifare il frontend.

## Decision

Il layer intermedio vive in due punti soltanto:

1. `frontend/src/app/globals.css`
   - definisce i recipe visivi condivisi, sopra i token root e senza duplicarli
2. `frontend/src/components/ui/surface-role.ts`
   - espone il path di consumo ergonomico via helper class-variance-authority

Scelta architetturale:

- ricette visive centralizzate in CSS, perche' `globals.css` e' gia la root authority runtime
- composizione leggera in TS, per evitare stringhe classi sparse e rendere l'adozione semplice

## Surface Roles Introduced

- `page`
- `hero`
- `dossier`
- `context`
- `signal`
- `chart`
- `semantic chip` con toni `neutral / teal / amber / red`

Questi ruoli assorbono:

- border/background/surface logic
- radius condivisi
- ombra/elevazione
- toni visivi riusabili

Non assorbono:

- semantica business
- layout specifico di pagina
- copy
- ranking o logica operativa

## Pilot Adoption

Pilota applicato a:

- `frontend/src/components/workspace/OggiHero.tsx`
- `frontend/src/components/workspace/OggiCommandCenter.tsx`

Obiettivo del pilota:

- dimostrare che il layer regge una superficie operativa reale
- togliere gradienti, `oklch()` e `style={{...}}` locali dai due componenti piu bespoke di `/oggi`

## Outcome

- i due componenti pilota consumano ora surface roles condivisi
- CTA principali tornano su primitive `Button`
- i chip di stato/tempo usano il nuovo ruolo condiviso
- `OggiHero` e `OggiCommandCenter` scendono a `0` inline style, `0` `oklch()`, `0` gradienti locali

## Verification

- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run lint -- "src/components/ui/surface-role.ts" "src/components/workspace/OggiHero.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\\Program Files\\nodejs\\npm.cmd --prefix frontend run build`
- `git diff --check`

## Residual Risks

- il layer copre solo superfici prodotto, non ancora CTA variants o chart shells reali
- `workspace-ui.ts` continua a mescolare semantica dominio e toni visuali per altri workspace
- altre isole locali (`clienti`, `dashboard`, `agenda`) restano fuori da questo microstep
