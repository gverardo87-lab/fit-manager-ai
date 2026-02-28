// src/components/workouts/SortableExerciseRow.tsx
"use client";

/**
 * Singola riga esercizio sortabile dentro una SessionCard.
 *
 * Due layout (entrambi snelli):
 * - compact=true: avviamento/stretching — 6 colonne (grip, info, nome, serie, rip, delete)
 * - compact=false: principale — 8 colonne (+ kg + riposo)
 *
 * Info icon: espande pannello unificato (nota + tempo + ExerciseDetailPanel).
 * Safety: icona cliccabile apre Popover ricco con condizioni dettagliate.
 * Dot indicator: teal dot accanto al nome se esercizio ha note/tempo compilati.
 */

import { useState, useMemo } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, ShieldAlert, AlertTriangle, ArrowRightLeft, CheckCircle2, Info, RefreshCw } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";

import { useExerciseRelations } from "@/hooks/useExercises";
import { ExerciseDetailPanel } from "./ExerciseDetailPanel";
import type { WorkoutExerciseRow, ExerciseSafetyEntry, Exercise } from "@/types/api";

const RELATION_LABELS: Record<string, string> = {
  regression: "Regressione",
  variation: "Variante",
  progression: "Progressione",
};

interface SortableExerciseRowProps {
  exercise: WorkoutExerciseRow;
  /** Layout compatto per avviamento/stretching */
  compact?: boolean;
  /** Safety entry da anamnesi cliente (informativo) */
  safety?: ExerciseSafetyEntry;
  /** Full safety entries per filtrare alternative sicure */
  safetyEntries?: Record<number, ExerciseSafetyEntry>;
  /** Dati esercizio completi dal exerciseMap (per pannello inline) */
  exerciseData?: Exercise;
  /** ID scheda per deep-link ritorno */
  schedaId?: number;
  /** Mappa pattern_movimento → valore 1RM cliente (per badge % 1RM) */
  oneRMByPattern?: Record<string, number> | null;
  onUpdate: (updates: Partial<WorkoutExerciseRow>) => void;
  onDelete: () => void;
  onReplace: () => void;
  /** Quick-replace: sostituisci con un altro esercizio (preserva serie/rip/riposo) */
  onQuickReplace?: (newExerciseId: number) => void;
}

