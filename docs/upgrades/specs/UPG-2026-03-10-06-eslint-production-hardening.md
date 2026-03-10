# UPG-2026-03-10-06 — ESLint Production Hardening

**Date**: 2026-03-10
**Area**: Frontend
**Type**: Production Hardening
**Impact**: High
**Risk**: Low (solo fix lint, zero cambio logica business)
**Branch**: `codex_02`
**Commit**: `e08176d`
**Status**: done

---

## Sommario

Eliminazione sistematica di tutti gli errori ESLint (29) e della quasi totalita dei warning (57 → 5)
nel frontend Next.js 16 + React 19. Sprint di chiusura pre-lancio per portare il codebase
a standard production-clean.

## Risultati

| Metrica | Prima | Dopo |
|---------|-------|------|
| Errori ESLint | 29 | 0 |
| Warning ESLint | 57 | 5 |
| File modificati | — | 45 |
| Logica business modificata | — | Zero |

### 5 Warning Residui (non-actionable)

Tutti `react-hooks/incompatible-library` da `react-hook-form` `watch()`.
React Compiler non puo auto-memoizzare `watch()` — warning informativo,
non un bug. Non risolvibile senza rimuovere react-hook-form.

## Categorie di Fix

### 1. Rules-of-Hooks (3 errori)
Hook chiamati dopo early return — violazione dell'ordine costante React.
- `ProjectionChart.tsx` — useMemo/useCallback spostati prima del return
- `WeeklyPulse.tsx` — useMemo spostato prima del return

### 2. Ref-During-Render (5 errori)
`ref.current` letto/scritto durante il render (vietato in React 19).
- `useBuilderState.ts` — scrittura ref spostata in useEffect
- `AnatomicalMuscleMap.tsx` — ResizeObserver + state per container width

### 3. setState-in-Effect (4 errori)
`setState` sincrono dentro useEffect causa render a cascata.
- `BuilderSaveBar.tsx` — setTimeout(fn, 0)
- `HealthScoreRing.tsx` — setTimeout(fn, 0)
- `AuthGuard.tsx` — useState initializer per SSR guard
- `schede/[id]/page.tsx` — variabili stabili estratte

### 4. React-Compiler (5 errori)
Violazioni specifiche del React Compiler (memoizzazione automatica).
- `schede/[id]/page.tsx` — ref rimosso da deps, variabili stabili

### 5. Unescaped-Entities (12 errori)
Caratteri non escaped in JSX (apostrofi e accenti italiani).
- 6 file con `&egrave;`, `&agrave;`, `&apos;`, `&ograve;`

### 6. Exhaustive-Deps (8 warning)
Dipendenze mancanti in useMemo — array instabili da `data?.items ?? []`.
- 6 file: wrappati in `useMemo(() => data?.items ?? [], [data])`
- `ForecastTab.tsx` — rimossa dipendenza `timeline` non usata nel body

### 7. Unused-Vars (30+ warning)
Import inutilizzati, variabili mai usate, prop non consumate.
- Configurazione `eslint.config.mjs`: aggiunta regola `@typescript-eslint/no-unused-vars`
  con `argsIgnorePattern: "^_"`, `varsIgnorePattern: "^_"`, `destructuredArrayIgnorePattern: "^_"`
- ~25 file: rimozione import morti, prefisso `_` per prop intenzionalmente unused

### 8. No-Img-Element (3 warning)
`<img>` senza `next/image` — eslint-disable per immagini base64 in export.

### 9. No-Unused-Expressions (1 warning)
`expect(x).toBeUndefined` senza `()` in test — corretto.

## File Chiave Modificati

- `frontend/eslint.config.mjs` — regola `@typescript-eslint/no-unused-vars`
- `frontend/src/app/(dashboard)/schede/[id]/page.tsx` — react-compiler + setState
- `frontend/src/components/workouts/AnatomicalMuscleMap.tsx` — ResizeObserver
- `frontend/src/hooks/useBuilderState.ts` — ref in useEffect
- `frontend/src/components/layout/CommandPalette.tsx` — useMemo stabilizzazione
- `frontend/src/app/(dashboard)/esercizi/page.tsx` — useMemo stabilizzazione
- `frontend/src/components/clients/ProgressiTab.tsx` — useMemo stabilizzazione

## Verifica

```bash
bash tools/scripts/check-all.sh  # ruff check + next build — green
```

## Lezioni Apprese

1. **`data?.items ?? []` crea nuova referenza a ogni render** — destabilizza useMemo deps.
   Fix: wrappare in `useMemo(() => data?.items ?? [], [data])`.
2. **React 19 vieta `ref.current` durante render** — usare ResizeObserver + state.
3. **`setState` sincrono in useEffect** causa render a cascata — `setTimeout(fn, 0)`.
4. **Hook dopo early return** — violazione rules-of-hooks. Spostare TUTTI gli hook prima.
5. **Prefisso `_` per unused vars** — richiede configurazione esplicita in eslint.config.mjs.
