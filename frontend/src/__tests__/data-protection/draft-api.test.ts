// src/__tests__/data-protection/draft-api.test.ts
/**
 * Test chirurgici sulla Draft API (sessionStorage).
 *
 * Copre: salvataggio, caricamento, cancellazione, corruzione, overflow,
 * isolamento chiavi, tipi complessi, timestamp.
 */

import { describe, it, expect, vi } from "vitest";
import { saveDraft, loadDraft, clearDraft } from "@/hooks/useUnsavedChanges";

// ════════════════════════════════════════════════════════════
// BASIC CRUD
// ════════════════════════════════════════════════════════════

describe("Draft API — CRUD", () => {
  it("salva e ricarica dati primitivi", () => {
    saveDraft("test-key", { name: "Mario", age: 30 });
    const result = loadDraft<{ name: string; age: number }>("test-key");

    expect(result).not.toBeNull();
    expect(result!.data.name).toBe("Mario");
    expect(result!.data.age).toBe(30);
    expect(result!.ts).toBeGreaterThan(0);
  });

  it("loadDraft ritorna null per chiave inesistente", () => {
    expect(loadDraft("ghost-key")).toBeNull();
  });

  it("clearDraft rimuove la bozza", () => {
    saveDraft("deleteme", { x: 1 });
    expect(loadDraft("deleteme")).not.toBeNull();

    clearDraft("deleteme");
    expect(loadDraft("deleteme")).toBeNull();
  });

  it("clearDraft su chiave inesistente non fa crash", () => {
    expect(() => clearDraft("never-existed")).not.toThrow();
  });

  it("sovrascrive bozza esistente con dati nuovi", () => {
    saveDraft("overwrite", { version: 1 });
    saveDraft("overwrite", { version: 2 });

    const result = loadDraft<{ version: number }>("overwrite");
    expect(result!.data.version).toBe(2);
  });
});

// ════════════════════════════════════════════════════════════
// ISOLAMENTO CHIAVI
// ════════════════════════════════════════════════════════════

describe("Draft API — Isolamento chiavi", () => {
  it("chiavi diverse sono indipendenti", () => {
    saveDraft("scheda-1", { sessions: [1, 2] });
    saveDraft("scheda-2", { sessions: [3, 4] });

    const d1 = loadDraft<{ sessions: number[] }>("scheda-1");
    const d2 = loadDraft<{ sessions: number[] }>("scheda-2");

    expect(d1!.data.sessions).toEqual([1, 2]);
    expect(d2!.data.sessions).toEqual([3, 4]);
  });

  it("clearDraft non tocca altre chiavi", () => {
    saveDraft("keep", "data-a");
    saveDraft("remove", "data-b");

    clearDraft("remove");

    expect(loadDraft("keep")).not.toBeNull();
    expect(loadDraft("remove")).toBeNull();
  });

  it("prefisso draft:: evita collisioni con altri dati sessionStorage", () => {
    // Dato "esterno" senza prefisso
    sessionStorage.setItem("scheda-1", "non-draft-data");
    saveDraft("scheda-1", { type: "draft" });

    // Il dato esterno non viene toccato
    expect(sessionStorage.getItem("scheda-1")).toBe("non-draft-data");
    // Il draft ha il suo prefisso
    expect(sessionStorage.getItem("draft::scheda-1")).not.toBeNull();
  });
});

// ════════════════════════════════════════════════════════════
// TIPI COMPLESSI (simula dati reali schede/anamnesi)
// ════════════════════════════════════════════════════════════

describe("Draft API — Tipi complessi", () => {
  it("serializza array di oggetti annidati (sessioni scheda)", () => {
    const sessions = [
      {
        id: "s1",
        nome: "Upper Body",
        esercizi: [
          { id_esercizio: 10, nome: "Panca Piana", serie: "4", rip: "8-10", riposo: "90", carico_kg: 80 },
          { id_esercizio: 20, nome: "Rematore", serie: "3", rip: "10-12", riposo: "60", carico_kg: null },
        ],
      },
    ];

    saveDraft("scheda-builder-5", sessions);
    const loaded = loadDraft<typeof sessions>("scheda-builder-5");

    expect(loaded!.data).toHaveLength(1);
    expect(loaded!.data[0].esercizi).toHaveLength(2);
    expect(loaded!.data[0].esercizi[0].carico_kg).toBe(80);
    expect(loaded!.data[0].esercizi[1].carico_kg).toBeNull();
  });

  it("preserva null, undefined diventa null in JSON", () => {
    const data = { a: null, b: undefined, c: 0, d: "", e: false };
    saveDraft("nulls", data);
    const loaded = loadDraft<typeof data>("nulls");

    expect(loaded!.data.a).toBeNull();
    // undefined → non presente in JSON (viene omesso)
    expect(loaded!.data.b).toBeUndefined();
    expect(loaded!.data.c).toBe(0);
    expect(loaded!.data.d).toBe("");
    expect(loaded!.data.e).toBe(false);
  });

  it("preserva date come stringhe ISO", () => {
    const date = new Date("2026-03-01T10:00:00Z");
    saveDraft("dates", { created: date.toISOString() });
    const loaded = loadDraft<{ created: string }>("dates");

    expect(loaded!.data.created).toBe("2026-03-01T10:00:00.000Z");
  });
});

