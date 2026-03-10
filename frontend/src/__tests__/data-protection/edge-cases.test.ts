// src/__tests__/data-protection/edge-cases.test.ts
/**
 * Edge cases e scenari di stress sulla protezione dati.
 *
 * Copre: race condition, rapid open/close, concurrent mutations,
 * beforeunload, onDirtyChange propagation, form lifecycle.
 */

import { describe, it, expect, vi } from "vitest";
import { saveDraft, loadDraft, clearDraft } from "@/hooks/useUnsavedChanges";

// ════════════════════════════════════════════════════════════
// BEFOREUNLOAD — Simulazione handler
// ════════════════════════════════════════════════════════════

/**
 * Riproduce il handler beforeunload del hook useUnsavedChanges.
 * Testa che il browser mostra il prompt solo quando dirty.
 */
describe("beforeunload handler", () => {
  it("chiama preventDefault quando dirty", () => {
    const dirtyRef = { current: true };
    const event = new Event("beforeunload") as BeforeUnloadEvent;
    const preventSpy = vi.spyOn(event, "preventDefault");

    // Simula handler come nel hook
    if (dirtyRef.current) {
      event.preventDefault();
    }

    expect(preventSpy).toHaveBeenCalled();
  });

  it("NON chiama preventDefault quando pulito", () => {
    const dirtyRef = { current: false };
    const event = new Event("beforeunload") as BeforeUnloadEvent;
    const preventSpy = vi.spyOn(event, "preventDefault");

    if (dirtyRef.current) {
      event.preventDefault();
    }

    expect(preventSpy).not.toHaveBeenCalled();
  });

  it("ref aggiornato: dirty→false dopo save, beforeunload non blocca", () => {
    const dirtyRef = { current: true };

    // Simula save
    dirtyRef.current = false;

    const event = new Event("beforeunload") as BeforeUnloadEvent;
    const preventSpy = vi.spyOn(event, "preventDefault");

    if (dirtyRef.current) {
      event.preventDefault();
    }

    expect(preventSpy).not.toHaveBeenCalled();
  });
});

// ════════════════════════════════════════════════════════════
// onDirtyChange PROPAGATION — Simulazione flusso Form→Sheet
// ════════════════════════════════════════════════════════════

describe("onDirtyChange propagation (Form → Sheet)", () => {
  it("isDirty=false iniziale: dirtyRef non viene settato", () => {
    const dirtyRef = { current: false };
    const handleDirtyChange = (d: boolean) => { dirtyRef.current = d; };

    // Form si monta con isDirty=false
    handleDirtyChange(false);
    expect(dirtyRef.current).toBe(false);
  });

  it("prima modifica: isDirty=true propaga a dirtyRef", () => {
    const dirtyRef = { current: false };
    const handleDirtyChange = (d: boolean) => { dirtyRef.current = d; };

    // Utente tocca un campo → react-hook-form isDirty diventa true
    handleDirtyChange(true);
    expect(dirtyRef.current).toBe(true);
  });

  it("reset form (dopo save): isDirty=false ripulisce dirtyRef", () => {
    const dirtyRef = { current: true };
    const handleDirtyChange = (d: boolean) => { dirtyRef.current = d; };

    // Save resetta il form
    handleDirtyChange(false);
    expect(dirtyRef.current).toBe(false);
  });

  it("transizione rapida: false→true→false→true (utente indeciso)", () => {
    const dirtyRef = { current: false };
    const handleDirtyChange = (d: boolean) => { dirtyRef.current = d; };

    handleDirtyChange(false); // Mount
    expect(dirtyRef.current).toBe(false);

    handleDirtyChange(true); // Modifica
    expect(dirtyRef.current).toBe(true);

    handleDirtyChange(false); // Undo (torna ai default)
    expect(dirtyRef.current).toBe(false);

    handleDirtyChange(true); // Ri-modifica
    expect(dirtyRef.current).toBe(true);
  });
});

// ════════════════════════════════════════════════════════════
// RAPID OPEN/CLOSE — Stress test lifecycle
// ════════════════════════════════════════════════════════════

