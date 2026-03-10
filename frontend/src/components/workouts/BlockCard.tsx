// src/components/workouts/BlockCard.tsx
"use client";

/**
 * BlockCard — Blocco strutturato nel builder schede allenamento.
 *
 * Supporta 6 formati (Phase 1):
 *   circuit   — N esercizi × X giri, riposo programmato tra stazioni
 *   superset  — 2+ esercizi abbinati, X serie, mini-riposo
 *   tabata    — 8 round 20s lavoro / 10s riposo (parametri modificabili)
 *   amrap     — As Many Rounds As Possible in N minuti
 *   emom      — Every Minute On the Minute, N minuti
 *   for_time  — X giri il prima possibile
 *
 * Ogni formato mostra solo i campi pertinenti (UI contestuale).
 * Esercizi dentro il blocco condividono le impostazioni del blocco (giri, work/rest).
 * DnD: esercizi riordinabili dentro il blocco via @dnd-kit/sortable.
 */

import { useCallback, useState } from "react";
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
import {
  Zap, RotateCcw, Timer, Trophy, Clock, Flame,
  Plus, Trash2, ChevronDown, GripVertical, StickyNote, Copy,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

import { SortableExerciseRow, BLOCK_EXERCISE_CONFIG } from "./SortableExerciseRow";
import type { BlockType, WorkoutExerciseRow, ExerciseSafetyEntry, Exercise } from "@/types/api";
import { BLOCK_TYPE_LABELS } from "@/types/api";

// ── Mutable local representation di un blocco (con id negativo per nuovi blocchi)
export interface BlockCardData {
  id: number;
  tipo_blocco: BlockType;
  ordine: number;
  nome: string | null;
  giri: number;
  durata_lavoro_sec: number | null;
  durata_riposo_sec: number | null;
  durata_blocco_sec: number | null;
  note: string | null;
  esercizi: WorkoutExerciseRow[];
}

interface BlockCardProps {
  block: BlockCardData;
  sessionId: number;
  safetyMap?: Record<number, ExerciseSafetyEntry>;
  exerciseMap?: Map<number, Exercise>;
  schedaId?: number;
  parentFrom?: string | null;
  oneRMByPattern?: Record<string, number> | null;
  onUpdateBlock: (blockId: number, updates: Partial<BlockCardData>) => void;
  onDeleteBlock: (blockId: number) => void;
  onDuplicateBlock?: (blockId: number) => void;
  onAddExerciseToBlock: (blockId: number) => void;
  onUpdateExerciseInBlock: (blockId: number, exerciseId: number, updates: Partial<WorkoutExerciseRow>) => void;
  onDeleteExerciseFromBlock: (blockId: number, exerciseId: number) => void;
  onReplaceExerciseInBlock: (blockId: number, exerciseId: number) => void;
  onQuickReplaceInBlock?: (blockId: number, exerciseId: number, newExerciseId: number) => void;
}

// ── Configurazione visiva per tipo blocco ──

const BLOCK_CONFIG: Record<BlockType, {
  icon: React.ReactNode;
  color: string;
  bg: string;
  border: string;
  defaultGiri: number;
  defaultLavoroSec: number | null;
  defaultRiposoSec: number | null;
  defaultBloccoDurSec: number | null;
  showGiri: boolean;
  showLavoro: boolean;
  showRiposo: boolean;
  showDurata: boolean;
  girlLabel: string;
  lavoroLabel: string;
  riposoLabel: string;
  durataLabel: string;
  hint: string;
}> = {
  circuit: {
    icon: <RotateCcw className="h-3.5 w-3.5" />,
    color: "text-violet-600 dark:text-violet-400",
    bg: "bg-violet-50 dark:bg-violet-950/30",
    border: "border-l-violet-400",
    defaultGiri: 3,
    defaultLavoroSec: null,
    defaultRiposoSec: 15,
    defaultBloccoDurSec: null,
    showGiri: true, showLavoro: false, showRiposo: true, showDurata: false,
    girlLabel: "Giri",
    lavoroLabel: "Lavoro",
    riposoLabel: "Riposo/stazione",
    durataLabel: "Durata",
    hint: "Esegui tutti gli esercizi in sequenza × Giri. Riposo breve tra stazioni.",
  },
  superset: {
    icon: <Zap className="h-3.5 w-3.5" />,
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-l-amber-400",
    defaultGiri: 3,
    defaultLavoroSec: null,
    defaultRiposoSec: 10,
    defaultBloccoDurSec: null,
    showGiri: true, showLavoro: false, showRiposo: true, showDurata: false,
    girlLabel: "Serie",
    lavoroLabel: "Lavoro",
    riposoLabel: "Riposo/es.",
    durataLabel: "Durata",
    hint: "2 esercizi back-to-back × Serie. Riposo minimo tra i due.",
  },
  tabata: {
    icon: <Timer className="h-3.5 w-3.5" />,
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-l-red-400",
    defaultGiri: 8,
    defaultLavoroSec: 20,
    defaultRiposoSec: 10,
    defaultBloccoDurSec: null,
    showGiri: true, showLavoro: true, showRiposo: true, showDurata: false,
    girlLabel: "Round",
    lavoroLabel: "Lavoro (s)",
    riposoLabel: "Riposo (s)",
    durataLabel: "Durata",
    hint: "Protocollo 20s/10s × 8 round (4 min). Intensità massimale.",
  },
  amrap: {
    icon: <Trophy className="h-3.5 w-3.5" />,
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-l-emerald-400",
    defaultGiri: 1,
    defaultLavoroSec: null,
    defaultRiposoSec: null,
    defaultBloccoDurSec: 720,
    showGiri: false, showLavoro: false, showRiposo: false, showDurata: true,
    girlLabel: "Giri",
    lavoroLabel: "Lavoro",
    riposoLabel: "Riposo",
    durataLabel: "Durata totale (min)",
    hint: "Quanti giri completi riesci in N minuti. No riposo programmato.",
  },
  emom: {
    icon: <Clock className="h-3.5 w-3.5" />,
    color: "text-teal-600 dark:text-teal-400",
    bg: "bg-teal-50 dark:bg-teal-950/30",
    border: "border-l-teal-400",
    defaultGiri: 10,
    defaultLavoroSec: 40,
    defaultRiposoSec: null,
    defaultBloccoDurSec: 600,
    showGiri: true, showLavoro: true, showRiposo: false, showDurata: true,
    girlLabel: "Minuti",
    lavoroLabel: "Lavoro/min (s)",
    riposoLabel: "Riposo",
    durataLabel: "Durata totale (min)",
    hint: "Ogni minuto: esegui gli esercizi, il tempo rimanente è riposo.",
  },
  for_time: {
    icon: <Flame className="h-3.5 w-3.5" />,
    color: "text-orange-600 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-950/30",
    border: "border-l-orange-400",
    defaultGiri: 5,
    defaultLavoroSec: null,
    defaultRiposoSec: null,
    defaultBloccoDurSec: null,
    showGiri: true, showLavoro: false, showRiposo: false, showDurata: false,
    girlLabel: "Giri",
    lavoroLabel: "Lavoro",
    riposoLabel: "Riposo",
    durataLabel: "Durata",
    hint: "Completa tutti i giri nel minor tempo possibile.",
  },
};

// ── Formattazione durata in minuti per AMRAP/EMOM ──
function secToMin(sec: number | null): string {
  if (!sec) return "";
  return String(Math.round(sec / 60));
}
function minToSec(min: string): number | null {
  const n = parseInt(min);
  return isNaN(n) || n <= 0 ? null : n * 60;
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function BlockCard({
  block,
  sessionId: _sessionId,
  safetyMap,
  exerciseMap,
  schedaId,
  parentFrom,
  oneRMByPattern,
  onUpdateBlock,
  onDeleteBlock,
  onDuplicateBlock,
  onAddExerciseToBlock,
  onUpdateExerciseInBlock,
  onDeleteExerciseFromBlock,
  onReplaceExerciseInBlock,
  onQuickReplaceInBlock,
}: BlockCardProps) {
  const [showNotes, setShowNotes] = useState(!!block.note);
  const [isOpen, setIsOpen] = useState(true);

  const config = BLOCK_CONFIG[block.tipo_blocco];
  const blockExCfg = BLOCK_EXERCISE_CONFIG[block.tipo_blocco];

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;
      const oldIdx = block.esercizi.findIndex((e) => e.id === active.id);
      const newIdx = block.esercizi.findIndex((e) => e.id === over.id);
      if (oldIdx === -1 || newIdx === -1) return;
      const reordered = arrayMove(block.esercizi, oldIdx, newIdx)
        .map((e, i) => ({ ...e, ordine: i + 1 }));
      onUpdateBlock(block.id, { esercizi: reordered });
    },
    [block.esercizi, block.id, onUpdateBlock],
  );

  // Change tipo_blocco → apply smart defaults for the new type
  const handleTypeChange = useCallback(
    (newType: BlockType) => {
      const newConfig = BLOCK_CONFIG[newType];
      onUpdateBlock(block.id, {
        tipo_blocco: newType,
        giri: newConfig.defaultGiri,
        durata_lavoro_sec: newConfig.defaultLavoroSec,
        durata_riposo_sec: newConfig.defaultRiposoSec,
        durata_blocco_sec: newConfig.defaultBloccoDurSec,
      });
    },
    [block.id, onUpdateBlock],
  );

  return (
    <Card
      className={`border-l-4 ${config.border} transition-all duration-200`}
      data-workout-block-id={block.id}
    >
      <CardHeader className="pb-2 pt-3 px-4">
        {/* ── Block Header ── */}
        <div className="flex items-center gap-2">
          {/* Grip */}
          <div className="cursor-grab text-muted-foreground/40 shrink-0">
            <GripVertical className="h-4 w-4" />
          </div>

          {/* Type badge + selector */}
          <div className="flex items-center gap-1.5 min-w-0 flex-1">
            <span className={`shrink-0 ${config.color}`}>{config.icon}</span>
            <Select
              value={block.tipo_blocco}
              onValueChange={(v) => handleTypeChange(v as BlockType)}
            >
              <SelectTrigger className={`h-6 px-2 text-xs font-semibold w-auto border-0 ${config.bg} ${config.color} hover:opacity-80`}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent position="popper">
                {Object.entries(BLOCK_TYPE_LABELS).map(([type, label]) => (
                  <SelectItem key={type} value={type} className="text-xs">
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Nome opzionale */}
            <Input
              value={block.nome ?? ""}
              onChange={(e) => onUpdateBlock(block.id, { nome: e.target.value || null })}
              placeholder="Nome blocco (opzionale)"
              className="h-6 flex-1 text-xs border-0 bg-transparent px-1 placeholder:text-muted-foreground/40"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground/50 hover:text-muted-foreground"
              onClick={() => setShowNotes(!showNotes)}
              title="Note blocco"
            >
              <StickyNote className="h-3.5 w-3.5" />
            </Button>
            {onDuplicateBlock && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground/50 hover:text-primary"
                onClick={() => onDuplicateBlock(block.id)}
                title="Duplica blocco"
              >
                <Copy className="h-3.5 w-3.5" />
              </Button>
            )}
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground/50">
                  <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground/40 hover:text-destructive"
              onClick={() => onDeleteBlock(block.id)}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* ── Block Params (contestuali per formato) ── */}
        <div className={`mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs ${config.bg} rounded-lg px-3 py-2`}>
          {/* Giri / Round / Serie / Minuti */}
          {config.showGiri && (
            <div className="flex items-center gap-1.5">
              <Label className={`text-[10px] font-semibold uppercase tracking-wider ${config.color}`}>
                {config.girlLabel}
              </Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={block.giri}
                onChange={(e) => onUpdateBlock(block.id, { giri: parseInt(e.target.value) || 1 })}
                className="h-6 w-12 text-xs text-center px-1"
                onWheel={(e) => (e.target as HTMLInputElement).blur()}
              />
            </div>
          )}

          {/* Durata lavoro (Tabata, EMOM) */}
          {config.showLavoro && (
            <div className="flex items-center gap-1.5">
              <Label className={`text-[10px] font-semibold uppercase tracking-wider ${config.color}`}>
                {config.lavoroLabel}
              </Label>
              <Input
                type="number"
                min={5}
                max={600}
                value={block.durata_lavoro_sec ?? ""}
                onChange={(e) => onUpdateBlock(block.id, { durata_lavoro_sec: parseInt(e.target.value) || null })}
                className="h-6 w-14 text-xs text-center px-1"
                onWheel={(e) => (e.target as HTMLInputElement).blur()}
              />
            </div>
          )}

          {/* Riposo tra stazioni (circuit, superset, tabata) */}
          {config.showRiposo && (
            <div className="flex items-center gap-1.5">
              <Label className={`text-[10px] font-semibold uppercase tracking-wider ${config.color}`}>
                {config.riposoLabel}
              </Label>
              <Input
                type="number"
                min={0}
                max={300}
                value={block.durata_riposo_sec ?? ""}
                onChange={(e) => onUpdateBlock(block.id, { durata_riposo_sec: parseInt(e.target.value) || null })}
                className="h-6 w-14 text-xs text-center px-1"
                onWheel={(e) => (e.target as HTMLInputElement).blur()}
              />
            </div>
          )}

          {/* Durata totale in minuti (AMRAP, EMOM) */}
          {config.showDurata && (
            <div className="flex items-center gap-1.5">
              <Label className={`text-[10px] font-semibold uppercase tracking-wider ${config.color}`}>
                {config.durataLabel}
              </Label>
              <Input
                type="number"
                min={1}
                max={120}
                value={secToMin(block.durata_blocco_sec)}
                onChange={(e) => onUpdateBlock(block.id, { durata_blocco_sec: minToSec(e.target.value) })}
                className="h-6 w-14 text-xs text-center px-1"
                onWheel={(e) => (e.target as HTMLInputElement).blur()}
              />
            </div>
          )}

          {/* Hint formato */}
          <p className="text-[10px] text-muted-foreground italic ml-auto hidden sm:block">
            {config.hint}
          </p>
        </div>

        {/* Note blocco */}
        {showNotes && (
          <Input
            value={block.note ?? ""}
            onChange={(e) => onUpdateBlock(block.id, { note: e.target.value || null })}
            placeholder="Note blocco..."
            className="mt-2 h-7 text-xs"
          />
        )}
      </CardHeader>

      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleContent>
          <CardContent className="px-4 pb-3 pt-0 space-y-1">
            {/* ── Esercizi dentro il blocco ── */}
            {block.esercizi.length === 0 ? (
              <div className="rounded-lg border border-dashed py-4 text-center">
                <p className="text-xs text-muted-foreground">
                  Aggiungi esercizi al {BLOCK_TYPE_LABELS[block.tipo_blocco]}
                </p>
              </div>
            ) : (
              <>
                {/* Header colonne — solo per formati con dati per esercizio (non tabata) */}
                {(blockExCfg.showRip || blockExCfg.showKg) && (
                  <div className={`grid ${blockExCfg.gridCols} gap-1 items-center px-1 pb-0.5`}>
                    <span />
                    <span />
                    <span className="text-[10px] text-muted-foreground">Esercizio</span>
                    {blockExCfg.showRip && (
                      <span className="text-[10px] text-muted-foreground text-center">
                        {blockExCfg.ripLabel}
                      </span>
                    )}
                    {blockExCfg.showKg && (
                      <span className="text-[10px] text-muted-foreground text-center">Kg</span>
                    )}
                    <span />
                  </div>
                )}
                <DndContext
                  sensors={sensors}
                  collisionDetection={closestCenter}
                  onDragEnd={handleDragEnd}
                >
                  <SortableContext
                    items={block.esercizi.map((e) => e.id)}
                    strategy={verticalListSortingStrategy}
                  >
                    {block.esercizi.map((ex, idx) => (
                      <SortableExerciseRow
                        key={ex.id}
                        exercise={ex}
                        compact={false}
                        blockType={block.tipo_blocco}
                        blockPosition={idx}
                        safety={safetyMap?.[ex.id_esercizio]}
                        safetyEntries={safetyMap}
                        exerciseData={exerciseMap?.get(ex.id_esercizio)}
                        schedaId={schedaId}
                        parentFrom={parentFrom}
                        oneRMByPattern={oneRMByPattern}
                        onUpdate={(updates) => onUpdateExerciseInBlock(block.id, ex.id, updates)}
                        onDelete={() => onDeleteExerciseFromBlock(block.id, ex.id)}
                        onReplace={() => onReplaceExerciseInBlock(block.id, ex.id)}
                        onQuickReplace={
                          onQuickReplaceInBlock
                            ? (newId) => onQuickReplaceInBlock(block.id, ex.id, newId)
                            : undefined
                        }
                      />
                    ))}
                  </SortableContext>
                </DndContext>
              </>
            )}

            {/* + Aggiungi esercizio al blocco */}
            <Button
              variant="ghost"
              size="sm"
              className={`w-full mt-1 h-7 text-xs gap-1 ${config.color} hover:opacity-80`}
              onClick={() => onAddExerciseToBlock(block.id)}
            >
              <Plus className="h-3.5 w-3.5" />
              Aggiungi al {BLOCK_TYPE_LABELS[block.tipo_blocco]}
            </Button>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// FACTORY — Crea un nuovo BlockCardData con defaults intelligenti
// ════════════════════════════════════════════════════════════

let _blockIdCounter = -1;

export function createBlockCardData(tipo: BlockType, ordine: number): BlockCardData {
  const config = BLOCK_CONFIG[tipo];
  return {
    id: _blockIdCounter--,  // ID negativo = nuovo blocco (non ancora persistito)
    tipo_blocco: tipo,
    ordine,
    nome: null,
    giri: config.defaultGiri,
    durata_lavoro_sec: config.defaultLavoroSec,
    durata_riposo_sec: config.defaultRiposoSec,
    durata_blocco_sec: config.defaultBloccoDurSec,
    note: null,
    esercizi: [],
  };
}

/** Converte SessionBlock (server) → BlockCardData (client mutable) */
export function serverBlockToCardData(block: import("@/types/api").SessionBlock): BlockCardData {
  return {
    id: block.id,
    tipo_blocco: block.tipo_blocco,
    ordine: block.ordine,
    nome: block.nome,
    giri: block.giri,
    durata_lavoro_sec: block.durata_lavoro_sec,
    durata_riposo_sec: block.durata_riposo_sec,
    durata_blocco_sec: block.durata_blocco_sec,
    note: block.note,
    esercizi: block.esercizi,
  };
}