// ════════════════════════════════════════════════════════════
// TIMESTAMP
// ════════════════════════════════════════════════════════════

describe("Draft API — Timestamp", () => {
  it("timestamp riflette il momento del salvataggio", () => {
    const before = Date.now();
    saveDraft("ts-test", {});
    const after = Date.now();

    const loaded = loadDraft("ts-test");
    expect(loaded!.ts).toBeGreaterThanOrEqual(before);
    expect(loaded!.ts).toBeLessThanOrEqual(after);
  });

  it("aggiornamento sovrascrive il timestamp", async () => {
    saveDraft("ts-update", { v: 1 });
    const ts1 = loadDraft("ts-update")!.ts;

    // Piccolo delay per garantire timestamp diverso
    await new Promise((r) => setTimeout(r, 5));

    saveDraft("ts-update", { v: 2 });
    const ts2 = loadDraft("ts-update")!.ts;

    expect(ts2).toBeGreaterThan(ts1);
  });
});

// ════════════════════════════════════════════════════════════
// CORRUZIONE & RESILIENZA
// ════════════════════════════════════════════════════════════

describe("Draft API — Corruzione & Resilienza", () => {
  it("loadDraft gestisce JSON corrotto senza crash", () => {
    sessionStorage.setItem("draft::corrupted", "NOT{VALID}JSON!!!");
    expect(loadDraft("corrupted")).toBeNull();
  });

  it("loadDraft gestisce stringa vuota", () => {
    sessionStorage.setItem("draft::empty", "");
    expect(loadDraft("empty")).toBeNull();
  });

  it("loadDraft gestisce oggetto senza campo data", () => {
    sessionStorage.setItem("draft::partial", JSON.stringify({ ts: 123 }));
    const result = loadDraft("partial");
    // Non crasha, ritorna l'oggetto (anche se data e' undefined)
    expect(result).not.toBeNull();
  });

  it("saveDraft gestisce sessionStorage pieno (graceful degradation)", () => {
    // Mock sessionStorage.setItem che lancia QuotaExceededError
    const original = sessionStorage.setItem.bind(sessionStorage);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Quota exceeded", "QuotaExceededError");
    });

    // Non deve fare crash
    expect(() => saveDraft("full", { big: "data" })).not.toThrow();

    vi.restoreAllMocks();
  });

  it("clearDraft gestisce errore sessionStorage", () => {
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("Storage access denied");
    });

    expect(() => clearDraft("any")).not.toThrow();

    vi.restoreAllMocks();
  });

  it("loadDraft gestisce errore sessionStorage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("Storage access denied");
    });

    expect(loadDraft("any")).toBeNull();

    vi.restoreAllMocks();
  });
});

// ════════════════════════════════════════════════════════════
// SCENARI REALI — lifecycle scheda builder
// ════════════════════════════════════════════════════════════

describe("Draft API — Lifecycle scheda builder", () => {
  it("ciclo completo: save → load → modify → save → clear", () => {
    const key = "scheda-builder-42";

    // 1. Utente apre builder, inizia a modificare
    const v1 = { sessions: [{ nome: "A", esercizi: [] }] };
    saveDraft(key, v1);

    // 2. Browser refresha (beforeunload) → rientra
    const loaded = loadDraft<typeof v1>(key);
    expect(loaded!.data.sessions).toHaveLength(1);

    // 3. Continua a modificare
    const v2 = { sessions: [...loaded!.data.sessions, { nome: "B", esercizi: [] }] };
    saveDraft(key, v2);

    // 4. Verifica aggiornamento
    const loaded2 = loadDraft<typeof v2>(key);
    expect(loaded2!.data.sessions).toHaveLength(2);

    // 5. Salva con successo → pulisce draft
    clearDraft(key);
    expect(loadDraft(key)).toBeNull();
  });

  it("draft sopravvive a operazioni su altre chiavi", () => {
    saveDraft("scheda-1", { keep: true });
    saveDraft("scheda-2", { temporary: true });
    clearDraft("scheda-2");

    // scheda-1 ancora presente
    expect(loadDraft("scheda-1")).not.toBeNull();
  });
});
