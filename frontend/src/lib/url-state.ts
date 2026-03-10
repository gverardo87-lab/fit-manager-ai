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

// ── Back navigation (centralizzato) ──

/**
 * Risolve il parametro `?from=` in href + label per la back navigation.
 *
 * Ogni pagina che riceve link con `?from=X` chiama questa funzione
 * per determinare dove tornare. Aggiungere nuovi valori QUI — un solo posto.
 *
 * Valori supportati:
 *   - Letterali: "dashboard", "oggi", "monitoraggio", "allenamenti", "schede"
 *   - Compositi: "clienti-{id}", "monitoraggio-{id}", "scheda-{id}"
 *
 * @param options.tab — tab da aprire sulla pagina destinazione (es. "schede", "contratti")
 */
export interface BackNavigation {
  href: string;
  label: string;
}

const SIMPLE_BACK_ROUTES: Record<string, BackNavigation> = {
  dashboard: { href: "/", label: "Torna alla dashboard" },
  oggi: { href: "/oggi", label: "Torna a Oggi" },
  monitoraggio: { href: "/clienti/myportal", label: "Torna a Monitoraggio" },
  allenamenti: { href: "/allenamenti", label: "Torna a Monitoraggio Allenamenti" },
  schede: { href: "/schede", label: "Torna alle schede" },
};

export function resolveBackNavigation(
  fromParam: string | null | undefined,
  fallback: BackNavigation,
  options?: { tab?: string },
): BackNavigation {
  if (!fromParam) return fallback;

  // Simple page literals
  const simple = SIMPLE_BACK_ROUTES[fromParam];
  if (simple) return simple;

  // Composite: clienti-{id}
  if (fromParam.startsWith("clienti-")) {
    const id = fromParam.slice(8);
    const tab = options?.tab;
    return {
      href: `/clienti/${id}${tab ? `?tab=${tab}` : ""}`,
      label: "Torna al profilo cliente",
    };
  }

  // Composite: monitoraggio-{id}
  if (fromParam.startsWith("monitoraggio-")) {
    const id = fromParam.slice(13);
    return { href: `/monitoraggio/${id}`, label: "Torna a Monitoraggio" };
  }

  // Composite: scheda-{id}
  if (fromParam.startsWith("scheda-")) {
    const id = fromParam.slice(7);
    return { href: `/schede/${id}`, label: "Torna alla scheda" };
  }

  return fallback;
}

/**
 * Appende `?from=X` a un href, gestendo correttamente href con query params esistenti.
 */
export function appendFromParam(href: string, from: string): string {
  return href.includes("?") ? `${href}&from=${from}` : `${href}?from=${from}`;
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
