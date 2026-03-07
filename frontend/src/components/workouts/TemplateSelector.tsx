// src/components/workouts/TemplateSelector.tsx
"use client";

/**
 * Modale per scegliere un template di partenza (beginner/intermedio/avanzato)
 * o creare una scheda vuota. Dopo la selezione, crea la scheda via API
 * e naviga al builder /schede/[id].
 *
 * Matching base: ogni slot viene popolato con l'esercizio piu' adatto
 * dal database, in base a pattern_movimento/categoria e difficolta.
 */

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, TrendingUp, Flame, FileText, User, Brain, Sparkles, Layers } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  WORKOUT_TEMPLATES,
  SECTION_CATEGORIES,
  type WorkoutTemplate,
  type TemplateExerciseSlot,
} from "@/lib/workout-templates";
import { storeSmartPlanPackage } from "@/lib/smart-plan-package-cache";
import { useCreateWorkout } from "@/hooks/useWorkouts";
import { useExercises } from "@/hooks/useExercises";
import { useClients } from "@/hooks/useClients";
import { useGeneratePlanPackage } from "@/hooks/useTrainingScience";
import type {
  Exercise,
  TSBuilderLevelChoice,
  TSBuilderObjective,
  WorkoutSessionInput,
  WorkoutExerciseInput,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// MATCHING BASE
// ════════════════════════════════════════════════════════════

/** Mappa livello template → difficolta esercizio */
const DIFFICULTY_MAP: Record<string, string> = {
  beginner: "beginner",
  intermedio: "intermediate",
  avanzato: "advanced",
};

/** Conta intersezione tra due array di stringhe */
function muscleOverlap(a: string[], b: string[]): number {
  return a.filter((m) => b.includes(m)).length;
}

/**
 * Trova l'esercizio migliore per uno slot template.
 *
 * Scoring base:
 * - +10  difficolta allineata al livello template
 * - +8   muscoli_target match (stretching mirato ai muscoli lavorati)
 * - +3   compound (priorita multi-articolari)
 * - +1   bodyweight (accessibilita)
 * - -3   stessa attrezzatura dell'esercizio precedente (varieta)
 */
function findBestExercise(
  exercises: Exercise[],
  slot: TemplateExerciseSlot,
  templateLevel: string,
  usedIds: Set<number>,
  lastEquipment?: string,
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

  // Score multi-dimensionale
  const targetMuscles = slot.muscoli_target ?? [];

  candidates.sort((a, b) => {
    let scoreA = 0;
    let scoreB = 0;

    // Difficolta allineata (+10)
    if (a.difficolta === preferred) scoreA += 10;
    if (b.difficolta === preferred) scoreB += 10;

    // Muscoli target match (+8 per overlap) — cruciale per stretching mirato
    if (targetMuscles.length > 0) {
      scoreA += muscleOverlap(a.muscoli_primari, targetMuscles) * 8;
      scoreB += muscleOverlap(b.muscoli_primari, targetMuscles) * 8;
    }

    // Compound bonus (+3) — priorita movimenti multi-articolari
    if (a.categoria === "compound") scoreA += 3;
    if (b.categoria === "compound") scoreB += 3;

    // Bodyweight bonus (+1) — accessibilita
    if (a.categoria === "bodyweight") scoreA += 1;
    if (b.categoria === "bodyweight") scoreB += 1;

    // Varieta attrezzatura (-3 se uguale all'ultimo) — solo per principale
    if (lastEquipment && slot.sezione === "principale") {
      if (a.attrezzatura === lastEquipment) scoreA -= 3;
      if (b.attrezzatura === lastEquipment) scoreB -= 3;
    }

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

export function TemplateSelector(props: TemplateSelectorProps) {
  const { open, clientId } = props;
  if (!open) return null;

  const dialogKey = `template-selector-${clientId ?? "none"}`;
  return <TemplateSelectorDialog key={dialogKey} {...props} />;
}

function TemplateSelectorDialog({ open, onOpenChange, clientId }: TemplateSelectorProps) {
  const router = useRouter();
  const createWorkout = useCreateWorkout();
  const generatePlanPackage = useGeneratePlanPackage();
  const { data: exerciseData } = useExercises();
  const exercises = useMemo(() => exerciseData?.items ?? [], [exerciseData]);
  const { data: clientsData } = useClients();
  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // State locale per selezione cliente — pre-compilato se prop esiste
  const [selectedClientId, setSelectedClientId] = useState<number | null>(clientId ?? null);

  // State configurazione Smart
  const [smartSessions, setSmartSessions] = useState<number>(4);
  const [smartObiettivo, setSmartObiettivo] = useState<TSBuilderObjective>("generale");
  const [smartLivello, setSmartLivello] = useState<TSBuilderLevelChoice>("auto");

  // Smart programming — profile client per scoring potenziato

  const handleSelectTemplate = useCallback(
    (template: WorkoutTemplate) => {
      if (exercises.length === 0) return;

      const sessioni: WorkoutSessionInput[] = template.sessioni.map((sess) => {
        const usedIds = new Set<number>();
        let lastEquipment: string | undefined;

        return {
          nome_sessione: sess.nome_sessione,
          focus_muscolare: sess.focus_muscolare,
          durata_minuti: sess.durata_minuti,
          esercizi: sess.slots.map((slot, slotIdx): WorkoutExerciseInput => {
            const match = findBestExercise(
              exercises, slot, template.livello, usedIds, lastEquipment,
            );
            if (match) {
              usedIds.add(match.id);
              if (slot.sezione === "principale") lastEquipment = match.attrezzatura;
            }

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
          id_cliente: selectedClientId,
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
    [createWorkout, selectedClientId, onOpenChange, router, exercises],
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
        id_cliente: selectedClientId,
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
  }, [createWorkout, selectedClientId, onOpenChange, router, exercises]);

  /** Scheda vuota con 1 blocco circuit pre-impostato in Principale */
  const handleBlankSheetHybrid = useCallback(() => {
    createWorkout.mutate(
      {
        nome: "Nuova Scheda",
        obiettivo: "generale",
        livello: "intermedio",
        sessioni_per_settimana: 3,
        durata_settimane: 4,
        id_cliente: selectedClientId,
        sessioni: [
          {
            nome_sessione: "Sessione 1",
            durata_minuti: 60,
            esercizi: [],
            blocchi: [
              {
                tipo_blocco: "circuit",
                ordine: 1,
                nome: null,
                giri: 3,
                durata_lavoro_sec: null,
                durata_riposo_sec: 15,
                durata_blocco_sec: null,
                note: null,
                esercizi: [],
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
  }, [createWorkout, selectedClientId, onOpenChange, router]);

  // ── Handler: Scheda Smart (generazione automatica 14 dimensioni) ──
  const handleSmartTemplate = useCallback(() => {
    generatePlanPackage.mutate(
      {
        client_id: selectedClientId,
        preset: {
          frequenza: smartSessions,
          obiettivo_builder: smartObiettivo,
          livello_choice: smartLivello,
        },
      },
      {
        onSuccess: (planPackage) => {
          createWorkout.mutate(
            planPackage.workout_projection.draft,
            {
              onSuccess: (plan) => {
                storeSmartPlanPackage(plan.id, planPackage);
                onOpenChange(false);
                router.push(`/schede/${plan.id}`);
              },
            },
          );
        },
      },
    );
  }, [
    createWorkout,
    generatePlanPackage,
    selectedClientId,
    smartSessions,
    smartObiettivo,
    smartLivello,
    onOpenChange,
    router,
  ]);

  const isTemplateLoading = !exerciseData || exercises.length === 0;
  const isSmartPending = generatePlanPackage.isPending || createWorkout.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Nuova Scheda Allenamento</DialogTitle>
          <DialogDescription>
            Scegli un template di partenza o crea una scheda vuota da personalizzare.
          </DialogDescription>
        </DialogHeader>

        {/* Selezione cliente */}
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-muted-foreground shrink-0" />
          <Select
            value={selectedClientId ? String(selectedClientId) : "__none__"}
            onValueChange={(v) => setSelectedClientId(v === "__none__" ? null : Number(v))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleziona cliente (opzionale)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">Nessun cliente (scheda generica)</SelectItem>
              {clients.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nome} {c.cognome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 mt-4">
          {/* Card Scheda Smart — configurazione inline */}
          <div className="relative rounded-xl border bg-gradient-to-br from-teal-50 to-cyan-100 dark:from-teal-950/30 dark:to-cyan-900/20 border-teal-200 dark:border-teal-800 p-4 sm:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <Brain className="h-6 w-6 text-teal-600 dark:text-teal-400" />
              <h3 className="font-semibold text-sm">Scheda Smart</h3>
              <Badge variant="secondary" className="text-[10px] bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300">
                Backend-first
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Genera una scheda dal profilo cliente reale con piano scientifico canonico e ranking esercizi deterministico lato backend.
            </p>

            {/* Configurazione Smart */}
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1">
                <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Sessioni/Sett</Label>
                <Select value={String(smartSessions)} onValueChange={(v) => setSmartSessions(Number(v))}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[2, 3, 4, 5, 6].map(n => (
                      <SelectItem key={n} value={String(n)}>{n}x</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Obiettivo</Label>
                <Select value={smartObiettivo} onValueChange={(v) => setSmartObiettivo(v as TSBuilderObjective)}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="generale">Generale</SelectItem>
                    <SelectItem value="forza">Forza</SelectItem>
                    <SelectItem value="ipertrofia">Ipertrofia</SelectItem>
                    <SelectItem value="resistenza">Resistenza</SelectItem>
                    <SelectItem value="dimagrimento">Dimagrimento</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Livello</Label>
                <Select value={smartLivello} onValueChange={(v) => setSmartLivello(v as TSBuilderLevelChoice)}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto (backend)</SelectItem>
                    <SelectItem value="beginner">Principiante</SelectItem>
                    <SelectItem value="intermedio">Intermedio</SelectItem>
                    <SelectItem value="avanzato">Avanzato</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Badge profilo + Genera */}
            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {selectedClientId && (
                  <>
                    <Badge variant="outline" className="text-[10px] border-teal-300 dark:border-teal-700">
                      Cliente collegato
                    </Badge>
                    <Badge variant="outline" className="text-[10px] border-teal-300 dark:border-teal-700">
                      Ranking deterministico
                    </Badge>
                  </>
                )}
              </div>
              <Button
                size="sm"
                onClick={handleSmartTemplate}
                disabled={isSmartPending}
                className="bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
              >
                <Sparkles className="h-3.5 w-3.5" />
                {generatePlanPackage.isPending ? "Genero..." : "Genera"}
              </Button>
            </div>
          </div>

          {/* Template statici */}
          {WORKOUT_TEMPLATES.map((template) => (
            <button
              key={template.id}
              onClick={() => handleSelectTemplate(template)}
              disabled={createWorkout.isPending || isTemplateLoading}
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

        {/* Scheda vuota — 2 opzioni: Standard o Con blocchi */}
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            onClick={handleBlankSheet}
            disabled={createWorkout.isPending || isTemplateLoading}
            className="flex items-start gap-3 rounded-xl border border-dashed p-4 text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
          >
            <FileText className="h-5 w-5 mt-0.5 text-muted-foreground shrink-0" />
            <div>
              <h3 className="font-semibold text-sm">Standard</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Esercizi per sezione: avviamento, principale, stretching.
              </p>
            </div>
          </button>

          <button
            onClick={handleBlankSheetHybrid}
            disabled={createWorkout.isPending || isTemplateLoading}
            className="flex items-start gap-3 rounded-xl border border-dashed p-4 text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
          >
            <Layers className="h-5 w-5 mt-0.5 text-muted-foreground shrink-0" />
            <div>
              <h3 className="font-semibold text-sm">Con blocchi</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Parte con un circuito in Principale, pronto da riempire.
              </p>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

