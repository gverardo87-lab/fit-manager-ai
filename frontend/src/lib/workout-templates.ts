// src/lib/workout-templates.ts
/**
 * Template predefiniti per schede allenamento.
 *
 * Ogni template pre-popola la struttura (sessioni + slot esercizi con suggerimenti).
 * Il trainer seleziona poi gli esercizi specifici dal database.
 *
 * Ogni sessione ha 3 sezioni:
 * - avviamento: riscaldamento e attivazione (warmup)
 * - principale: esercizi di forza/ipertrofia (strength)
 * - stretching: stretching e mobilita (cooldown)
 *
 * I suggerimenti usano pattern_movimento come hint per l'exercise selector.
 */

export type TemplateSection = "avviamento" | "principale" | "stretching";

export interface TemplateExerciseSlot {
  /** Sezione della sessione a cui appartiene lo slot */
  sezione: TemplateSection;
  /** Suggerimento pattern_movimento per filtrare il selector */
  pattern_hint: string;
  /** Label descrittiva per lo slot (es. "Squat o Pressa") */
  label: string;
  /** Serie di default */
  serie: number;
  /** Ripetizioni di default */
  ripetizioni: string;
  /** Tempo riposo in secondi */
  tempo_riposo_sec: number;
}

export interface TemplateSession {
  nome_sessione: string;
  focus_muscolare: string;
  durata_minuti: number;
  slots: TemplateExerciseSlot[];
}

export interface WorkoutTemplate {
  id: string;
  nome: string;
  descrizione: string;
  livello: "beginner" | "intermedio" | "avanzato";
  obiettivo_default: string;
  sessioni_per_settimana: number;
  durata_settimane: number;
  sessioni: TemplateSession[];
}

/** Sezione labels per UI */
export const SECTION_LABELS: Record<TemplateSection, string> = {
  avviamento: "Avviamento",
  principale: "Esercizio Principale",
  stretching: "Stretching & Mobilita",
};

/** Categorie esercizio che appartengono a ciascuna sezione */
export const SECTION_CATEGORIES: Record<TemplateSection, string[]> = {
  avviamento: ["avviamento"],
  principale: ["compound", "isolation", "bodyweight", "cardio"],
  stretching: ["stretching", "mobilita"],
};

/** Data una categoria esercizio, ritorna la sezione */
export function getSectionForCategory(categoria: string): TemplateSection {
  if (SECTION_CATEGORIES.avviamento.includes(categoria)) return "avviamento";
  if (SECTION_CATEGORIES.stretching.includes(categoria)) return "stretching";
  return "principale";
}

// ════════════════════════════════════════════════════════════
// BEGINNER — Full Body (2 sessioni/settimana)
// ════════════════════════════════════════════════════════════

const BEGINNER_TEMPLATE: WorkoutTemplate = {
  id: "beginner-full-body",
  nome: "Full Body Principiante",
  descrizione: "2 sessioni a settimana, focus compound. Ideale per chi inizia o riprende.",
  livello: "beginner",
  obiettivo_default: "generale",
  sessioni_per_settimana: 2,
  durata_settimane: 4,
  sessioni: [
    {
      nome_sessione: "Full Body A",
      focus_muscolare: "quadricipiti, petto, dorsali",
      durata_minuti: 50,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera o Cyclette", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Jumping Jacks", serie: 2, ripetizioni: "15", tempo_riposo_sec: 30 },
        // Principale
        { sezione: "principale", pattern_hint: "squat", label: "Squat o Pressa", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_h", label: "Panca o Push-up", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rematore o Lat Machine", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "hinge", label: "Romanian Deadlift", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_v", label: "Shoulder Press", serie: 2, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "core", label: "Plank o Crunch", serie: 3, ripetizioni: "30s", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Quadricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Pettorali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Dorsali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Full Body B",
      focus_muscolare: "glutei, spalle, braccia",
      durata_minuti: 50,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Skip o Cyclette", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cerchi Braccia", serie: 2, ripetizioni: "10/direzione", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "hinge", label: "Stacco o Hip Thrust", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_v", label: "Military Press", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_v", label: "Lat Pulldown", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Affondi o Leg Press", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Bicipiti", serie: 2, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "core", label: "Russian Twist o Side Plank", serie: 3, ripetizioni: "30s", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Femorali", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Spalle", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "mobility", label: "Stretching Schiena (Cat-Cow)", serie: 1, ripetizioni: "10 reps", tempo_riposo_sec: 0 },
      ],
    },
  ],
};

// ════════════════════════════════════════════════════════════
// INTERMEDIO — Upper/Lower Split (4 sessioni/settimana)
// ════════════════════════════════════════════════════════════