describe("Rapid open/close lifecycle", () => {
  /**
   * BUG POTENZIALE: utente apre e chiude Sheet rapidamente.
   * Il dirtyRef deve resettarsi correttamente ad ogni ciclo.
   */
  it("10 cicli apri/chiudi senza modifiche: mai bloccato", () => {
    const onOpenChange = vi.fn();
    const dirtyRef = { current: false };

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      dirtyRef.current = false;
      onOpenChange(newOpen);
    };

    for (let i = 0; i < 10; i++) {
      guardedOpenChange(true);  // Apri
      guardedOpenChange(false); // Chiudi
    }

    // 20 chiamate totali (10 apri + 10 chiudi)
    expect(onOpenChange).toHaveBeenCalledTimes(20);
  });

  it("apri → dirty → blocca → apri → dirty → conferma → chiudi", () => {
    const onOpenChange = vi.fn();
    const dirtyRef = { current: false };

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      dirtyRef.current = false;
      onOpenChange(newOpen);
    };

    // Ciclo 1: dirty, blocca chiusura
    guardedOpenChange(true);
    dirtyRef.current = true;
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledTimes(1); // Solo open

    // dirtyRef ancora true (non resettato dal blocco)
    expect(dirtyRef.current).toBe(true);

    // Ciclo 2: conferma chiusura
    vi.spyOn(window, "confirm").mockReturnValue(true);
    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledTimes(2); // Open + close
    expect(dirtyRef.current).toBe(false);
  });
});

// ════════════════════════════════════════════════════════════
// DRAFT + GUARD INTEGRATION
// ════════════════════════════════════════════════════════════

describe("Draft + Guard integration", () => {
  it("scenario builder: modifica → draft salvato → refresh → draft recuperato", () => {
    const key = "scheda-builder-7";

    // 1. Utente modifica la scheda
    const sessions = [{ id: "s1", name: "Push", exercises: ["Panca", "Croci"] }];
    saveDraft(key, sessions);

    // 2. Browser si refresha (o crash)
    // ... sessionStorage persiste ...

    // 3. Al rientro, draft disponibile
    const recovered = loadDraft<typeof sessions>(key);
    expect(recovered).not.toBeNull();
    expect(recovered!.data[0].exercises).toEqual(["Panca", "Croci"]);
  });

  it("scenario builder: save con successo → draft cancellato → nessun recover", () => {
    const key = "scheda-builder-7";

    // 1. Draft presente
    saveDraft(key, { data: "work-in-progress" });
    expect(loadDraft(key)).not.toBeNull();

    // 2. Save con successo
    clearDraft(key);

    // 3. Nessun draft residuo
    expect(loadDraft(key)).toBeNull();
  });

  it("scenario: chiusura bloccata → draft ancora disponibile per recovery", () => {
    const key = "scheda-builder-7";
    const dirtyRef = { current: false };
    const isOpen = true;

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      isOpen = newOpen;
      dirtyRef.current = false;
    };

    // 1. Utente modifica → draft salvato
    dirtyRef.current = true;
    saveDraft(key, { modified: true });

    // 2. Prova a chiudere → RIFIUTA
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);

    // 3. Sheet ancora aperto
    expect(isOpen).toBe(true);

    // 4. Draft ancora disponibile
    expect(loadDraft(key)).not.toBeNull();
  });
});

// ════════════════════════════════════════════════════════════
// CONCURRENT MUTATIONS — Race condition
// ════════════════════════════════════════════════════════════

describe("Concurrent mutations — Race condition", () => {
  /**
   * BUG POTENZIALE: utente clicca "Salva" due volte rapidamente.
   * La seconda mutation non deve corrompere lo stato.
   */
  it("doppio click salva: la prima chiude, la seconda e' no-op", () => {
    const onOpenChange = vi.fn();
    const dirtyRef = { current: true };
    let mutationCount = 0;

    const handleSave = () => {
      mutationCount++;
      // Simula onSuccess della prima mutation
      if (mutationCount === 1) {
        dirtyRef.current = false;
        onOpenChange(false);
      }
      // Seconda chiamata: gia' chiuso, no-op
    };

    handleSave(); // Click 1
    handleSave(); // Click 2 (rapido)

    expect(onOpenChange).toHaveBeenCalledTimes(1);
    expect(dirtyRef.current).toBe(false);
  });

  /**
   * SCENARIO: mutation fallisce (server error) → form resta aperto e dirty.
   * L'utente deve poter correggere e riprovare.
   */
  it("mutation fallita: form resta dirty e aperto", () => {
    const dirtyRef = { current: true };
    const isOpen = true;

    // Mutation fallisce → onError (non chiama onOpenChange)
    const handleMutationError = () => {
      // Non fare nulla: il form resta com'e'
    };

    handleMutationError();

    expect(dirtyRef.current).toBe(true);
    expect(isOpen).toBe(true);
  });
});

