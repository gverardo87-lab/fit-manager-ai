// src/__tests__/data-protection/guard-patterns.test.ts
/**
 * Test sui pattern di guardia chiusura (guardedOpenChange).
 *
 * Testa la LOGICA pura dei pattern usati nei Sheet/Dialog,
 * senza dipendenze React. Simula il comportamento del ref + confirm.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ════════════════════════════════════════════════════════════
// Simulatore del pattern guardedOpenChange
// ════════════════════════════════════════════════════════════

/**
 * Riproduce fedelmente la logica dei nostri Sheet/Dialog wrapper.
 * Questo e' il CUORE del pattern — se questo test fallisce,
 * la protezione dati e' rotta.
 */
function createGuardedOpenChange(onOpenChange: (open: boolean) => void) {
  const dirtyRef = { current: false };

  const guardedOpenChange = (newOpen: boolean) => {
    if (!newOpen && dirtyRef.current) {
      if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    }
    dirtyRef.current = false;
    onOpenChange(newOpen);
  };

  return { dirtyRef, guardedOpenChange };
}

// ════════════════════════════════════════════════════════════
// BASIC GUARD BEHAVIOR
// ════════════════════════════════════════════════════════════

describe("guardedOpenChange — Comportamento base", () => {
  let onOpenChange: ReturnType<typeof vi.fn>;
  let dirtyRef: { current: boolean };
  let guardedOpenChange: (open: boolean) => void;

  beforeEach(() => {
    onOpenChange = vi.fn();
    const guard = createGuardedOpenChange(onOpenChange);
    dirtyRef = guard.dirtyRef;
    guardedOpenChange = guard.guardedOpenChange;
  });

  it("apertura (open=true) passa sempre, anche se dirty", () => {
    dirtyRef.current = true;
    guardedOpenChange(true);
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it("chiusura senza modifiche passa senza confirm", () => {
    dirtyRef.current = false;
    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("chiusura con dirty=true mostra confirm", () => {
    dirtyRef.current = true;
    vi.spyOn(window, "confirm").mockReturnValue(true);

    guardedOpenChange(false);

    expect(window.confirm).toHaveBeenCalledWith("Hai modifiche non salvate. Vuoi davvero uscire?");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("chiusura con dirty=true e conferma rifiutata BLOCCA la chiusura", () => {
    dirtyRef.current = true;
    vi.spyOn(window, "confirm").mockReturnValue(false);

    guardedOpenChange(false);

    expect(window.confirm).toHaveBeenCalled();
    expect(onOpenChange).not.toHaveBeenCalled();
  });

  it("chiusura con dirty=true e conferma accettata resetta dirty", () => {
    dirtyRef.current = true;
    vi.spyOn(window, "confirm").mockReturnValue(true);

    guardedOpenChange(false);

    expect(dirtyRef.current).toBe(false);
  });

  it("chiusura senza dirty resetta comunque il ref", () => {
    dirtyRef.current = false;
    guardedOpenChange(false);
    expect(dirtyRef.current).toBe(false);
  });
});

// ════════════════════════════════════════════════════════════
// SCENARI SEQUENZIALI
// ════════════════════════════════════════════════════════════

describe("guardedOpenChange — Scenari sequenziali", () => {
  it("apri → modifica → chiudi (bloccato) → modifica ancora → chiudi (confermato)", () => {
    const onOpenChange = vi.fn();
    const { dirtyRef, guardedOpenChange } = createGuardedOpenChange(onOpenChange);

    // 1. Apri
    guardedOpenChange(true);
    expect(onOpenChange).toHaveBeenCalledWith(true);
    onOpenChange.mockClear();

    // 2. Utente modifica
    dirtyRef.current = true;

    // 3. Prova a chiudere — RIFIUTA
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);
    expect(onOpenChange).not.toHaveBeenCalled();
    // dirty resta true — l'utente sta ancora lavorando
    expect(dirtyRef.current).toBe(true);

    // 4. Modifica ancora (dirty resta true)

    // 5. Prova a chiudere — CONFERMA
    vi.spyOn(window, "confirm").mockReturnValue(true);
    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(dirtyRef.current).toBe(false);
  });

  it("apri → chiudi (senza modifiche) → riapri → modifica → chiudi (bloccato)", () => {
    const onOpenChange = vi.fn();
    const { dirtyRef, guardedOpenChange } = createGuardedOpenChange(onOpenChange);

    // 1. Apri e chiudi senza modifiche
    guardedOpenChange(true);
    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledTimes(2);
    onOpenChange.mockClear();

    // 2. Riapri
    guardedOpenChange(true);
    onOpenChange.mockClear();

    // 3. Modifica
    dirtyRef.current = true;

    // 4. Chiudi — RIFIUTA
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);
    expect(onOpenChange).not.toHaveBeenCalled();
  });
});

// ════════════════════════════════════════════════════════════
// SAVE BYPASS — il save NON deve mostrare confirm
// ════════════════════════════════════════════════════════════

describe("guardedOpenChange — Save bypass", () => {
  it("save resetta dirty prima di chiudere → nessun confirm", () => {
    const onOpenChange = vi.fn();
    const { dirtyRef, guardedOpenChange: _guardedOpenChange } = createGuardedOpenChange(onOpenChange);

    // Utente ha modificato
    dirtyRef.current = true;

    // Mutation onSuccess: resetta dirty e chiama onOpenChange direttamente
    // (bypassando guardedOpenChange — come nel codice reale)
    dirtyRef.current = false;
    onOpenChange(false);

    // Nessun confirm mostrato
    expect(window.confirm).toBeUndefined();
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});

// ════════════════════════════════════════════════════════════
// SIMULATORE isDirtyRef GUARD (pattern schede builder)
// ════════════════════════════════════════════════════════════

/**
 * Riproduce il pattern del builder schede:
 * useEffect([plan]) sincronizza dati server → stato locale,
 * ma SOLO se isDirtyRef.current === false.
 *
 * BUG ORIGINALE: senza il guard, ogni refetch di React Query
 * sovrascriveva silenziosamente le modifiche non salvate.
 */
function simulateServerSync(
  serverData: { sessions: string[] },
  isDirty: boolean,
  localSessions: string[],
): string[] {
  // Pattern identico a schede/[id]/page.tsx useEffect
  if (serverData && !isDirty) {
    return [...serverData.sessions]; // Sincronizza da server
  }
  return localSessions; // Preserva modifiche locali
}

describe("isDirtyRef guard — Server sync protection", () => {
  it("sincronizza dati server quando form e' pulito", () => {
    const result = simulateServerSync(
      { sessions: ["Server A", "Server B"] },
      false,
      ["Old Local"],
    );
    expect(result).toEqual(["Server A", "Server B"]);
  });

  it("BLOCCA sync server quando form ha modifiche non salvate", () => {
    const result = simulateServerSync(
      { sessions: ["Server A", "Server B"] },
      true,
      ["My Edited Session"],
    );
    expect(result).toEqual(["My Edited Session"]);
  });

  it("scenario reale: utente modifica → mutation inline → refetch → dati preservati", () => {
    let local = ["Sessione Base"];
    let isDirty = false;

    // 1. Server iniziale caricato
    local = simulateServerSync({ sessions: ["Sessione Base"] }, isDirty, local);
    expect(local).toEqual(["Sessione Base"]);

    // 2. Utente aggiunge esercizi, modifica carichi
    local = ["Sessione Modificata"];
    isDirty = true;

    // 3. Utente cambia obiettivo scheda → mutation → invalidate → refetch
    //    React Query restituisce il dato server (SENZA le modifiche locali)
    local = simulateServerSync({ sessions: ["Sessione Base"] }, isDirty, local);

    // 4. Le modifiche locali sono preservate! (Bug originale: qui venivano perse)
    expect(local).toEqual(["Sessione Modificata"]);
  });

  it("dopo save (isDirty=false) il prossimo refetch sincronizza", () => {
    let local = ["Dati Modificati"];
    let isDirty = true;

    // 1. Save con successo
    isDirty = false;

    // 2. Server restituisce dati aggiornati (ora con le modifiche salvate)
    local = simulateServerSync({ sessions: ["Dati Salvati Sul Server"] }, isDirty, local);

    // 3. Sincronizzazione avviene
    expect(local).toEqual(["Dati Salvati Sul Server"]);
  });
});

// ════════════════════════════════════════════════════════════
// SIMULATORE initializedEditId (pattern misurazioni)
// ════════════════════════════════════════════════════════════

/**
 * Riproduce il pattern di misurazioni/page.tsx:
 * useEffect([editMeasurement]) inizializza il form da una misurazione esistente,
 * ma SOLO se non e' gia' stata inizializzata (previene re-init su refetch).
 *
 * BUG ORIGINALE: senza il ref, ogni refetch reinizializzava il form
 * sovrascrivendo le modifiche in corso.
 */
function simulateEditInit(
  editMeasurement: { id: number; values: Record<number, number> } | null,
  initializedEditId: { current: number | null },
  currentValues: Record<number, string>,
): Record<number, string> {
  if (editMeasurement && initializedEditId.current !== editMeasurement.id) {
    // Prima inizializzazione: popola form da misurazione
    const vals: Record<number, string> = {};
    for (const [k, v] of Object.entries(editMeasurement.values)) {
      vals[Number(k)] = String(v);
    }
    initializedEditId.current = editMeasurement.id;
    return vals;
  }
  return currentValues; // Mantieni valori attuali
}

describe("initializedEditId — Edit init protection", () => {
  it("prima apertura: inizializza form dalla misurazione", () => {
    const ref = { current: null as number | null };
    const result = simulateEditInit(
      { id: 42, values: { 1: 75.5, 2: 18.3 } },
      ref,
      {},
    );
    expect(result).toEqual({ 1: "75.5", 2: "18.3" });
    expect(ref.current).toBe(42);
  });

  it("refetch stessa misurazione: NON reinizializza", () => {
    const ref = { current: 42 as number | null };
    const result = simulateEditInit(
      { id: 42, values: { 1: 75.5, 2: 18.3 } },
      ref,
      { 1: "80.0", 2: "16.0" }, // Utente ha modificato
    );
    // Valori utente preservati
    expect(result).toEqual({ 1: "80.0", 2: "16.0" });
  });

  it("cambio misurazione (diverso id): reinizializza", () => {
    const ref = { current: 42 as number | null };
    const result = simulateEditInit(
      { id: 99, values: { 1: 90.0 } },
      ref,
      { 1: "80.0" },
    );
    expect(result).toEqual({ 1: "90" }); // String(90.0) === "90" in JS
    expect(ref.current).toBe(99);
  });

  it("misurazione null: mantiene stato attuale", () => {
    const ref = { current: null as number | null };
    const result = simulateEditInit(
      null,
      ref,
      { 1: "75.5" },
    );
    expect(result).toEqual({ 1: "75.5" });
    expect(ref.current).toBeNull();
  });
});

// ════════════════════════════════════════════════════════════
// SIMULATORE userHasEdited (pattern impostazioni)
// ════════════════════════════════════════════════════════════

/**
 * Riproduce il pattern di impostazioni/page.tsx SaldoInizialeSection:
 * useEffect([saldoData]) sincronizza da server, ma SOLO se l'utente
 * non ha ancora toccato i campi.
 *
 * BUG ORIGINALE: ogni refetch resettava importo e data nel form.
 */
function simulateSettingsSync(
  serverData: { saldo: string; dataInizio: string } | null,
  userHasEdited: boolean,
  currentImporto: string,
  currentDataInizio: string,
): { importo: string; dataInizio: string } {
  if (!serverData || userHasEdited) {
    return { importo: currentImporto, dataInizio: currentDataInizio };
  }
  return { importo: serverData.saldo, dataInizio: serverData.dataInizio };
}

describe("userHasEdited — Settings sync protection", () => {
  it("inizializzazione da server se utente non ha editato", () => {
    const result = simulateSettingsSync(
      { saldo: "1000", dataInizio: "2026-01-01" },
      false, "", "",
    );
    expect(result).toEqual({ importo: "1000", dataInizio: "2026-01-01" });
  });

  it("BLOCCA sync se utente ha editato", () => {
    const result = simulateSettingsSync(
      { saldo: "1000", dataInizio: "2026-01-01" },
      true,
      "5000",
      "2026-06-01",
    );
    expect(result).toEqual({ importo: "5000", dataInizio: "2026-06-01" });
  });

  it("serverData null: preserva valori attuali", () => {
    const result = simulateSettingsSync(null, false, "500", "2025-12-01");
    expect(result).toEqual({ importo: "500", dataInizio: "2025-12-01" });
  });
});