const INTERMEDIO_TEMPLATE: WorkoutTemplate = {
  id: "intermedio-upper-lower",
  nome: "Upper/Lower Split",
  descrizione: "4 sessioni a settimana, split upper/lower. Bilanciato per massa e forza.",
  livello: "intermedio",
  obiettivo_default: "ipertrofia",
  sessioni_per_settimana: 4,
  durata_settimane: 6,
  sessioni: [
    {
      nome_sessione: "Upper A — Push Focus",
      focus_muscolare: "petto, spalle, tricipiti",
      durata_minuti: 60,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cerchi Braccia + Rotazioni Tronco", serie: 2, ripetizioni: "10/direzione", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Shoulder Dislocates", serie: 2, ripetizioni: "10", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "push_h", label: "Panca Piana", serie: 4, ripetizioni: "6-8", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "push_v", label: "Military Press", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_h", label: "Croci o Panca Inclinata", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rematore", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_h", label: "Tricipiti", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Bicipiti", serie: 2, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Pettorali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Spalle", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Tricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Lower A — Quad Focus",
      focus_muscolare: "quadricipiti, glutei, polpacci",
      durata_minuti: 60,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cyclette o Corsa", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Squat Bodyweight + Skip", serie: 2, ripetizioni: "15", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Mobilita Caviglie", serie: 2, ripetizioni: "10/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "squat", label: "Squat", serie: 4, ripetizioni: "6-8", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "squat", label: "Leg Press", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "hinge", label: "Romanian Deadlift", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Leg Extension", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "hinge", label: "Leg Curl", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "squat", label: "Calf Raise", serie: 3, ripetizioni: "15-20", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Quadricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Femorali", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Polpacci", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Upper B — Pull Focus",
      focus_muscolare: "dorsali, trapezio, bicipiti",
      durata_minuti: 60,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Inchworm", serie: 2, ripetizioni: "5", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Rotazioni Toraciche", serie: 2, ripetizioni: "8/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "pull_v", label: "Trazioni o Lat Pulldown", serie: 4, ripetizioni: "6-8", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rematore Bilanciere", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_v", label: "Lento Avanti", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Face Pull o Alzate Lat.", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Manubri", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_h", label: "French Press", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Dorsali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Spalle", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Collo", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Lower B — Hip Focus",
      focus_muscolare: "glutei, femorali, core",
      durata_minuti: 60,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cyclette o Corsa", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Affondi Bodyweight", serie: 2, ripetizioni: "10/lato", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Cerchi d'Anca", serie: 2, ripetizioni: "10/direzione", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "hinge", label: "Stacco da Terra", serie: 4, ripetizioni: "5-6", tempo_riposo_sec: 150 },
        { sezione: "principale", pattern_hint: "hinge", label: "Hip Thrust", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Affondi Camminati", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "hinge", label: "Leg Curl Sdraiato", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "core", label: "Plank o Ab Wheel", serie: 3, ripetizioni: "30-45s", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "carry", label: "Farmer Walk", serie: 3, ripetizioni: "30m", tempo_riposo_sec: 60 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Flessori Anca", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Glutei", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Schiena (Cat-Cow)", serie: 1, ripetizioni: "10 reps", tempo_riposo_sec: 0 },
      ],
    },
  ],
};

// ════════════════════════════════════════════════════════════
// AVANZATO — Push/Pull/Legs (6 sessioni/settimana)
// ════════════════════════════════════════════════════════════

