// src/components/clients/anamnesi/anamnesi-helpers.ts
/**
 * Utility per anamnesi: default values, type guards, helpers.
 */

import type { AnamnesiData, AnamnesiQuestion } from "@/types/api";

const EMPTY_QUESTION: AnamnesiQuestion = { presente: false, dettaglio: null };

/** Default values per wizard nuovo (prima compilazione) */
export function getEmptyAnamnesi(): AnamnesiData {
  return {
    // Step 1: Muscoloscheletrico
    infortuni_attuali: { ...EMPTY_QUESTION },
    infortuni_pregressi: { ...EMPTY_QUESTION },
    interventi_chirurgici: { ...EMPTY_QUESTION },
    dolori_cronici: { ...EMPTY_QUESTION },
    // Step 2: Condizioni Mediche
    patologie: { ...EMPTY_QUESTION },
    farmaci: { ...EMPTY_QUESTION },
    problemi_cardiovascolari: { ...EMPTY_QUESTION },
    problemi_respiratori: { ...EMPTY_QUESTION },
    // Step 3: Stile di Vita
    livello_attivita: "sedentario",
    ore_sonno: "7-8",
    livello_stress: "medio",
    dieta_particolare: { ...EMPTY_QUESTION },
    // Step 4: Obiettivi e Limitazioni
    obiettivi_specifici: null,
    limitazioni_funzionali: null,
    note: null,
    // Metadata
    data_compilazione: new Date().toISOString().slice(0, 10),
    data_ultimo_aggiornamento: new Date().toISOString().slice(0, 10),
  };
}

/** Verifica se i dati sono nel formato strutturato (vs legacy dict) */
export function isStructuredAnamnesi(data: Record<string, unknown>): boolean {
  return "infortuni_attuali" in data && "data_compilazione" in data;
}

/** Ha condizioni mediche rilevanti (per badge/icone nel summary) */
export function hasMedicalConcerns(data: AnamnesiData): boolean {
  return (
    data.infortuni_attuali.presente ||
    data.dolori_cronici.presente ||
    data.patologie.presente ||
    data.problemi_cardiovascolari.presente ||
    data.problemi_respiratori.presente
  );
}

/** Estrae keywords controindicazioni per futuro filtro esercizi */
export function extractContraindications(data: AnamnesiData): string[] {
  const keywords: string[] = [];
  if (data.infortuni_attuali.presente && data.infortuni_attuali.dettaglio) {
    keywords.push(data.infortuni_attuali.dettaglio);
  }
  if (data.dolori_cronici.presente && data.dolori_cronici.dettaglio) {
    keywords.push(data.dolori_cronici.dettaglio);
  }
  if (data.limitazioni_funzionali) {
    keywords.push(data.limitazioni_funzionali);
  }
  return keywords;
}
