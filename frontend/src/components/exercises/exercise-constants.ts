// src/components/exercises/exercise-constants.ts
/**
 * Mapping valori interni (inglese) → label italiane per UI.
 * Usati nei filtri, badge, form select.
 */

export const CATEGORY_LABELS: Record<string, string> = {
  compound: "Composto",
  isolation: "Isolamento",
  bodyweight: "Corpo Libero",
  cardio: "Cardio",
};

export const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const EQUIPMENT_LABELS: Record<string, string> = {
  barbell: "Bilanciere",
  dumbbell: "Manubri",
  cable: "Cavi",
  machine: "Macchina",
  bodyweight: "Corpo Libero",
  kettlebell: "Kettlebell",
  band: "Elastico",
  trx: "TRX",
};

export const EQUIPMENT_OPTIONS = Object.entries(EQUIPMENT_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: "Base",
  intermediate: "Intermedio",
  advanced: "Avanzato",
};

export const DIFFICULTY_OPTIONS = Object.entries(DIFFICULTY_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const PATTERN_LABELS: Record<string, string> = {
  squat: "Squat",
  hinge: "Hinge",
  push_h: "Push Orizzontale",
  push_v: "Push Verticale",
  pull_h: "Pull Orizzontale",
  pull_v: "Pull Verticale",
  core: "Core",
  rotation: "Rotazione",
  carry: "Carry",
};

export const PATTERN_OPTIONS = Object.entries(PATTERN_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const MUSCLE_LABELS: Record<string, string> = {
  quadriceps: "Quadricipiti",
  hamstrings: "Femorali",
  glutes: "Glutei",
  calves: "Polpacci",
  adductors: "Adduttori",
  chest: "Petto",
  back: "Schiena",
  lats: "Dorsali",
  shoulders: "Spalle",
  traps: "Trapezio",
  biceps: "Bicipiti",
  triceps: "Tricipiti",
  forearms: "Avambracci",
  core: "Core",
};

export const MUSCLE_OPTIONS = Object.entries(MUSCLE_LABELS).map(
  ([value, label]) => ({ value, label })
);

// ── Colori badge ──

export const CATEGORY_COLORS: Record<string, string> = {
  compound: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  isolation: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  bodyweight: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  cardio: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
};

export const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  intermediate: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  advanced: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};