const AVANZATO_TEMPLATE: WorkoutTemplate = {
  id: "avanzato-ppl",
  nome: "Push / Pull / Legs",
  descrizione: "6 sessioni a settimana, PPL x2. Per atleti intermedi-avanzati con esperienza.",
  livello: "avanzato",
  obiettivo_default: "ipertrofia",
  sessioni_per_settimana: 6,
  durata_settimane: 8,
  sessioni: [
    {
      nome_sessione: "Push A — Forza",
      focus_muscolare: "petto, spalle, tricipiti",
      durata_minuti: 70,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cerchi Braccia", serie: 2, ripetizioni: "10/direzione", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Shoulder Dislocates", serie: 2, ripetizioni: "10", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "push_h", label: "Panca Piana", serie: 5, ripetizioni: "5-6", tempo_riposo_sec: 150 },
        { sezione: "principale", pattern_hint: "push_v", label: "Military Press", serie: 4, ripetizioni: "6-8", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "push_h", label: "Panca Inclinata Manubri", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_v", label: "Alzate Laterali", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_h", label: "Dip o Push Down", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_h", label: "Overhead Extension", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_v", label: "Alzate Frontali", serie: 2, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Pettorali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Spalle", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Tricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Pull A — Forza",
      focus_muscolare: "dorsali, trapezio, bicipiti",
      durata_minuti: 70,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Inchworm", serie: 2, ripetizioni: "5", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Rotazioni Toraciche", serie: 2, ripetizioni: "8/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "pull_v", label: "Trazioni Zavorrate", serie: 4, ripetizioni: "5-6", tempo_riposo_sec: 150 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rematore Bilanciere", serie: 4, ripetizioni: "6-8", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "pull_v", label: "Lat Pulldown Presa Stretta", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Face Pull", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Bilanciere", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Martello", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rear Delt Fly", serie: 2, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Dorsali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Collo", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "mobility", label: "Open Book", serie: 1, ripetizioni: "8/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Legs A — Quad Focus",
      focus_muscolare: "quadricipiti, glutei, polpacci",
      durata_minuti: 70,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cyclette", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Squat Bodyweight + Skip", serie: 2, ripetizioni: "15", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Mobilita Caviglie", serie: 2, ripetizioni: "10/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "squat", label: "Squat", serie: 5, ripetizioni: "5-6", tempo_riposo_sec: 180 },
        { sezione: "principale", pattern_hint: "squat", label: "Leg Press", serie: 4, ripetizioni: "8-10", tempo_riposo_sec: 120 },
        { sezione: "principale", pattern_hint: "hinge", label: "Romanian Deadlift", serie: 3, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Leg Extension", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "squat", label: "Affondi Bulgari", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Calf Raise in Piedi", serie: 4, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        { sezione: "principale", pattern_hint: "core", label: "Crunch Cable", serie: 3, ripetizioni: "15-20", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Quadricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Femorali", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Polpacci", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Push B — Ipertrofia",
      focus_muscolare: "petto, spalle, tricipiti",
      durata_minuti: 65,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Jumping Jacks", serie: 2, ripetizioni: "20", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cerchi Braccia", serie: 2, ripetizioni: "10/direzione", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "push_h", label: "Panca Inclinata", serie: 4, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_h", label: "Croci Cavi", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_v", label: "Arnold Press", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "push_v", label: "Alzate Laterali Cavi", serie: 4, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        { sezione: "principale", pattern_hint: "push_h", label: "Tricipiti Corda", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "push_h", label: "Kick Back", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Pettorali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Tricipiti", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Pull B — Ipertrofia",
      focus_muscolare: "dorsali, trapezio, bicipiti",
      durata_minuti: 65,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Corsa leggera", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "Rotazioni Toraciche", serie: 2, ripetizioni: "8/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "pull_v", label: "Lat Pulldown", serie: 4, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Rematore Manubrio", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Pulley Basso", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Face Pull", serie: 3, ripetizioni: "15-20", tempo_riposo_sec: 45 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Concentrato", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "pull_h", label: "Curl Cavo Presa Alta", serie: 3, ripetizioni: "12-15", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Dorsali", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Spalle", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
      ],
    },
    {
      nome_sessione: "Legs B — Hip Focus",
      focus_muscolare: "glutei, femorali, core",
      durata_minuti: 65,
      slots: [
        // Avviamento
        { sezione: "avviamento", pattern_hint: "warmup", label: "Cyclette", serie: 1, ripetizioni: "5 min", tempo_riposo_sec: 0 },
        { sezione: "avviamento", pattern_hint: "warmup", label: "Affondi Bodyweight", serie: 2, ripetizioni: "10/lato", tempo_riposo_sec: 30 },
        { sezione: "avviamento", pattern_hint: "mobility", label: "World's Greatest Stretch", serie: 2, ripetizioni: "5/lato", tempo_riposo_sec: 0 },
        // Principale
        { sezione: "principale", pattern_hint: "hinge", label: "Stacco da Terra", serie: 4, ripetizioni: "5-6", tempo_riposo_sec: 180 },
        { sezione: "principale", pattern_hint: "hinge", label: "Hip Thrust", serie: 4, ripetizioni: "8-10", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "squat", label: "Affondi Camminati", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 90 },
        { sezione: "principale", pattern_hint: "hinge", label: "Leg Curl", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "hinge", label: "Good Morning", serie: 3, ripetizioni: "10-12", tempo_riposo_sec: 60 },
        { sezione: "principale", pattern_hint: "squat", label: "Calf Raise Seduto", serie: 4, ripetizioni: "15-20", tempo_riposo_sec: 45 },
        { sezione: "principale", pattern_hint: "core", label: "Plank Laterale", serie: 3, ripetizioni: "30s", tempo_riposo_sec: 45 },
        // Stretching
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Flessori Anca", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Glutei", serie: 1, ripetizioni: "30s/lato", tempo_riposo_sec: 0 },
        { sezione: "stretching", pattern_hint: "stretch", label: "Stretching Adduttori", serie: 1, ripetizioni: "30s", tempo_riposo_sec: 0 },
      ],
    },
  ],
};

// ════════════════════════════════════════════════════════════
// EXPORT
// ════════════════════════════════════════════════════════════

export const WORKOUT_TEMPLATES: WorkoutTemplate[] = [
  BEGINNER_TEMPLATE,
  INTERMEDIO_TEMPLATE,
  AVANZATO_TEMPLATE,
];

export function getTemplateById(id: string): WorkoutTemplate | undefined {
  return WORKOUT_TEMPLATES.find((t) => t.id === id);
}
