# MANIFESTO.md - FitManager AI Studio

Questo documento contiene la verita' di prodotto che non deve cambiare a ogni microstep.

## Missione

FitManager vuole essere il CRM locale di riferimento per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Gestisce salute, progressione e denaro di persone reali: il prodotto deve trasmettere fiducia prima ancora che feature density.

## Promesse di prodotto

- Locale prima di tutto: dati sul PC del professionista, non dipendenza strutturale dal cloud.
- Privacy-first: dati clinici e finanziari trattati come sensibili.
- Determinismo: i flussi critici devono essere spiegabili, auditabili e prevedibili.
- Italiano nativo: linguaggio, messaggi e workflow pensati per il contesto italiano.
- Continuita' operativa: il CRM core deve restare usabile anche senza AI e anche con connettivita' limitata.

## Posizionamento

FitManager non compete come "altro SaaS generico per coach".
Il suo vantaggio e' l'unione di:

- CRM operativo per chinesiologi, personal trainer e professionisti fitness a P.IVA
- attenzione clinica/scientifica deterministica e dimostrabile
- gestione finance coerente
- installazione locale e supportabile

## Principi UX

- Action-first: ogni pagina deve aiutare a decidere o fare qualcosa, non solo mostrare dati.
- Gerarchia chiara: critico, warning e informativo non possono sembrare equivalenti.
- Zero frizione gratuita: loading, error ed empty state devono essere espliciti.
- Fiducia visiva: tono professionale, italiano curato, niente interfacce che sembrano prototipi.
- Uso reale: desktop e tablet/mobile devono restare praticabili senza distruggere l'identita' della pagina.

## Vincoli strutturali

- Nessun compromesso su ownership, audit e privacy.
- Dati persistenti in `data/`.
- AI solo come capability opzionale, mai come prerequisito del CRM.
- Le feature launch-critical valgono piu' delle macro-feature accessorie.

## Visual Identity

**Palette:** teal come accento primario — oklch hue 170 (`--primary` in globals.css). Stone/zinc come neutri (light/dark). Nessun blue, purple o altri accent.

**Segnali cromatici — regola del singolo colore:**
- Una sola superficie colorata per componente. Il resto e' sempre neutral.
- Toni ammessi: `neutral` (default), `teal` (positivo/pronto), `amber` (attenzione), `red` (critico/bloccato).
- Il colore vive nel testo o nel dot, non in superfici multiple.
- Chip informativi: sempre `tone: "neutral"`. Il badge stato e' l'unico elemento cromatico.

**Design system:** `surface-role.ts` — `surfaceRoleClassName` (role + tone) e `surfaceChipClassName` (tone + emphasis).
Roles: `page`, `hero`, `signal`, `context`, `dossier`, `chart`. Mai classi Tailwind colore inline se esiste un role.

**Tipografia:** scala rigorosa — label 8-9px uppercase tracking wide, valori 11-13px bold, titoli 20px extrabold.
Font: Inter (sans) + JetBrains Mono (mono). Nessun serif.

**Motion:** `usePageReveal()` per staggered fade-in + slide-up al caricamento pagina (delay incrementale per blocchi).
AnimatedNumber per counter. Nessuna animazione decorativa che ritarda l'uso.

**LogoIcon:** SVG custom (onda + chart + foglia) in `components/ui/logo-icon.tsx`. Non modificare proporzioni o path.

## Regola pratica

Se una scelta aumenta complessita' documentale o runtime ma non migliora velocita operativa,
affidabilita', privacy o supportabilita', va respinta.