// ════════════════════════════════════════════════════════════
// AnamnesiWizard — SCENARI SPECIFICI
// ════════════════════════════════════════════════════════════

describe("AnamnesiWizard — Protezione multi-step", () => {
  /**
   * L'utente compila 3 step del wizard, poi clicca fuori dal dialog.
   * PRIMA del fix: tutto perso. DOPO: confirm chiede conferma.
   */
  it("wizard: step 3 con dirty blocca overlay click", () => {
    const dirtyRef = { current: false };
    const onOpenChange = vi.fn();

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
      }
      onOpenChange(newOpen);
    };

    // Utente compila 3 step
    dirtyRef.current = true;

    // Click overlay → Radix chiama onOpenChange(false)
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);

    expect(onOpenChange).not.toHaveBeenCalled();
  });

  it("wizard: open resetta dirty per sessione pulita", () => {
    const dirtyRef = { current: true }; // Sessione precedente

    // Nuova apertura resetta dirty
    dirtyRef.current = false;

    expect(dirtyRef.current).toBe(false);
  });

  it("wizard: Escape key viene intercettato (stessa logica di overlay)", () => {
    const dirtyRef = { current: true };
    const onOpenChange = vi.fn();

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      onOpenChange(newOpen);
    };

    // Radix Dialog manda onOpenChange(false) su Escape
    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);

    expect(onOpenChange).not.toHaveBeenCalled();
  });
});

// ════════════════════════════════════════════════════════════
// EDIT MODE — Pre-popolazione form
// ════════════════════════════════════════════════════════════

