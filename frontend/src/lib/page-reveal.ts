// lib/page-reveal.ts
/**
 * Animazione di ingresso pagina — fade-in + slide-up con stagger.
 *
 * Pattern:
 *   const { ready, revealClass, revealStyle } = usePageReveal();
 *
 *   <div className={revealClass(0)}>Header</div>
 *   <div className={revealClass(40)}>KPI</div>
 *
 * Rispetta `prefers-reduced-motion`.
 */

import { useEffect, useState } from "react";

/** CSS class per reveal: fade-in + translateY con transition. */
export function getRevealClass(ready: boolean, extraClass?: string): string {
  const base = `transform-gpu transition-[opacity,transform] duration-500 ease-out motion-reduce:transform-none motion-reduce:transition-none`;
  const state = ready
    ? "translate-y-0 opacity-100"
    : "translate-y-1 opacity-0 motion-reduce:translate-y-0 motion-reduce:opacity-100";
  return extraClass ? `${base} ${state} ${extraClass}` : `${base} ${state}`;
}

/** Style con transitionDelay per stagger. */
export function getRevealStyle(delayMs: number): React.CSSProperties {
  return { transitionDelay: `${delayMs}ms` };
}

/**
 * Hook per animazione di ingresso pagina.
 *
 * Ritorna:
 * - `ready`: booleano che diventa true dopo il primo frame
 * - `revealClass(delayMs, extra?)`: classe CSS per l'elemento
 * - `revealStyle(delayMs)`: style con delay
 */
export function usePageReveal() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const rafId = window.requestAnimationFrame(() => setReady(true));
    return () => window.cancelAnimationFrame(rafId);
  }, []);

  return {
    ready,
    revealClass: (delayMs: number, extraClass?: string) =>
      getRevealClass(ready, extraClass),
    revealStyle: (delayMs: number) => getRevealStyle(delayMs),
  };
}
