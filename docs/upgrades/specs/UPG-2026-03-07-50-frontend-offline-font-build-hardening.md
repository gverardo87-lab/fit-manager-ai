# UPG-2026-03-07-50 - Frontend Offline Font Build Hardening

## Context

Il frontend era tornato build-breaker per due motivi distinti:

1. drift TypeScript su `MuscleMapPanel` / `training-science-display`;
2. dipendenza di `next build` da `next/font/google` in `src/app/layout.tsx`.

In ambiente offline o sandboxed, `next/font/google` falliva il fetch di:

- `Geist`
- `Geist Mono`
- `Caveat`

bloccando la build di produzione.

## Goal

Rendere il frontend buildabile anche senza accesso a Google Fonts, preservando la semantica delle variabili tipografiche gia' usate nei componenti.

## Scope

- `frontend/src/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/lib/training-science-display.ts`

## Implementation

### 1. Type sync locale

- `getBackendVolumeCounts()` ora accetta anche `undefined`, coerentemente con l'uso in `MuscleMapPanel`.

### 2. Font offline-safe

- rimosso `next/font/google` da `layout.tsx`;
- mantenute le stesse custom properties:
  - `--font-geist-sans`
  - `--font-geist-mono`
  - `--font-caveat`
- definite in `globals.css` con fallback locali/system-safe.

Questo evita fetch di rete in build e non richiede di cambiare i componenti che usano `font-[family-name:var(--font-caveat)]` o il mapping `--font-sans` / `--font-mono`.

## Verification

```powershell
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/layout.tsx" "src/lib/training-science-display.ts" "src/components/workouts/MuscleMapPanel.tsx"
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build
```

## Residual Risks

- Resta il warning Next 16: `middleware` deprecato in favore di `proxy`. Non blocca la build ma va pianificato come microstep separato.
- Il fallback tipografico locale non e' identico al rendering di Google Fonts; e' una scelta di affidabilita' build-first.