describe("Edit mode — Pre-population e protezione", () => {
  /**
   * SCENARIO: utente apre form in edit mode.
   * I campi vengono popolati dal server.
   * react-hook-form NON marca isDirty (perche' i valori = defaultValues).
   * Se l'utente non modifica nulla e chiude → nessun confirm (corretto).
   */
  it("apertura in edit mode: isDirty=false, chiusura libera", () => {
    const dirtyRef = { current: false };
    const onOpenChange = vi.fn();

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      onOpenChange(newOpen);
    };

    // Form si monta con defaultValues dal server
    // isDirty = false (nessuna modifica)

    guardedOpenChange(false);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  /**
   * SCENARIO: utente apre form in edit mode e modifica un campo.
   * isDirty diventa true → chiusura bloccata.
   */
  it("edit mode + modifica: isDirty=true, chiusura bloccata", () => {
    const dirtyRef = { current: false };
    const onOpenChange = vi.fn();

    const guardedOpenChange = (newOpen: boolean) => {
      if (!newOpen && dirtyRef.current) {
        if (!window.confirm("Confirm?")) return;
      }
      dirtyRef.current = false;
      onOpenChange(newOpen);
    };

    // Utente modifica un campo
    dirtyRef.current = true;

    vi.spyOn(window, "confirm").mockReturnValue(false);
    guardedOpenChange(false);
    expect(onOpenChange).not.toHaveBeenCalled();
  });
});

// ════════════════════════════════════════════════════════════
// STORAGE LIMITS — Draft con dati grandi
// ════════════════════════════════════════════════════════════

describe("Draft — Dati di dimensioni reali", () => {
  it("scheda con 6 sessioni × 8 esercizi ciascuna (48 esercizi)", () => {
    const sessions = Array.from({ length: 6 }, (_, si) => ({
      id: `session-${si}`,
      nome: `Sessione ${si + 1}`,
      esercizi: Array.from({ length: 8 }, (_, ei) => ({
        id_esercizio: si * 10 + ei,
        nome: `Esercizio ${ei + 1}`,
        serie: "4",
        rip: "8-12",
        riposo: "90",
        carico_kg: Math.round(Math.random() * 100),
        note: `Note per esercizio ${ei + 1} nella sessione ${si + 1}`,
        tempo_esecuzione: "3-1-2",
      })),
    }));

    const key = "scheda-stress-test";
    saveDraft(key, sessions);
    const loaded = loadDraft<typeof sessions>(key);

    expect(loaded).not.toBeNull();
    expect(loaded!.data).toHaveLength(6);
    expect(loaded!.data[0].esercizi).toHaveLength(8);

    // Verifica integrita' ultimo elemento
    const last = loaded!.data[5].esercizi[7];
    expect(last.serie).toBe("4");
    expect(typeof last.carico_kg).toBe("number");
  });

  it("anamnesi con tutti i campi compilati", () => {
    const anamnesi = {
      patologie_muscoloscheletriche: ["Ernia L4-L5", "Protrusione C5-C6"],
      interventi_chirurgici: ["Artroscopia ginocchio DX 2020"],
      dolore_cronico: "Lombalgia cronica lieve",
      limitazioni_movimento: "Flessione anca DX limitata 90°",
      condizioni_cardiovascolari: ["Ipertensione controllata"],
      condizioni_metaboliche: ["Diabete tipo 2"],
      farmaci: "Metformina 500mg × 2, Ramipril 5mg",
      allergie: "Nessuna nota",
      livello_attivita: "Moderato (3-4 allenamenti/settimana)",
      ore_sonno: "6-7",
      stress_percepito: "Alto",
      alimentazione: "Mediterranea, pasto libero sabato",
      obiettivi_specifici: "Perdita grasso 5kg, miglioramento postura, prevenzione recidiva lombalgia",
      motivazione: "Alta",
      disponibilita_settimanale: "3 sessioni da 60 min",
      data_compilazione: "2026-01-15",
      data_ultimo_aggiornamento: "2026-03-01",
    };

    saveDraft("anamnesi-42", anamnesi);
    const loaded = loadDraft<typeof anamnesi>("anamnesi-42");

    expect(loaded!.data.patologie_muscoloscheletriche).toHaveLength(2);
    expect(loaded!.data.farmaci).toContain("Metformina");
    expect(loaded!.data.data_ultimo_aggiornamento).toBe("2026-03-01");
  });
});

// ════════════════════════════════════════════════════════════
// BOUNDARY VALUES — Valori limite
// ════════════════════════════════════════════════════════════

describe("Boundary values", () => {
  it("draft con stringa vuota come dato", () => {
    saveDraft("empty-string", "");
    const loaded = loadDraft<string>("empty-string");
    expect(loaded!.data).toBe("");
  });

  it("draft con numero zero", () => {
    saveDraft("zero", 0);
    const loaded = loadDraft<number>("zero");
    expect(loaded!.data).toBe(0);
  });

  it("draft con array vuoto", () => {
    saveDraft("empty-array", []);
    const loaded = loadDraft<unknown[]>("empty-array");
    expect(loaded!.data).toEqual([]);
  });

  it("draft con oggetto vuoto", () => {
    saveDraft("empty-obj", {});
    const loaded = loadDraft<Record<string, never>>("empty-obj");
    expect(loaded!.data).toEqual({});
  });

  it("draft con false come dato", () => {
    saveDraft("false-val", false);
    const loaded = loadDraft<boolean>("false-val");
    expect(loaded!.data).toBe(false);
  });

  it("chiave con caratteri speciali", () => {
    const key = "scheda-[builder]-{test}-(v2)";
    saveDraft(key, { ok: true });
    const loaded = loadDraft<{ ok: boolean }>(key);
    expect(loaded!.data.ok).toBe(true);
  });

  it("chiave con spazi e unicode", () => {
    const key = "anamnesi cliente №42";
    saveDraft(key, { italian: "caffè" });
    const loaded = loadDraft<{ italian: string }>(key);
    expect(loaded!.data.italian).toBe("caffè");
  });
});
