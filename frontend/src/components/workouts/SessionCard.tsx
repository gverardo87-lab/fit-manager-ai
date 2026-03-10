// src/components/workouts/SessionCard.tsx
"use client";

/**
 * Card per una singola sessione di allenamento dentro il builder.
 *
 * 3 sezioni visive come separatori leggeri (label + linea h-px colorata, zero box):
 * - Avviamento (warm-up)      → linea amber
 * - Blocco Serie x Ripetizioni → linea primary
 * - Stretching & Mobilita     → linea cyan
 *
 * Ogni sezione ha drag & drop indipendente, + button, e "Svuota" button.
 * Blocchi strutturati (circuit, tabata…) si inseriscono nella sezione principale.
 * Azioni sessione in overflow menu (⋮) per header compatto.
 */

import { useCallback, useMemo, useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Plus, Trash2, Pencil, Flame, Dumbbell, Heart, ShieldAlert, AlertTriangle, Info, Copy, StickyNote, MoreVertical, Layers, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { SortableExerciseRow } from "./SortableExerciseRow";
import { BlockCard, type BlockCardData } from "./BlockCard";
import { getSectionForCategory, type TemplateSection } from "@/lib/workout-templates";
import { MUSCLE_LABELS, MUSCLE_COLORS } from "@/components/exercises/exercise-constants";
import type { WorkoutExerciseRow, ExerciseSafetyEntry, Exercise, BlockType } from "@/types/api";

export interface SessionCardData {
  id: number;
  numero_sessione: number;
  nome_sessione: string;
  focus_muscolare: string | null;
  durata_minuti: number;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
  /** Blocchi strutturati (circuit, tabata, AMRAP, EMOM, superset) — nella sezione principale */
  blocchi: BlockCardData[];
}

interface SessionCardProps {
  session: SessionCardData;
  /** Layout board (colonne affiancate): esercizi compatti su 2 righe */
  boardView?: boolean;
  /** Safety map per-esercizio (da anamnesi cliente). Informativo, mai bloccante. */
  safetyMap?: Record<number, ExerciseSafetyEntry>;
  /** Mappa esercizi completi per pannello dettaglio inline */
  exerciseMap?: Map<number, Exercise>;
  /** ID scheda per deep-link ritorno dalla pagina esercizio */
  schedaId?: number;
  /** Contesto provenienza scheda (es. "allenamenti") per catena navigazione */
  parentFrom?: string | null;
  /** Mappa pattern_movimento → valore 1RM cliente (per badge % 1RM) */
  oneRMByPattern?: Record<string, number> | null;
  onUpdateSession: (sessionId: number, updates: Partial<SessionCardData>) => void;
  onDeleteSession: (sessionId: number) => void;
  onDuplicateSession?: (sessionId: number) => void;
  onAddExercise: (sessionId: number, sezione?: TemplateSection) => void;
  onUpdateExercise: (sessionId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => void;
  onDeleteExercise: (sessionId: number, exerciseId: number) => void;
  onReplaceExercise: (sessionId: number, exerciseId: number) => void;
  /** Quick-replace: sostituisci esercizio preservando serie/rip/riposo */
  onQuickReplace?: (sessionId: number, exerciseId: number, newExerciseId: number) => void;
  // ── Block handlers ──
  onAddBlock?: (sessionId: number, tipo: BlockType) => void;
  onUpdateBlock?: (sessionId: number, blockId: number, updates: Partial<BlockCardData>) => void;
  onDeleteBlock?: (sessionId: number, blockId: number) => void;
  onDuplicateBlock?: (sessionId: number, blockId: number) => void;
  onAddExerciseToBlock?: (sessionId: number, blockId: number) => void;
  onUpdateExerciseInBlock?: (sessionId: number, blockId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => void;
  onDeleteExerciseFromBlock?: (sessionId: number, blockId: number, exerciseId: number) => void;
  onReplaceExerciseInBlock?: (sessionId: number, blockId: number, exerciseId: number) => void;
  onQuickReplaceInBlock?: (sessionId: number, blockId: number, exerciseId: number, newExerciseId: number) => void;
  /** Svuota una sezione (esercizi, blocchi, o entrambi) */
  onClearSection?: (sessionId: number, sezione: TemplateSection, what: "exercises" | "blocks" | "all") => void;
}

// ── Session accent colors (per-session colore bordo top) ──

const SESSION_ACCENT = [
  { border: "border-t-primary",     badge: "bg-primary/12 text-primary ring-1 ring-primary/15",                          pill: "bg-primary/8 text-primary" },
  { border: "border-t-blue-500",    badge: "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 ring-1 ring-blue-500/15",    pill: "bg-blue-500/8 text-blue-600 dark:text-blue-400" },
  { border: "border-t-violet-500",  badge: "bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 ring-1 ring-violet-500/15", pill: "bg-violet-500/8 text-violet-600 dark:text-violet-400" },
  { border: "border-t-amber-500",   badge: "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/15",  pill: "bg-amber-500/8 text-amber-600 dark:text-amber-400" },
  { border: "border-t-rose-500",    badge: "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 ring-1 ring-rose-500/15",   pill: "bg-rose-500/8 text-rose-600 dark:text-rose-400" },
  { border: "border-t-emerald-500", badge: "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/15", pill: "bg-emerald-500/8 text-emerald-600 dark:text-emerald-400" },
];

// ── Sezione config ──

const SECTION_CONFIG: Record<TemplateSection, {
  label: string;
  icon: React.ReactNode;
  addLabel: string;
  color: string;
  dividerBg: string;
  sectionBg: string;
}> = {
  avviamento: {
    label: "Avviamento",
    icon: <Flame className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Avviamento",
    color: "text-amber-600 dark:text-amber-400",
    dividerBg: "bg-amber-200 dark:bg-amber-700",
    sectionBg: "bg-amber-50/50 dark:bg-amber-950/20",
  },
  principale: {
    label: "Blocco Serie x Ripetizioni",
    icon: <Dumbbell className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Esercizio",
    color: "text-primary",
    dividerBg: "bg-primary/20",
    sectionBg: "",
  },
  stretching: {
    label: "Stretching & Mobilita",
    icon: <Heart className="h-3.5 w-3.5" />,
    addLabel: "Aggiungi Stretching",
    color: "text-cyan-600 dark:text-cyan-400",
    dividerBg: "bg-cyan-200 dark:bg-cyan-700",
    sectionBg: "bg-cyan-50/50 dark:bg-cyan-950/20",
  },
};

const SECTION_ORDER: TemplateSection[] = ["avviamento", "principale", "stretching"];

// ── ClearSectionButton — bottone "Svuota" per ogni sezione ──

function ClearSectionButton({
  sessionId,
  sezione,
  hasExercises,
  hasBlocks,
  onClear,
}: {
  sessionId: number;
  sezione: TemplateSection;
  hasExercises: boolean;
  hasBlocks: boolean;
  onClear?: (sessionId: number, sezione: TemplateSection, what: "exercises" | "blocks" | "all") => void;
}) {
  if (!onClear) return null;
  if (!hasExercises && !hasBlocks) return null;

  const btnClass = "h-5 w-5 text-muted-foreground/40 hover:text-destructive transition-colors";

  // Principale con entrambi → DropdownMenu
  if (sezione === "principale" && hasExercises && hasBlocks) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className={btnClass}>
            <X className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="text-xs">
          <DropdownMenuItem
            className="text-xs"
            onClick={() => onClear(sessionId, sezione, "exercises")}
          >
            Svuota esercizi
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-xs"
            onClick={() => onClear(sessionId, sezione, "blocks")}
          >
            Svuota blocchi
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-xs text-destructive focus:text-destructive"
            onClick={() => onClear(sessionId, sezione, "all")}
          >
            Svuota tutto
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  // Caso semplice → singolo X
  const what = sezione === "principale" && hasBlocks && !hasExercises ? "blocks" : "exercises";
  return (
    <Button
      variant="ghost"
      size="icon"
      className={btnClass}
      onClick={() => onClear(sessionId, sezione, what)}
      title={`Svuota ${sezione}`}
    >
      <X className="h-3 w-3" />
    </Button>
  );
}

/** Parsa range ripetizioni → media. "8-12" → 10, "5" → 5, "30s" → 0. */
export function parseAvgReps(reps: string): number {
  const range = reps.match(/^(\d+)\s*-\s*(\d+)$/);
  if (range) return (parseInt(range[1]) + parseInt(range[2])) / 2;
  const single = reps.match(/^(\d+)$/);
  if (single) return parseInt(single[1]);
  return 0;
}

export function SessionCard({
  session,
  boardView = false,
  safetyMap,
  exerciseMap,
  schedaId,
  parentFrom,
  oneRMByPattern,
  onUpdateSession,
  onDeleteSession,
  onDuplicateSession,
  onAddExercise,
  onUpdateExercise,
  onDeleteExercise,
  onReplaceExercise,
  onQuickReplace,
  onAddBlock,
  onUpdateBlock,
  onDeleteBlock,
  onDuplicateBlock,
  onAddExerciseToBlock,
  onUpdateExerciseInBlock,
  onDeleteExerciseFromBlock,
  onReplaceExerciseInBlock,
  onQuickReplaceInBlock,
  onClearSection,
}: SessionCardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState(session.nome_sessione);
  const [showNotes, setShowNotes] = useState(!!session.note);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  // Raggruppa esercizi per sezione
  const groupedExercises = useMemo(() => {
    const groups: Record<TemplateSection, WorkoutExerciseRow[]> = {
      avviamento: [],
      principale: [],
      stretching: [],
    };
    for (const ex of session.esercizi) {
      const section = getSectionForCategory(ex.esercizio_categoria);
      groups[section].push(ex);
    }
    return groups;
  }, [session.esercizi]);

  // Volume sessione (solo sezione principale, solo se >= 1 esercizio ha carico)
  const sessionVolume = useMemo(() => {
    const principale = groupedExercises.principale;
    const withLoad = principale.filter((e) => e.carico_kg != null && e.carico_kg > 0);
    if (withLoad.length === 0) return null;
    const total = withLoad.reduce((sum, e) => {
      const reps = parseAvgReps(e.ripetizioni);
      return sum + e.serie * reps * (e.carico_kg ?? 0);
    }, 0);
    return Math.round(total);
  }, [groupedExercises.principale]);

  // Safety pills: contatori avoid/caution/modify per questa sessione (straight + in blocchi)
  const sessionSafety = useMemo(() => {
    if (!safetyMap) return { avoid: 0, caution: 0, modify: 0 };
    let avoid = 0;
    let caution = 0;
    let modify = 0;
    const allExercises = [
      ...session.esercizi,
      ...session.blocchi.flatMap((b) => b.esercizi),
    ];
    for (const ex of allExercises) {
      const entry = safetyMap[ex.id_esercizio];
      if (!entry) continue;
      if (entry.severity === "avoid") avoid++;
      else if (entry.severity === "caution") caution++;
      else modify++;
    }
    return { avoid, caution, modify };
  }, [safetyMap, session.esercizi, session.blocchi]);

  // Auto-derived focus muscolare (top 3 muscoli primari per frequenza)
  const derivedMuscles = useMemo(() => {
    if (!exerciseMap) return [];
    const counts = new Map<string, number>();
    const allExercises = [
      ...session.esercizi,
      ...session.blocchi.flatMap((b) => b.esercizi),
    ];
    for (const ex of allExercises) {
      const data = exerciseMap.get(ex.id_esercizio);
      if (!data?.muscoli_primari) continue;
      for (const m of data.muscoli_primari) {
        counts.set(m, (counts.get(m) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([slug]) => slug);
  }, [exerciseMap, session.esercizi, session.blocchi]);

  // Auto-nome sessione basato sui muscoli dominanti
  const derivedName = useMemo(() => {
    if (derivedMuscles.length === 0) return null;
    const muscleNames = derivedMuscles.map((m) => MUSCLE_LABELS[m] ?? m);
    return `Sessione ${session.numero_sessione} — ${muscleNames.join(", ")}`;
  }, [derivedMuscles, session.numero_sessione]);

  // Template default names da sovrascrivere
  const isTemplateName = useMemo(() => {
    const n = session.nome_sessione.toLowerCase();
    return /^(full body|upper|lower|push|pull|legs|sessione\s+\d)/i.test(n);
  }, [session.nome_sessione]);

  const displayName = isTemplateName && derivedName ? derivedName : session.nome_sessione;

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const activeEx = session.esercizi.find((e) => e.id === active.id);
      const overEx = session.esercizi.find((e) => e.id === over.id);
      if (!activeEx || !overEx) return;

      const activeSection = getSectionForCategory(activeEx.esercizio_categoria);
      const overSection = getSectionForCategory(overEx.esercizio_categoria);

      // Solo riordino dentro la stessa sezione
      if (activeSection !== overSection) return;

      const sectionExs = [...groupedExercises[activeSection]];
      const oldIdx = sectionExs.findIndex((e) => e.id === active.id);
      const newIdx = sectionExs.findIndex((e) => e.id === over.id);
      if (oldIdx === -1 || newIdx === -1) return;

      const reordered = arrayMove(sectionExs, oldIdx, newIdx);

      const fullList = [
        ...(activeSection === "avviamento" ? reordered : groupedExercises.avviamento),
        ...(activeSection === "principale" ? reordered : groupedExercises.principale),
        ...(activeSection === "stretching" ? reordered : groupedExercises.stretching),
      ].map((e, idx) => ({ ...e, ordine: idx + 1 }));

      onUpdateSession(session.id, { esercizi: fullList });
    },
    [session.esercizi, session.id, groupedExercises, onUpdateSession],
  );

  const handleNameSave = useCallback(() => {
    setIsEditingName(false);
    if (editName.trim() && editName !== session.nome_sessione) {
      onUpdateSession(session.id, { nome_sessione: editName.trim() });
    }
  }, [editName, session.id, session.nome_sessione, onUpdateSession]);

  const accent = SESSION_ACCENT[(session.numero_sessione - 1) % SESSION_ACCENT.length];

  return (
    <Card
      className={`transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 border-t-[3px] shadow-sm ${accent.border}`}
      data-workout-session-id={session.id}
      data-workout-session-number={session.numero_sessione}
    >
      <CardHeader className="pb-3 space-y-2">
        {/* Riga 1: badge numero + nome sessione + menu */}
        <div className="flex items-center gap-2.5">
          <div className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm font-extrabold tabular-nums shadow-sm ${accent.badge}`}>
            {session.numero_sessione}
          </div>
          <div className="flex-1 min-w-0 group">
            {isEditingName ? (
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={handleNameSave}
                onKeyDown={(e) => e.key === "Enter" && handleNameSave()}
                className="h-8 text-sm font-bold"
                autoFocus
              />
            ) : (
              <button
                onClick={() => { setEditName(displayName); setIsEditingName(true); }}
                className="flex items-center gap-1.5 text-sm font-bold tracking-tight hover:text-primary transition-colors"
              >
                {displayName}
                {session.note && (
                  <span className="h-1.5 w-1.5 rounded-full bg-primary/70 shrink-0 animate-pulse" />
                )}
                <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-60 transition-opacity" />
              </button>
            )}
            {derivedMuscles.length > 0 ? (
              <div className="flex gap-1 mt-1 flex-wrap">
                {derivedMuscles.map((m) => (
                  <span key={m} className={`text-[10px] font-medium rounded-full px-2 py-0.5 leading-tight ring-1 ring-inset ring-black/[0.04] dark:ring-white/[0.06] ${MUSCLE_COLORS[m] ?? "bg-muted/50 text-muted-foreground/70"}`}>
                    {MUSCLE_LABELS[m] ?? m}
                  </span>
                ))}
              </div>
            ) : session.focus_muscolare ? (
              <p className="text-[11px] text-muted-foreground/80 truncate mt-0.5">{session.focus_muscolare}</p>
            ) : null}
          </div>
          {/* Overflow menu (⋮) */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 text-muted-foreground/50 hover:text-muted-foreground">
                <MoreVertical className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setShowNotes(!showNotes)}>
                <StickyNote className="h-3.5 w-3.5 mr-2" />
                {session.note ? "Modifica note" : "Aggiungi note"}
              </DropdownMenuItem>
              {onDuplicateSession && (
                <DropdownMenuItem onClick={() => onDuplicateSession(session.id)}>
                  <Copy className="h-3.5 w-3.5 mr-2" />
                  Duplica sessione
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDeleteSession(session.id)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5 mr-2" />
                Elimina sessione
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {/* Riga 2: safety pills + volume (sotto il nome, non compressi) */}
        {(sessionSafety.avoid > 0 || sessionSafety.caution > 0 || sessionSafety.modify > 0 || (sessionVolume != null && sessionVolume > 0)) && (
          <div className="flex items-center gap-1.5 flex-wrap pl-[42px]">
            {sessionSafety.avoid > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-red-50 dark:bg-red-950/40 px-2 py-0.5 text-[10px] font-semibold text-red-600 dark:text-red-400 ring-1 ring-red-200/60 dark:ring-red-800/40">
                <ShieldAlert className="h-3 w-3" />
                {sessionSafety.avoid}
              </span>
            )}
            {sessionSafety.modify > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 text-[10px] font-semibold text-blue-600 dark:text-blue-400 ring-1 ring-blue-200/60 dark:ring-blue-800/40">
                <Info className="h-3 w-3" />
                {sessionSafety.modify}
              </span>
            )}
            {sessionSafety.caution > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400 ring-1 ring-amber-200/60 dark:ring-amber-800/40">
                <AlertTriangle className="h-3 w-3" />
                {sessionSafety.caution}
              </span>
            )}
            {sessionVolume != null && sessionVolume > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/8 px-2.5 py-0.5 text-[10px] font-bold text-primary tabular-nums tracking-tight ring-1 ring-primary/10">
                <Dumbbell className="h-2.5 w-2.5" />
                {sessionVolume.toLocaleString("it-IT")} kg
              </span>
            )}
          </div>
        )}
      </CardHeader>

      {/* Note sessione espandibili */}
      {showNotes && (
        <div className="px-6 pb-2">
          <Input
            value={session.note ?? ""}
            onChange={(e) => onUpdateSession(session.id, { note: e.target.value || null })}
            placeholder="Note sessione: RPE target, focus, indicazioni generali..."
            className="h-7 text-xs"
            autoFocus={!session.note}
          />
        </div>
      )}

      <CardContent className="pt-1 space-y-4">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          {SECTION_ORDER.map((sectionKey) => {
            const config = SECTION_CONFIG[sectionKey];
            const exercises = groupedExercises[sectionKey];
            const isPrincipale = sectionKey === "principale";
            const hasBlocks = isPrincipale && session.blocchi.length > 0;
            const hasContent = exercises.length > 0 || hasBlocks;

            // Sezioni vuote auto-collapsed: solo separator + "Aggiungi" inline
            if (!hasContent && !isPrincipale) {
              return (
                <div key={sectionKey}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`inline-flex items-center gap-1.5 ${config.color} text-[10px] font-medium uppercase tracking-widest shrink-0 opacity-40`}>
                      {config.icon} {config.label}
                    </span>
                    <div className={`flex-1 h-px ${config.dividerBg} opacity-25`} />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 px-2 text-[10px] text-muted-foreground hover:text-primary"
                      onClick={() => onAddExercise(session.id, sectionKey)}
                    >
                      <Plus className="mr-0.5 h-2.5 w-2.5" />
                      {config.addLabel}
                    </Button>
                  </div>
                </div>
              );
            }

            const itemCount = exercises.length + (hasBlocks ? session.blocchi.length : 0);

            return (
              <div key={sectionKey}>
                {/* ── Section separator: label badge + linea colorata ── */}
                <div className="flex items-center gap-2 mb-2.5">
                  <span className={`inline-flex items-center gap-1.5 ${config.color} text-[10px] font-semibold uppercase tracking-widest shrink-0`}>
                    {config.icon} {config.label}
                    {hasContent && (
                      <span className="inline-flex items-center justify-center h-4 min-w-4 rounded-full bg-muted/80 text-[9px] font-bold text-muted-foreground tabular-nums px-1">
                        {itemCount}
                      </span>
                    )}
                  </span>
                  <div className={`flex-1 h-px ${config.dividerBg}`} />
                  {/* Svuota button */}
                  <ClearSectionButton
                    sessionId={session.id}
                    sezione={sectionKey}
                    hasExercises={exercises.length > 0}
                    hasBlocks={hasBlocks}
                    onClear={onClearSection}
                  />
                </div>

                {/* ── Section body ── */}
                <div className={`pl-2 ${config.sectionBg ? `${config.sectionBg} rounded-lg py-2 -mx-1 px-3` : ""}`}>
                  {/* Empty state — sessione vuota */}
                  {isPrincipale && exercises.length === 0 && session.blocchi.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-muted/40 mb-2.5 ring-1 ring-border/50">
                        <Dumbbell className="h-5 w-5 text-muted-foreground/40" />
                      </div>
                      <p className="text-[11px] text-muted-foreground/60 font-medium">Aggiungi il primo esercizio</p>
                    </div>
                  )}
                  {/* Exercise rows */}
                  {exercises.length > 0 && (
                    <>
                      {/* Column header — nascosto in board view (spazio troppo stretto) */}
                      {!boardView && (
                        <div className={`grid ${isPrincipale
                          ? "grid-cols-[20px_14px_1fr_44px_52px_52px_44px_24px]"
                          : "grid-cols-[20px_14px_1fr_44px_52px_24px]"
                        } gap-1 px-1 pb-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wider`}>
                          <span />
                          <span />
                          <span>Esercizio</span>
                          <span className="text-center">Serie</span>
                          <span className="text-center">Rip</span>
                          {isPrincipale && (
                            <>
                              <span className="text-center">Kg</span>
                              <span className="text-center">Riposo</span>
                            </>
                          )}
                          <span />
                        </div>
                      )}

                      <SortableContext
                        items={exercises.map((e) => e.id)}
                        strategy={verticalListSortingStrategy}
                      >
                        <div className="space-y-1.5">
                          {exercises.map((exercise) => (
                            <SortableExerciseRow
                              key={exercise.id}
                              exercise={exercise}
                              compact={!isPrincipale}
                              boardView={boardView}
                              safety={safetyMap?.[exercise.id_esercizio]}
                              safetyEntries={safetyMap}
                              exerciseData={exerciseMap?.get(exercise.id_esercizio)}
                              exerciseMap={exerciseMap}
                              schedaId={schedaId}
                              parentFrom={parentFrom}
                              oneRMByPattern={isPrincipale ? oneRMByPattern : undefined}
                              onUpdate={(updates) => onUpdateExercise(session.id, exercise.id, updates)}
                              onDelete={() => onDeleteExercise(session.id, exercise.id)}
                              onReplace={() => onReplaceExercise(session.id, exercise.id)}
                              onQuickReplace={onQuickReplace ? (newId) => onQuickReplace(session.id, exercise.id, newId) : undefined}
                            />
                          ))}
                        </div>
                      </SortableContext>
                    </>
                  )}

                  {/* Add button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="mt-2 w-full text-[11px] text-muted-foreground/70 hover:text-primary h-7 border border-dashed border-muted-foreground/15 hover:border-primary/30 hover:bg-primary/[0.03] rounded-lg transition-all duration-200"
                    onClick={() => onAddExercise(session.id, sectionKey)}
                  >
                    <Plus className="mr-1 h-3 w-3" />
                    {config.addLabel}
                  </Button>

                  {/* ── Blocchi strutturati — solo nella sezione principale ── */}
                  {isPrincipale && session.blocchi.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {session.blocchi
                        .slice()
                        .sort((a, b) => a.ordine - b.ordine)
                        .map((block) => (
                          <BlockCard
                            key={block.id}
                            block={block}
                            sessionId={session.id}
                            safetyMap={safetyMap}
                            exerciseMap={exerciseMap}
                            schedaId={schedaId}
                            parentFrom={parentFrom}
                            oneRMByPattern={oneRMByPattern}
                            onUpdateBlock={(blockId, updates) => onUpdateBlock?.(session.id, blockId, updates)}
                            onDeleteBlock={(blockId) => onDeleteBlock?.(session.id, blockId)}
                            onDuplicateBlock={onDuplicateBlock ? (blockId) => onDuplicateBlock(session.id, blockId) : undefined}
                            onAddExerciseToBlock={(blockId) => onAddExerciseToBlock?.(session.id, blockId)}
                            onUpdateExerciseInBlock={(blockId, exId, updates) => onUpdateExerciseInBlock?.(session.id, blockId, exId, updates)}
                            onDeleteExerciseFromBlock={(blockId, exId) => onDeleteExerciseFromBlock?.(session.id, blockId, exId)}
                            onReplaceExerciseInBlock={(blockId, exId) => onReplaceExerciseInBlock?.(session.id, blockId, exId)}
                            onQuickReplaceInBlock={onQuickReplaceInBlock
                              ? (blockId, exId, newId) => onQuickReplaceInBlock(session.id, blockId, exId, newId)
                              : undefined}
                          />
                        ))}
                    </div>
                  )}

                  {/* ── Aggiungi Blocco — solo nella sezione principale ── */}
                  {isPrincipale && onAddBlock && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {(["circuit", "superset", "tabata", "amrap", "emom", "for_time"] as BlockType[]).map((tipo) => (
                        <Button
                          key={tipo}
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[10px] text-muted-foreground hover:text-violet-600 dark:hover:text-violet-400"
                          onClick={() => onAddBlock(session.id, tipo)}
                        >
                          <Layers className="mr-1 h-3 w-3" />
                          + {tipo.toUpperCase()}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </DndContext>
      </CardContent>
    </Card>
  );
}
