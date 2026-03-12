# UPG-2026-03-12-23 - Oggi Runtime-First Redesign

## Metadata

- Upgrade ID: `UPG-2026-03-12-23`
- Date: `2026-03-12`
- Owner: `Codex`
- Area: `Frontend Workspace UX + Runtime Product Direction`
- Priority: `high`
- Target release: `fit_launch_01`
- Status: `done`

## Why This Exists

`/oggi` era diventata un ibrido tra hero dashboard, timeline agenda, command center a quadranti
e workspace generico. La route usava dati realmente utili (`session-prep`, `workspace/today`), ma
senza una promessa unica di pagina.

## Product Decision

- Page promise: `/oggi` serve a preparare e governare le sedute di oggi.
- Unit of work dominante: la seduta di oggi da preparare o verificare prima di entrare in sala.
- Esclusioni esplicite:
  - non una dashboard riassuntiva generica
  - non un collage di card
  - non un clone di CRM sales
  - non un secondo profilo cliente

## Runtime Changes

- Il vecchio hero motivazionale viene sostituito da un header operativo compatto, con una sola CTA
  dominante sulla seduta prioritaria.
- La lista sinistra smette di essere una timeline neutra e diventa una lista sedute orientata a
  `richiedono attenzione / pronte / altri impegni`.
- Il pannello destro smette di usare 4 quadranti equivalenti e diventa una scheda pre-seduta con:
  - punti da verificare adesso
  - contesto rapido
  - note pre-seduta
  - link operativi essenziali
- I casi `workspace/today` restano solo come supporto secondario fuori seduta e non governano piu'
  la shell.
- Secondo pass UX/UI mirato: la shell passa a una composizione piu compatta gia da `lg`, le note
  pre-seduta salgono subito sotto i punti da verificare, il contesto viene accorpato e la palette
  abbandona il grigio freddo in favore di superfici piu calde e coerenti con FitManager.

## Files Touched

- `frontend/src/app/(dashboard)/oggi/page.tsx`
- `frontend/src/components/workspace/OggiHero.tsx`
- `frontend/src/components/workspace/OggiTimeline.tsx`
- `frontend/src/components/workspace/OggiCommandCenter.tsx`

## Verification

- `C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/OggiHero.tsx" "src/components/workspace/OggiTimeline.tsx" "src/components/workspace/OggiCommandCenter.tsx"`
- `C:\Program Files\nodejs\npm.cmd --prefix frontend run build`
- `git diff --check`
- review manuale degli stati `loading / empty / error`
- review manuale dei breakpoint `390px / 768px / 1024px / desktop largo` sui file toccati

## Residual Risks

1. La pagina usa ancora due sorgenti read-only (`session-prep` e `workspace/today`); il focus fuori seduta e'
   volutamente declassato, ma il doppio contratto resta.
2. Le note pre-seduta restano locali a `localStorage`; sono utili nel lavoro quotidiano ma non sono condivise.
3. La logica di priorita' delle sedute e' frontend-owned; se dovra' diventare canonica andra' spostata nel runtime.
4. Tra `lg` e `2xl` il pannello pre-seduta resta internamente su una colonna per non comprimere troppo il
   contesto; ulteriore densita' richiederebbe una shell ancora piu selettiva o nuovi dati sintetici runtime.
