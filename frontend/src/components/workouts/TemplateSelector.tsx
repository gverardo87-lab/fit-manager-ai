// src/components/workouts/TemplateSelector.tsx
"use client";

/**
 * Modale per scegliere un template di partenza (beginner/intermedio/avanzato)
 * o creare una scheda vuota. Dopo la selezione, crea la scheda via API
 * e naviga al builder /schede/[id].
 *
 * Smart matching: ogni slot viene popolato con l'esercizio piu' adatto
 * dal database, in base a pattern_movimento/categoria e difficolta.
 */

import { useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Zap, TrendingUp, Flame, FileText } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

import {
  WORKOUT_TEMPLATES,
  SECTION_CATEGORIES,
  type WorkoutTemplate,
  type TemplateExerciseSlot,
} from "@/lib/workout-templates";
import { useCreateWorkout } from "@/hooks/useWorkouts";
import { useExercises } from "@/hooks/useExercises";
import type { Exercise, WorkoutSessionInput, WorkoutExerciseInput } from "@/types/api";

// ════════════════════════════════════════════════════════════
// SMART MATCHING
// ════════════════════════════════════════════════════════════

/** Mappa livello template → difficolta esercizio */
const DIFFICULTY_MAP: Record<string, string> = {
  beginner: "beginner",
  intermedio: "intermediate",
  avanzato: "advanced",
};

/**
 * Trova l'esercizio migliore per uno slot template.
 *
 * Logica:
 * - avviamento → cerca per categoria "avviamento"
 * - stretching → cerca per categoria "stretching" o "mobilita"
 * - principale → cerca per pattern_movimento
 * - Score: +10 se difficolta allineata, +3 se compound, +1 se bodyweight
 * - Evita duplicati (usedIds)
 */
function findBestExercise(
  exercises: Exercise[],
  slot: TemplateExerciseSlot,
  templateLevel: string,
  usedIds: Set<number>,
): Exercise | undefined {
  const preferred = DIFFICULTY_MAP[templateLevel] ?? "intermediate";

  // Determina i candidati in base alla sezione
  let candidates: Exercise[];
  if (slot.sezione === "avviamento") {
    candidates = exercises.filter(
      (e) => SECTION_CATEGORIES.avviamento.includes(e.categoria) && !usedIds.has(e.id),
    );
  } else if (slot.sezione === "stretching") {
    candidates = exercises.filter(
      (e) => SECTION_CATEGORIES.stretching.includes(e.categoria) && !usedIds.has(e.id),
    );
  } else {
    // principale: match per pattern_movimento
    candidates = exercises.filter(
      (e) => e.pattern_movimento === slot.pattern_hint && !usedIds.has(e.id),
    );
  }

  // Fallback: allarga la ricerca (includi anche gia' usati)
  if (candidates.length === 0) {
    if (slot.sezione === "avviamento") {
      candidates = exercises.filter((e) => SECTION_CATEGORIES.avviamento.includes(e.categoria));
    } else if (slot.sezione === "stretching") {
      candidates = exercises.filter((e) => SECTION_CATEGORIES.stretching.includes(e.categoria));
    } else {
      candidates = exercises.filter((e) => e.pattern_movimento === slot.pattern_hint);
    }
  }

  // Ultimo fallback: qualsiasi esercizio
  if (candidates.length === 0) {
    return exercises.find((e) => !usedIds.has(e.id)) ?? exercises[0];
  }

  // Score e ordinamento
  candidates.sort((a, b) => {
    let scoreA = 0;
    let scoreB = 0;
    if (a.difficolta === preferred) scoreA += 10;
    if (b.difficolta === preferred) scoreB += 10;
    if (a.categoria === "compound") scoreA += 3;
    if (b.categoria === "compound") scoreB += 3;
    if (a.categoria === "bodyweight") scoreA += 1;
    if (b.categoria === "bodyweight") scoreB += 1;
    return scoreB - scoreA;
  });

  return candidates[0];
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

const TEMPLATE_ICONS: Record<string, React.ReactNode> = {
  beginner: <Zap className="h-6 w-6 text-emerald-500" />,
  intermedio: <TrendingUp className="h-6 w-6 text-amber-500" />,
  avanzato: <Flame className="h-6 w-6 text-red-500" />,
};

const TEMPLATE_GRADIENTS: Record<string, string> = {
  beginner: "from-emerald-50 to-emerald-100 dark:from-emerald-950/30 dark:to-emerald-900/20 border-emerald-200 dark:border-emerald-800",
  intermedio: "from-amber-50 to-amber-100 dark:from-amber-950/30 dark:to-amber-900/20 border-amber-200 dark:border-amber-800",
  avanzato: "from-red-50 to-red-100 dark:from-red-950/30 dark:to-red-900/20 border-red-200 dark:border-red-800",
};

interface TemplateSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId?: number;
}

