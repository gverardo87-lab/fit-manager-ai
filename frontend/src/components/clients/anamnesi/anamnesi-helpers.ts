// src/components/clients/anamnesi/anamnesi-helpers.ts
/**
 * Utility per anamnesi v2: default values, type guards, helpers.
 *
 * Supporta backward compat con v1 (isStructuredAnamnesi distingue i formati).
 */

import type { AnamnesiData, AnamnesiQuestion } from "@/types/api";

const EMPTY_QUESTION: AnamnesiQuestion = { presente: false, dettaglio: null };

/** Default values per wizard nuovo (prima compilazione) — v2 */
export function getEmptyAnamnesi(): AnamnesiData {
  return {
    // Step 1: Stile di Vita
    professione: null,
    ore_seduto: "3-6",
    spostamento: "auto",
    ore_sonno: "7-8",
    qualita_sonno: "varia",
    livello_stress: 3,
    fumo: "no",
    alcol: "occasionalmente",
    passi_giornalieri: null,
    // Step 2: Obiettivo e Motivazione
    obiettivo_principale: "salute_generale",
    obiettivi_secondari: null,
    perche_adesso: null,
    cosa_3_mesi: null,
    impegno: 7,
    // Step 3: Esperienza Sportiva
    si_allena: false,
    frequenza_settimanale: "2",
    luogo_allenamento: "palestra",
    tipo_preferito: null,
    esperienza_durata: "mai",
    esperienza_pt: false,
    feedback_pt: null,
    // Step 4: Salute e Sicurezza
    dolori_attuali: [],
    dolori_attuali_altro: null,
    infortuni_importanti: { ...EMPTY_QUESTION },
    patologie: { ...EMPTY_QUESTION },
    patologie_lista: [],
    patologie_altro: null,
    farmaci_risposta: "no",
    farmaci_dettaglio: null,
    limitazioni_mediche: { ...EMPTY_QUESTION },
    certificato_sportivo: "no",
    // Step 5: Alimentazione
    tipo_alimentazione: "equilibrata",
    intolleranze: null,
    serenita_cibo: 7,
    messaggio_alimentazione: null,
    rapporto_complesso_alimentazione: "no",
    // Step 6: Logistica e Note
    preferenza_luogo: "palestra",
    sedute_settimana: "2",
    giorni_orari_preferiti: null,
    freni_passato: [],
    freni_altro: null,
    consenso_privacy: false,
    note_finali: null,
    // Metadata
    data_compilazione: new Date().toISOString().slice(0, 10),
    data_ultimo_aggiornamento: new Date().toISOString().slice(0, 10),
  };
}

/** Verifica se i dati sono nel formato strutturato v2.
 *  v1 (vecchio formato con infortuni_attuali) e' trattato come legacy — richiede ricompilazione. */
export function isStructuredAnamnesi(data: Record<string, unknown>): boolean {
  return "obiettivo_principale" in data && "data_compilazione" in data;
}

/** Ha condizioni mediche rilevanti (per badge/icone nel summary) */
export function hasMedicalConcerns(data: AnamnesiData): boolean {
  return (
    data.dolori_attuali.length > 0 ||
    data.infortuni_importanti.presente ||
    data.patologie.presente ||
    data.limitazioni_mediche.presente
  );
}

/** Estrae keywords controindicazioni per futuro filtro esercizi */
export function extractContraindications(data: AnamnesiData): string[] {
  const keywords: string[] = [];
  if (data.dolori_attuali.length > 0) {
    keywords.push(...data.dolori_attuali);
  }
  if (data.dolori_attuali_altro) {
    keywords.push(data.dolori_attuali_altro);
  }
  if (data.infortuni_importanti.presente && data.infortuni_importanti.dettaglio) {
    keywords.push(data.infortuni_importanti.dettaglio);
  }
  if (data.limitazioni_mediche.presente && data.limitazioni_mediche.dettaglio) {
    keywords.push(data.limitazioni_mediche.dettaglio);
  }
  return keywords;
}
