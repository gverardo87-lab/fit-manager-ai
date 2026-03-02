// src/hooks/useUnsavedChanges.ts
/**
 * Hook centralizzato per protezione dati non salvati.
 *
 * 2 livelli di difesa:
 * 1. beforeunload — avviso su chiusura tab / refresh / navigazione esterna
 * 2. Draft sessionStorage — salvataggio bozza automatico, recuperabile al rientro
 *
 * Uso base (solo beforeunload):
 *   useUnsavedChanges({ dirty: isDirty });
 *
 * Uso con draft:
 *   useUnsavedChanges({ dirty: isDirty, draftKey: `scheda-${id}`, draftData: sessions });
 *   // Al mount: const saved = loadDraft<MyType>(`scheda-${id}`);
 *   // Dopo save: clearDraft(`scheda-${id}`);
 */

import { useEffect, useRef } from "react";

const DRAFT_PREFIX = "draft::";

// ── Draft API (sessionStorage) ──

/** Salva bozza in sessionStorage. Silenzioso se storage pieno. */
export function saveDraft<T>(key: string, data: T): void {
  try {
    sessionStorage.setItem(
      DRAFT_PREFIX + key,
      JSON.stringify({ data, ts: Date.now() }),
    );
  } catch {
    // sessionStorage pieno — graceful degradation
  }
}

/** Carica bozza da sessionStorage. Ritorna null se non presente o corrotta. */
export function loadDraft<T>(key: string): { data: T; ts: number } | null {
  try {
    const raw = sessionStorage.getItem(DRAFT_PREFIX + key);
    if (!raw) return null;
    return JSON.parse(raw) as { data: T; ts: number };
  } catch {
    return null;
  }
}

/** Rimuove bozza da sessionStorage. */
export function clearDraft(key: string): void {
  try {
    sessionStorage.removeItem(DRAFT_PREFIX + key);
  } catch {
    // ignore
  }
}

// ── Hook ──

interface UseUnsavedChangesOptions<T> {
  /** Il componente ha modifiche non salvate? */
  dirty: boolean;
  /** Chiave per draft sessionStorage (opzionale). Se omessa, solo beforeunload. */
  draftKey?: string;
  /** Dato da salvare come bozza. Auto-save quando dirty + draftKey presenti. */
  draftData?: T;
}

export function useUnsavedChanges<T>({
  dirty,
  draftKey,
  draftData,
}: UseUnsavedChangesOptions<T>): void {
  // Ref per evitare closure stale nel listener
  const dirtyRef = useRef(dirty);
  dirtyRef.current = dirty;

  // Livello 1: beforeunload (chiusura tab / refresh)
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirtyRef.current) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, []);

  // Livello 2: auto-save draft quando dirty + dati cambiano
  useEffect(() => {
    if (draftKey && draftData !== undefined && dirtyRef.current) {
      saveDraft(draftKey, draftData);
    }
  }, [draftKey, draftData]);
}
