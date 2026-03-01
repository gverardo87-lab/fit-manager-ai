// src/lib/url-state.ts
/**
 * Utility per persistere lo stato dei filtri attraverso la navigazione.
 *
 * Problema: Next.js 14.1+ intercetta pushState/replaceState e potrebbe
 * normalizzare l'URL durante la back-navigation, perdendo i search params.
 * Né `useSearchParams()` né `window.location.search` sono affidabili al
 * momento del mount del componente dopo un browser-back.
 *
 * Soluzione: **sessionStorage come fonte primaria** per il restore dei filtri.
 * L'URL viene aggiornato per feedback visivo ma non è la fonte di verità.
 *
 * Pattern per ogni pagina:
 *   INIT:  loadFilters("esercizi") ?? parseFromUrl()
 *   WRITE: saveFilters("esercizi", state) + syncUrlParams(pathname, params)
 */

// ── SessionStorage (fonte primaria) ──

/**
 * Salva lo stato filtri in sessionStorage (sopravvive a navigazione e remount).
 */
export function saveFilters(
  pageKey: string,
  state: Record<string, unknown>,
): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(`filters:${pageKey}`, JSON.stringify(state));
}

/**
 * Carica lo stato filtri da sessionStorage.
 * Ritorna null se non presente o non parsabile.
 */
export function loadFilters(
  pageKey: string,
): Record<string, unknown> | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(`filters:${pageKey}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// ── URL (feedback visivo) ──

/**
 * Legge i search params dall'URL reale del browser.
 * Usato come fallback se sessionStorage è vuoto (primo accesso, link diretto).
 */
export function getUrlParams(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

/**
 * Scrive i search params nell'URL per feedback visivo.
 * Preserva `history.state` per non rompere la navigazione interna di Next.js.
 */
export function syncUrlParams(
  pathname: string,
  params: URLSearchParams,
): void {
  if (typeof window === "undefined") return;
  const qs = params.toString();
  const url = `${pathname}${qs ? `?${qs}` : ""}`;
  window.history.replaceState(window.history.state, "", url);
}