function SafetyPopover({
  safety,
  exerciseName,
  exerciseId,
  iconSize,
  safetyEntries,
  onQuickReplace,
}: {
  safety: ExerciseSafetyEntry;
  exerciseName: string;
  exerciseId: number;
  iconSize: string;
  safetyEntries?: Record<number, ExerciseSafetyEntry>;
  onQuickReplace?: (newExerciseId: number) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: relations } = useExerciseRelations(isOpen ? exerciseId : null);

  const safeAlternatives = useMemo(() => {
    if (!relations || !safetyEntries) return [];
    return relations
      .filter((rel) => {
        const entry = safetyEntries[rel.related_exercise_id];
        return !entry || entry.severity !== "avoid";
      })
      .map((rel) => ({
        id: rel.related_exercise_id,
        nome: rel.related_exercise_nome,
        tipo: rel.tipo_relazione,
        hasCaution: !!safetyEntries[rel.related_exercise_id],
      }));
  }, [relations, safetyEntries]);

  const SafetyIcon = safety.severity === "avoid" ? ShieldAlert : AlertTriangle;
  const dotColor = safety.severity === "avoid" ? "bg-red-500" : "bg-amber-500";

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={`shrink-0 ${safety.severity === "avoid" ? "text-red-500" : "text-amber-500"} hover:scale-110 transition-transform`}
        >
          <SafetyIcon className={iconSize} />
        </button>
      </PopoverTrigger>
      <PopoverContent side="right" align="start" className="w-72 p-0">
        {/* Header */}
        <div className="px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full shrink-0 ${dotColor}`} />
            <span className="text-sm font-semibold truncate">{exerciseName}</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 ml-4">
            {safety.conditions.length} condizion{safety.conditions.length === 1 ? "e rilevante" : "i rilevanti"}
          </p>
        </div>
        <Separator />
        {/* Conditions list */}
        <div className="px-3 py-2 space-y-2.5">
          {safety.conditions.map((cond) => (
            <div key={cond.id}>
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-semibold uppercase tracking-wider ${cond.severita === "avoid" ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"}`}>
                  {cond.severita === "avoid" ? "Evitare" : "Cautela"}
                </span>
              </div>
              <p className="text-xs font-medium mt-0.5">{cond.nome}</p>
              {cond.nota && (
                <p className="text-[11px] text-muted-foreground leading-relaxed mt-0.5">{cond.nota}</p>
              )}
            </div>
          ))}
        </div>
        {/* Safe alternatives */}
        {safeAlternatives.length > 0 && (
          <>
            <Separator />
            <div className="px-3 py-2">
              <div className="flex items-center gap-1.5 mb-1.5">
                <ArrowRightLeft className="h-3 w-3 text-primary" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-primary">
                  Alternative sicure
                </span>
              </div>
              <div className="space-y-1">
                {safeAlternatives.map((alt) => (
                  <div key={`${alt.id}-${alt.tipo}`} className="flex items-center gap-1.5 text-[11px]">
                    <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
                    <span className="flex-1 truncate">{alt.nome}</span>
                    <span className="text-[9px] text-muted-foreground shrink-0">
                      {RELATION_LABELS[alt.tipo] ?? alt.tipo}
                    </span>
                    {onQuickReplace && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 px-1.5 text-[10px] text-primary hover:text-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          onQuickReplace(alt.id);
                          setIsOpen(false);
                        }}
                      >
                        <RefreshCw className="h-2.5 w-2.5 mr-0.5" />
                        Sostituisci
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </PopoverContent>
    </Popover>
  );
}

export function SortableExerciseRow({
  exercise,
  compact = false,
  safety,
  safetyEntries,
  exerciseData,
  schedaId,
  oneRMByPattern,
  onUpdate,
  onDelete,
  onReplace,
  onQuickReplace,
}: SortableExerciseRowProps) {
  const [expanded, setExpanded] = useState(false);

  // % 1RM (solo principale, solo se carico + 1RM disponibili)
  const percentOneRM = useMemo(() => {
    if (!oneRMByPattern || !exercise.carico_kg || exercise.carico_kg <= 0) return null;
    const pattern = exerciseData?.pattern_movimento;
    if (!pattern) return null;
    const oneRM = oneRMByPattern[pattern];
    if (!oneRM || oneRM <= 0) return null;
    return Math.round((exercise.carico_kg / oneRM) * 100);
  }, [oneRMByPattern, exercise.carico_kg, exerciseData?.pattern_movimento]);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: exercise.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // Background tint per severity
  const safetyBg = safety?.severity === "avoid"
    ? "bg-red-50/60 dark:bg-red-950/20"
    : safety?.severity === "caution"
      ? "bg-amber-50/60 dark:bg-amber-950/20"
      : "";

  // Indicatore contenuto secondario (nota o tempo compilati)
  const hasSecondaryContent = !!exercise.note || !!exercise.tempo_esecuzione;

  if (compact) {
    return (
      <div ref={setNodeRef} style={style}>
        <div
          className={`group/row grid grid-cols-[20px_14px_1fr_44px_52px_24px] gap-1 items-center rounded-md px-1 py-1 hover:bg-muted/40 transition-colors ${safetyBg}`}
        >
          {/* Drag handle */}
          <button
            {...attributes}
            {...listeners}
            className="flex items-center justify-center cursor-grab active:cursor-grabbing text-muted-foreground/50 hover:text-muted-foreground"
          >
            <GripVertical className="h-3.5 w-3.5" />
          </button>

          {/* Info icon — espande pannello unificato */}
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className={`flex items-center justify-center transition-colors ${expanded ? "text-primary" : "text-muted-foreground/40 hover:text-muted-foreground"}`}
          >
            <Info className="h-3 w-3" />
          </button>

          {/* Nome esercizio + safety icon + dot indicator */}
          <div className="flex items-center gap-1 min-w-0">
            {safety && (
              <SafetyPopover safety={safety} exerciseName={exercise.esercizio_nome} exerciseId={exercise.id_esercizio} iconSize="h-3 w-3" safetyEntries={safetyEntries} onQuickReplace={onQuickReplace} />
            )}
            <button
              onClick={onReplace}
              className="text-left text-xs truncate hover:text-primary transition-colors"
              title={`${exercise.esercizio_nome} — clicca per sostituire`}
            >
              {exercise.esercizio_nome}
            </button>
            {hasSecondaryContent && (
              <span className="shrink-0 h-1.5 w-1.5 rounded-full bg-primary/60" />
            )}
          </div>

          {/* Serie */}
          <Input
            type="number"
            value={exercise.serie}
            onChange={(e) => onUpdate({ serie: parseInt(e.target.value) || 1 })}
            min={1}
            max={10}
            className="h-6 text-center text-[11px] px-1"
          />

          {/* Ripetizioni */}
          <Input
            value={exercise.ripetizioni}
            onChange={(e) => onUpdate({ ripetizioni: e.target.value })}
            className="h-6 text-center text-[11px] px-1"
            placeholder="30s"
          />

          {/* Delete — semi-trasparente, visibile su hover */}
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-muted-foreground/0 group-hover/row:text-muted-foreground/50 hover:!text-destructive transition-colors"
            onClick={onDelete}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>

        {/* Pannello espandibile unificato: nota + dettagli */}
        {expanded && (
          <div className="ml-[34px] mr-1 mt-0.5 mb-1 space-y-1.5">
            {/* Nota input */}
            <Input
              value={exercise.note ?? ""}
              onChange={(e) => onUpdate({ note: e.target.value || null })}
              placeholder="Es: 30s per lato, focus respirazione..."
              className="h-6 text-xs"
            />
            {/* Detail panel */}
            {exerciseData && (
              <ExerciseDetailPanel
                exercise={exerciseData}
                exerciseId={exercise.id_esercizio}
                safety={safety}
                safetyEntries={safetyEntries}
                schedaId={schedaId}
                onQuickReplace={onQuickReplace}
              />
            )}
          </div>
        )}
      </div>
    );
  }

  // ── Layout principale (8 colonne) ──

  return (
    <div ref={setNodeRef} style={style}>
      <div
        className={`group/row grid grid-cols-[20px_14px_1fr_44px_52px_52px_44px_24px] gap-1 items-center rounded-md px-1 py-1 hover:bg-muted/40 transition-colors ${safetyBg}`}
      >
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="flex items-center justify-center cursor-grab active:cursor-grabbing text-muted-foreground/50 hover:text-muted-foreground"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>

        {/* Info icon — espande pannello unificato */}
        <button
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          className={`flex items-center justify-center transition-colors ${expanded ? "text-primary" : "text-muted-foreground/40 hover:text-muted-foreground"}`}
        >
          <Info className="h-3 w-3" />
        </button>

        {/* Nome esercizio + safety icon + dot indicator */}
        <div className="flex items-center gap-1 min-w-0">
          {safety && (
            <SafetyPopover safety={safety} exerciseName={exercise.esercizio_nome} exerciseId={exercise.id_esercizio} iconSize="h-3 w-3" safetyEntries={safetyEntries} onQuickReplace={onQuickReplace} />
          )}
          <button
            onClick={onReplace}
            className="text-left text-sm truncate hover:text-primary transition-colors"
            title={`${exercise.esercizio_nome} — clicca per sostituire`}
          >
            {exercise.esercizio_nome}
          </button>
          {hasSecondaryContent && (
            <span className="shrink-0 h-1.5 w-1.5 rounded-full bg-primary/60" />
          )}
        </div>

        {/* Serie */}
        <Input
          type="number"
          value={exercise.serie}
          onChange={(e) => onUpdate({ serie: parseInt(e.target.value) || 1 })}
          min={1}
          max={10}
          className="h-6 text-center text-[11px] px-1"
        />

        {/* Ripetizioni */}
        <Input
          value={exercise.ripetizioni}
          onChange={(e) => onUpdate({ ripetizioni: e.target.value })}
          className="h-6 text-center text-[11px] px-1"
          placeholder="8-12"
        />

        {/* Carico kg + % 1RM badge */}
        <div className="flex flex-col items-center">
          <Input
            type="number"
            value={exercise.carico_kg ?? ""}
            onChange={(e) => onUpdate({
              carico_kg: e.target.value ? parseFloat(e.target.value) : null,
            })}
            min={0}
            max={500}
            step={0.5}
            className="h-6 text-center text-[11px] px-1"
            placeholder="—"
          />
          {percentOneRM != null && (
            <span className="text-[9px] text-muted-foreground tabular-nums mt-0.5">
              {percentOneRM}% 1RM
            </span>
          )}
        </div>

        {/* Tempo riposo */}
        <Input
          type="number"
          value={exercise.tempo_riposo_sec}
          onChange={(e) => onUpdate({ tempo_riposo_sec: parseInt(e.target.value) || 0 })}
          min={0}
          max={300}
          step={15}
          className="h-6 text-center text-[11px] px-1"
        />

        {/* Delete — semi-trasparente, visibile su hover */}
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5 text-muted-foreground/0 group-hover/row:text-muted-foreground/50 hover:!text-destructive transition-colors"
          onClick={onDelete}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      {/* Pannello espandibile unificato: nota + tempo esecuzione + dettagli */}
      {expanded && (
        <div className="ml-[34px] mr-1 mt-0.5 mb-1 space-y-1.5">
          {/* Nota + Tempo inline */}
          <div className="flex gap-1.5">
            <Input
              value={exercise.note ?? ""}
              onChange={(e) => onUpdate({ note: e.target.value || null })}
              placeholder="Nota: presa supina, pausa 2s, RPE 8..."
              className="h-6 text-xs flex-1"
            />
            <Input
              value={exercise.tempo_esecuzione ?? ""}
              onChange={(e) => onUpdate({ tempo_esecuzione: e.target.value || null })}
              className="h-6 text-[11px] text-center w-20"
              placeholder="Tempo 3-1-2-0"
            />
          </div>
          {/* Detail panel */}
          {exerciseData && (
            <ExerciseDetailPanel
              exercise={exerciseData}
              exerciseId={exercise.id_esercizio}
              safety={safety}
              safetyEntries={safetyEntries}
              schedaId={schedaId}
              onQuickReplace={onQuickReplace}
            />
          )}
        </div>
      )}
    </div>
  );
}
