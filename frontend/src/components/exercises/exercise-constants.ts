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
  stretching: "Stretching",
  mobilita: "Mobilità",
  avviamento: "Avviamento",
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
  stretch: "Stretching",
  mobility: "Mobilità",
  warmup: "Avviamento",
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

// ── Classificazione biomeccanica (v2) ──

export const FORCE_TYPE_LABELS: Record<string, string> = {
  push: "Spinta",
  pull: "Trazione",
  static: "Statico",
};

export const FORCE_TYPE_OPTIONS = Object.entries(FORCE_TYPE_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const LATERAL_PATTERN_LABELS: Record<string, string> = {
  bilateral: "Bilaterale",
  unilateral: "Unilaterale",
  alternating: "Alternato",
};

export const LATERAL_PATTERN_OPTIONS = Object.entries(LATERAL_PATTERN_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const RELATION_TYPE_LABELS: Record<string, string> = {
  progression: "Progressione",
  regression: "Regressione",
  variation: "Variante",
};

// ── Biomeccanica avanzata (tassonomia v3) ──

export const KINETIC_CHAIN_LABELS: Record<string, string> = {
  open: "Catena Aperta",
  closed: "Catena Chiusa",
};

export const KINETIC_CHAIN_OPTIONS = Object.entries(KINETIC_CHAIN_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const MOVEMENT_PLANE_LABELS: Record<string, string> = {
  sagittal: "Sagittale",
  frontal: "Frontale",
  transverse: "Trasversale",
  multi: "Multiplanare",
};

export const MOVEMENT_PLANE_OPTIONS = Object.entries(MOVEMENT_PLANE_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const CONTRACTION_TYPE_LABELS: Record<string, string> = {
  concentric: "Concentrica",
  eccentric: "Eccentrica",
  isometric: "Isometrica",
  dynamic: "Dinamica",
};

export const CONTRACTION_TYPE_OPTIONS = Object.entries(CONTRACTION_TYPE_LABELS).map(
  ([value, label]) => ({ value, label })
);

export const JOINT_ROLE_LABELS: Record<string, string> = {
  agonist: "Agonista",
  stabilizer: "Stabilizzatore",
};

export const MUSCLE_ROLE_LABELS: Record<string, string> = {
  primary: "Primario",
  secondary: "Secondario",
  stabilizer: "Stabilizzatore",
};

// ── Colori chip (hex per inline style nel FilterBar) ──

export const CATEGORY_CHIP_COLORS: Record<string, string> = {
  compound: "#3b82f6",
  isolation: "#a855f7",
  bodyweight: "#10b981",
  cardio: "#f97316",
  stretching: "#06b6d4",
  mobilita: "#84cc16",
  avviamento: "#f59e0b",
};

// ── Colori badge ──

export const CATEGORY_COLORS: Record<string, string> = {
  compound: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  isolation: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  bodyweight: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  cardio: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  stretching: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400",
  mobilita: "bg-lime-100 text-lime-700 dark:bg-lime-900/30 dark:text-lime-400",
  avviamento: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
};

export const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  intermediate: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  advanced: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export const FORCE_TYPE_COLORS: Record<string, string> = {
  push: "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400",
  pull: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
  static: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900/30 dark:text-zinc-400",
};

export const LATERAL_PATTERN_COLORS: Record<string, string> = {
  bilateral: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400",
  unilateral: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400",
  alternating: "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-400",
};
