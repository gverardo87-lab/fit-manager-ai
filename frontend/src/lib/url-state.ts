// src/lib/url-state.ts
/**
 * Utility per persistere lo stato dei filtri attraverso la navigazione.
 *
 * Strategia:
 * - sessionStorage salva filtri e scroll per ogni pagina
 * - La Sidebar cancella lo stato salvato onClick → navigazione fresca = default
 * - Back-nav (browser back) NON passa dalla Sidebar → stato ancora presente → ripristinato
 * - L'URL viene aggiornato per feedback visivo ma non è la fonte di verità
 *
 * Pattern per ogni pagina:
 *   INIT:  loadFilters("esercizi") ?? parseFromUrl() ?? default
 *   WRITE: saveFilters("esercizi", state) + syncUrlParams(pathname, params)
 */

// ── Pagine con filtri (usato dalla Sidebar per sapere cosa cancellare) ──

const FILTER_PAGE_KEYS: Record<string, string> = {
  "/clienti": "clienti",
  "/contratti": "contratti",
  "/cassa": "cassa",
  "/esercizi": "esercizi",
  "/schede": "schede",
  "/allenamenti": "allenamenti",
};

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

// ── Clear state (chiamato dalla Sidebar onClick) ──

/**
 * Cancella filtri e scroll salvati per una pagina.
 * Chiamato dalla Sidebar prima della navigazione → la pagina partirà da zero.
 * Accetta l'href della Sidebar (es. "/esercizi").
 */
export function clearPageState(href: string): void {
  if (typeof window === "undefined") return;
  const pageKey = FILTER_PAGE_KEYS[href];
  if (pageKey) {
    sessionStorage.removeItem(`filters:${pageKey}`);
  }
  // Cancella anche lo scroll salvato per questa rotta
  sessionStorage.removeItem(`scroll:${href}`);
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