export function TemplateSelector({ open, onOpenChange, clientId }: TemplateSelectorProps) {
  const router = useRouter();
  const createWorkout = useCreateWorkout();
  const { data: exerciseData } = useExercises();
  const exercises = useMemo(() => exerciseData?.items ?? [], [exerciseData]);

  const handleSelectTemplate = useCallback(
    (template: WorkoutTemplate) => {
      if (exercises.length === 0) return;

      const sessioni: WorkoutSessionInput[] = template.sessioni.map((sess) => {
        const usedIds = new Set<number>();

        return {
          nome_sessione: sess.nome_sessione,
          focus_muscolare: sess.focus_muscolare,
          durata_minuti: sess.durata_minuti,
          esercizi: sess.slots.map((slot, slotIdx): WorkoutExerciseInput => {
            const match = findBestExercise(exercises, slot, template.livello, usedIds);
            if (match) usedIds.add(match.id);

            return {
              id_esercizio: match?.id ?? exercises[0].id,
              ordine: slotIdx + 1,
              serie: slot.serie,
              ripetizioni: slot.ripetizioni,
              tempo_riposo_sec: slot.tempo_riposo_sec,
              note: slot.label,
            };
          }),
        };
      });

      createWorkout.mutate(
        {
          nome: template.nome,
          obiettivo: template.obiettivo_default,
          livello: template.livello,
          sessioni_per_settimana: template.sessioni_per_settimana,
          durata_settimane: template.durata_settimane,
          id_cliente: clientId ?? null,
          sessioni,
        },
        {
          onSuccess: (plan) => {
            onOpenChange(false);
            router.push(`/schede/${plan.id}`);
          },
        },
      );
    },
    [createWorkout, clientId, onOpenChange, router, exercises],
  );

  const handleBlankSheet = useCallback(() => {
    const firstExercise = exercises[0];
    createWorkout.mutate(
      {
        nome: "Nuova Scheda",
        obiettivo: "generale",
        livello: "intermedio",
        sessioni_per_settimana: 3,
        durata_settimane: 4,
        id_cliente: clientId ?? null,
        sessioni: [
          {
            nome_sessione: "Sessione 1",
            durata_minuti: 60,
            esercizi: [
              {
                id_esercizio: firstExercise?.id ?? 1,
                ordine: 1,
                serie: 3,
                ripetizioni: "8-12",
                tempo_riposo_sec: 90,
              },
            ],
          },
        ],
      },
      {
        onSuccess: (plan) => {
          onOpenChange(false);
          router.push(`/schede/${plan.id}`);
        },
      },
    );
  }, [createWorkout, clientId, onOpenChange, router, exercises]);

  const isLoading = !exerciseData || exercises.length === 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Nuova Scheda Allenamento</DialogTitle>
          <DialogDescription>
            Scegli un template di partenza o crea una scheda vuota da personalizzare.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mt-4">
          {WORKOUT_TEMPLATES.map((template) => (
            <button
              key={template.id}
              onClick={() => handleSelectTemplate(template)}
              disabled={createWorkout.isPending || isLoading}
              className={`group rounded-xl border bg-gradient-to-br ${TEMPLATE_GRADIENTS[template.livello] ?? ""} p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50`}
            >
              <div className="flex items-center gap-2">
                {TEMPLATE_ICONS[template.livello]}
                <h3 className="font-semibold text-sm">{template.nome}</h3>
              </div>
              <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                {template.descrizione}
              </p>
              <div className="mt-3 flex flex-wrap gap-1">
                <Badge variant="outline" className="text-[10px]">
                  {template.sessioni.length} sessioni
                </Badge>
                <Badge variant="outline" className="text-[10px]">
                  {template.sessioni_per_settimana}x/sett
                </Badge>
                <Badge variant="outline" className="text-[10px]">
                  {template.durata_settimane} sett
                </Badge>
              </div>
            </button>
          ))}
        </div>

        {/* Scheda vuota */}
        <button
          onClick={handleBlankSheet}
          disabled={createWorkout.isPending || isLoading}
          className="mt-2 flex items-center gap-3 rounded-xl border border-dashed p-4 text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
        >
          <FileText className="h-6 w-6 text-muted-foreground" />
          <div>
            <h3 className="font-semibold text-sm">Scheda Vuota</h3>
            <p className="text-xs text-muted-foreground">
              Parti da zero e costruisci la tua scheda personalizzata.
            </p>
          </div>
        </button>
      </DialogContent>
    </Dialog>
  );
}
