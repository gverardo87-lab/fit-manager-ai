// src/components/workouts/SmartAnalysisPanel.tsx
"use client";

/**
 * Pannello di analisi scientifica per il builder schede allenamento.
 *
 * V2: consuma il Training Science Engine backend per analisi EMG-based.
 * Mantiene biomeccanica e safety dal frontend (dati non disponibili nel backend).
 *
 * Sezioni:
 * 1. Copertura Muscolare — EMG-based volume ipertrofico vs MEV/MAV/MRV (backend)
 * 2. Rapporti Biomeccanici — 5 ratio con fonti scientifiche (backend)
 * 3. Varieta Biomeccanica — piani, catene, contrazioni (frontend)
 * 4. Warning Scientifici — frequenza, recupero, volume (backend)
 * 5. Compatibilita Clinica — safety map anamnesi (frontend)
 *
 * Il bridge function converte esercizi builder -> TSTemplatePiano per l'endpoint
 * POST /training-science/analyze che ritorna analisi 4D con score 0-100.
 */

import { useMemo, useState, useEffect, useRef, useEffectEvent } from "react";
import { BarChart3, ChevronDown, AlertTriangle, BookOpen, Scale } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import {
  analyzeBiomechanics,
  computeSafetyBreakdown,
  type BiomechanicalVariety,
  type SafetyBreakdown,
} from "@/lib/smart-programming";
import { getBackendVolumeCounts, mapBackendVolumeStatus, VALID_PATTERNS } from "@/lib/training-science-display";
import { useAnalyzePlan } from "@/hooks/useTrainingScience";
import { ProtocolSection, FeasibilitySection, ConstraintSection } from "./SmartProtocolSection";
import type {
  Exercise,
  ExerciseSafetyEntry,
  TSPlanPackage,
  TSTemplatePiano,
  TSObjective,
  TSLevel,
  TSPattern,
  TSAnalisiPiano,
  TSVolumeEffettivo,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface SmartAnalysisPanelProps {
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>;
  exerciseMap: Map<number, Exercise>;
  livello: string;
  obiettivo: string;
  sessioniPerSettimana: number;
  safetyMap: Record<number, ExerciseSafetyEntry> | null;
  smartPlanPackage?: TSPlanPackage | null;
  safetyConditionCount?: number;
  impactedConditionCount?: number;
  onBackendAnalysisChange?: (analysis: TSAnalisiPiano | null) => void;
}

// ════════════════════════════════════════════════════════════
// BRIDGE — Workout exercises → TSTemplatePiano
// ════════════════════════════════════════════════════════════

const LIVELLO_MAP: Record<string, TSLevel> = {
  beginner: "principiante",
  principiante: "principiante",
  intermedio: "intermedio",
  avanzato: "avanzato",
};

const VALID_OBIETTIVI = new Set<TSObjective>([
  "forza", "ipertrofia", "resistenza", "dimagrimento", "tonificazione",
]);

function buildTemplatePiano(
  sessions: SmartAnalysisPanelProps["sessions"],
  exerciseMap: Map<number, Exercise>,
  livello: string,
  obiettivo: string,
  sessioniPerSettimana: number,
): TSTemplatePiano | null {
  const mappedLivello = LIVELLO_MAP[livello] ?? "intermedio";
  const mappedObiettivo: TSObjective = VALID_OBIETTIVI.has(obiettivo as TSObjective)
    ? (obiettivo as TSObjective)
    : "ipertrofia";

  const sessioni = sessions.map((s) => {
    const slots = s.esercizi
      .map((e) => {
        const exercise = exerciseMap.get(e.id_esercizio);
        if (!exercise) return null;
        const pattern = exercise.pattern_movimento as TSPattern;
        if (!VALID_PATTERNS.has(pattern)) return null;
        return {
          pattern,
          priorita: 2 as const,
          serie: e.serie,
          rep_min: 8,
          rep_max: 12,
          riposo_sec: 90,
          muscolo_target: null,
          note: "",
          carico_kg: null,
        };
      })
      .filter((s): s is NonNullable<typeof s> => s !== null);

    return {
      nome: s.nome_sessione,
      ruolo: "full_body" as const,
      focus: "",
      slots,
    };
  });

  const hasSlots = sessioni.some((s) => s.slots.length > 0);
  if (!hasSlots) return null;

  return {
    frequenza: Math.max(2, Math.min(6, sessioniPerSettimana)),
    obiettivo: mappedObiettivo,
    livello: mappedLivello,
    tipo_split: "full_body",
    sessioni,
    note_generazione: [],
  };
}

function buildTemplatePianoFromCanonical(planPackage: TSPlanPackage): TSTemplatePiano {
  return {
    frequenza: planPackage.canonical_plan.frequenza,
    obiettivo: planPackage.canonical_plan.obiettivo,
    livello: planPackage.canonical_plan.livello,
    tipo_split: planPackage.canonical_plan.tipo_split,
    sessioni: planPackage.canonical_plan.sessioni.map((session) => ({
      nome: session.nome,
      ruolo: session.ruolo,
      focus: session.focus,
      slots: session.slots.map((slot) => ({
        pattern: slot.pattern,
        priorita: slot.priorita,
        serie: slot.serie,
        rep_min: slot.rep_min,
        rep_max: slot.rep_max,
        riposo_sec: slot.riposo_sec,
        muscolo_target: slot.muscolo_target,
        note: slot.note,
        carico_kg: null,
      })),
    })),
    note_generazione: planPackage.canonical_plan.note_generazione,
  };
}

// ════════════════════════════════════════════════════════════
// VOLUME STATUS — Colori e label per stato backend
// ════════════════════════════════════════════════════════════

const STATUS_COLORS = {
  deficit: {
    bg: "bg-red-100 dark:bg-red-950/40",
    text: "text-red-700 dark:text-red-400",
    bar: "bg-red-500",
  },
  suboptimal: {
    bg: "bg-blue-100 dark:bg-blue-950/40",
    text: "text-blue-700 dark:text-blue-400",
    bar: "bg-blue-500",
  },
  optimal: {
    bg: "bg-emerald-100 dark:bg-emerald-950/40",
    text: "text-emerald-700 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  excess: {
    bg: "bg-amber-100 dark:bg-amber-950/40",
    text: "text-amber-700 dark:text-amber-400",
    bar: "bg-amber-500",
  },
} as const;

const STATUS_LABELS = {
  deficit: "Deficit",
  suboptimal: "Sub-ottimale",
  optimal: "Ottimale",
  excess: "Eccesso",
} as const;

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  deltoide_anteriore: "Delt. Ant.",
  deltoide_laterale: "Delt. Lat.",
  deltoide_posteriore: "Delt. Post.",
  bicipiti: "Bicipiti",
  tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti",
  femorali: "Femorali",
  glutei: "Glutei",
  polpacci: "Polpacci",
  core: "Core",
  trapezio: "Trapezio",
  adduttori: "Adduttori",
  avambracci: "Avambracci",
};

const PLAN_MODE_LABELS: Record<string, string> = {
  general: "General",
  performance: "Performance",
  clinical: "Clinical",
};

const ANAMNESI_STATE_LABELS: Record<string, string> = {
  missing: "Anamnesi mancante",
  legacy: "Anamnesi legacy",
  structured: "Anamnesi strutturata",
};

// Score color based on 0-100 range
function getScoreColor(score: number): string {
  if (score >= 75) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 50) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function SmartAnalysisPanel({
  sessions,
  exerciseMap,
  livello,
  obiettivo,
  sessioniPerSettimana,
  safetyMap,
  smartPlanPackage,
  safetyConditionCount = 0,
  impactedConditionCount = 0,
  onBackendAnalysisChange,
}: SmartAnalysisPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const analyzeMutation = useAnalyzePlan();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Build TSTemplatePiano from workout exercises
  const templatePiano = useMemo(
    () => smartPlanPackage
      ? buildTemplatePianoFromCanonical(smartPlanPackage)
      : buildTemplatePiano(sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana),
    [smartPlanPackage, sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana],
  );

  // Stable serialization key to detect real data changes
  const pianoKey = useMemo(() => {
    if (!templatePiano) return "";
    if (smartPlanPackage) {
      return `canonical:${smartPlanPackage.canonical_plan.plan_id}`;
    }
    return templatePiano.sessioni
      .map((s) => s.slots.map((sl) => `${sl.pattern}:${sl.serie}`).join(","))
      .join("|") + `|${templatePiano.livello}|${templatePiano.obiettivo}`;
  }, [templatePiano, smartPlanPackage]);

  // Trigger backend analysis on data change (debounced 600ms)
  const triggerAnalysis = useEffectEvent((piano: TSTemplatePiano) => {
    analyzeMutation.mutate(piano);
  });

  useEffect(() => {
    if (!templatePiano || !pianoKey) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      triggerAnalysis(templatePiano);
    }, 600);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [pianoKey]); // eslint-disable-line react-hooks/exhaustive-deps

  // Frontend-only analysis (biomechanics variety + safety)
  const biomechanics = useMemo<BiomechanicalVariety>(
    () => analyzeBiomechanics(sessions, exerciseMap),
    [sessions, exerciseMap],
  );

  const safetyBreakdown = useMemo<SafetyBreakdown>(
    () => computeSafetyBreakdown(sessions, safetyMap),
    [sessions, safetyMap],
  );

  const backendAnalysis: TSAnalisiPiano | null = analyzeMutation.data ?? null;
  const generationWarnings = useMemo(() => {
    if (!smartPlanPackage) return [];
    return Array.from(
      new Set([
        ...smartPlanPackage.scientific_profile.profile_warnings,
        ...smartPlanPackage.warnings,
      ]),
    );
  }, [smartPlanPackage]);

  useEffect(() => {
    onBackendAnalysisChange?.(backendAnalysis);
  }, [backendAnalysis, onBackendAnalysisChange]);

  if (!templatePiano) return null;

  // KPI from backend analysis
  const volumeData = backendAnalysis?.volume;
  const volumeCounts = getBackendVolumeCounts(backendAnalysis);
  const optimalCount = volumeCounts.optimal;
  const needsAttentionCount = volumeCounts.attention;
  const attentionColors = volumeCounts.deficit > 0 ? STATUS_COLORS.deficit : STATUS_COLORS.excess;
  const hasSafetyRisk =
    safetyBreakdown.avoid > 0 || safetyBreakdown.modify > 0 || safetyBreakdown.caution > 0;
  const safetyKpiParts = [
    safetyBreakdown.avoid > 0 ? (
      <span key="avoid" className="text-red-600 dark:text-red-400">{safetyBreakdown.avoid}A</span>
    ) : null,
    safetyBreakdown.modify > 0 ? (
      <span key="modify" className="text-blue-600 dark:text-blue-400">{safetyBreakdown.modify}M</span>
    ) : null,
    safetyBreakdown.caution > 0 ? (
      <span key="caution" className="text-amber-600 dark:text-amber-400">{safetyBreakdown.caution}C</span>
    ) : null,
  ].filter(Boolean);

  const borderColor = backendAnalysis
    ? backendAnalysis.score >= 75
      ? "border-l-emerald-400"
      : backendAnalysis.score >= 50
        ? "border-l-teal-400"
        : "border-l-amber-400"
    : "border-l-teal-400";

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <Card className={`border-l-4 ${borderColor} transition-all duration-200`}>
        <CardContent className="p-4 space-y-3">
          {/* Header */}
          <CollapsibleTrigger asChild>
            <button className="flex items-center justify-between w-full text-left group">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
                <span className="text-sm font-semibold">Analisi Scientifica</span>
                {smartPlanPackage && (
                  <Badge variant="outline" className="h-5 text-[9px] font-normal">
                    Piano canonico backend
                  </Badge>
                )}
                {analyzeMutation.isPending && (
                  <span className="text-[10px] text-muted-foreground animate-pulse">analisi...</span>
                )}
              </div>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${expanded ? "rotate-180" : ""}`} />
            </button>
          </CollapsibleTrigger>

          {/* KPI mini-row */}
          <div className="grid grid-cols-4 gap-2">
            {backendAnalysis ? (
              <div className="rounded-lg bg-muted/50 px-2 py-2 text-center">
                <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${getScoreColor(backendAnalysis.score)}`}>
                  {Math.round(backendAnalysis.score)}
                </div>
                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Score</div>
              </div>
            ) : (
              <div className="rounded-lg bg-muted/50 px-2 py-2 text-center">
                <div className="text-lg font-extrabold tracking-tighter tabular-nums text-muted-foreground">—</div>
                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Score</div>
              </div>
            )}
            <div className={`rounded-lg ${STATUS_COLORS.optimal.bg} px-2 py-2 text-center`}>
              <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${STATUS_COLORS.optimal.text}`}>{optimalCount}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Ottimali</div>
            </div>
            <div className={`rounded-lg ${needsAttentionCount > 0 ? attentionColors.bg : "bg-muted/50"} px-2 py-2 text-center`}>
              <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${needsAttentionCount > 0 ? attentionColors.text : "text-muted-foreground"}`}>{needsAttentionCount}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Da correggere</div>
            </div>
            <div className="rounded-lg bg-muted/50 px-2 py-2 text-center">
              {safetyBreakdown.hasConditions ? (
                <>
                  <div className="text-sm font-extrabold tracking-tighter tabular-nums leading-6">
                    {hasSafetyRisk ? (
                      safetyKpiParts.map((part, index) => (
                        <span key={index}>
                          {index > 0 && <span className="mx-0.5 text-muted-foreground">/</span>}
                          {part}
                        </span>
                      ))
                    ) : (
                      <span className="text-emerald-600 dark:text-emerald-400">OK</span>
                    )}
                  </div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Safety</div>
                </>
              ) : (
                <>
                  <div className="text-lg font-extrabold tracking-tighter tabular-nums text-muted-foreground">—</div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Safety</div>
                </>
              )}
            </div>
          </div>

          {/* Expanded content */}
          <CollapsibleContent className="space-y-4">
            <Separator />

            {smartPlanPackage && (
              <section>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Contesto Generazione
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline" className="text-[10px] font-normal">
                    {PLAN_MODE_LABELS[smartPlanPackage.scientific_profile.mode] ?? smartPlanPackage.scientific_profile.mode}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] font-normal">
                    Livello {smartPlanPackage.scientific_profile.livello_scientifico}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] font-normal">
                    {ANAMNESI_STATE_LABELS[smartPlanPackage.scientific_profile.anamnesi_state] ?? smartPlanPackage.scientific_profile.anamnesi_state}
                  </Badge>
                  {smartPlanPackage.scientific_profile.safety_condition_count > 0 && (
                    <Badge variant="outline" className="text-[10px] font-normal">
                      {smartPlanPackage.scientific_profile.safety_condition_count} condizioni safety
                    </Badge>
                  )}
                </div>
                {generationWarnings.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    {generationWarnings.map((warning, index) => (
                      <div key={`${warning}-${index}`} className="flex items-start gap-2 text-[11px]">
                        <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5 text-amber-500" />
                        <span className="text-muted-foreground">{warning}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* SMART Protocol + Feasibility + Constraints (backend) */}
            {smartPlanPackage && (
              <>
                <ProtocolSection protocol={smartPlanPackage.protocol} />
                <FeasibilitySection summary={smartPlanPackage.feasibility_summary} />
                <ConstraintSection evaluation={smartPlanPackage.constraint_evaluation} />
              </>
            )}

            {/* 1. Copertura Muscolare — EMG-based (backend) */}
            {volumeData && (
              <section>
                <div className="flex items-center gap-1.5 mb-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Volume Muscolare (serie ipertrofiche/sett)
                  </div>
                  <Badge variant="outline" className="text-[8px] px-1 py-0 h-3.5 font-normal text-muted-foreground">
                    EMG
                  </Badge>
                </div>
                <div className="space-y-1.5">
                  {volumeData.per_muscolo
                    .filter((m) => m.serie_effettive > 0 || mapBackendVolumeStatus(m.stato) === "deficit")
                    .map((m) => (
                      <VolumeRow key={m.muscolo} data={m} />
                    ))}
                </div>
                <div className="mt-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                  <span>Totale: <strong className="text-foreground">{volumeData.volume_totale_settimana}</strong> serie/sett</span>
                  {volumeData.muscoli_sotto_mev.length > 0 && (
                    <span className="text-red-600 dark:text-red-400">
                      {volumeData.muscoli_sotto_mev.length} sotto MEV
                    </span>
                  )}
                  {volumeData.muscoli_sopra_mrv.length > 0 && (
                    <span className="text-amber-600 dark:text-amber-400">
                      {volumeData.muscoli_sopra_mrv.length} sopra MRV
                    </span>
                  )}
                </div>
              </section>
            )}

            {/* 2. Rapporti Biomeccanici (backend) */}
            {backendAnalysis?.balance && (
              <section>
                <div className="flex items-center gap-1.5 mb-2">
                  <Scale className="h-3 w-3 text-muted-foreground" />
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Rapporti Biomeccanici
                  </div>
                </div>
                <div className="space-y-1.5">
                  {Object.entries(backendAnalysis.balance.rapporti).map(([name, value]) => {
                    const target = backendAnalysis.balance.target[name] ?? 1;
                    const isBalanced = !backendAnalysis.balance.squilibri.some(
                      (s) => s.startsWith(name),
                    );
                    return (
                      <BalanceRow
                        key={name}
                        name={name}
                        value={value}
                        target={target}
                        isBalanced={isBalanced}
                      />
                    );
                  })}
                </div>
              </section>
            )}

            {/* 3. Varieta Biomeccanica (frontend) */}
            <section>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Varieta Biomeccanica
              </div>
              <div className="grid grid-cols-3 gap-2">
                <BiomechanicsChip label="Piani" data={biomechanics.planes} />
                <BiomechanicsChip label="Catene" data={biomechanics.chains} />
                <BiomechanicsChip label="Contrazioni" data={biomechanics.contractions} />
              </div>
            </section>

            {/* 4. Warning Scientifici (backend) */}
            {backendAnalysis && backendAnalysis.warnings.length > 0 && (
              <section>
                <div className="flex items-center gap-1.5 mb-2">
                  <BookOpen className="h-3 w-3 text-muted-foreground" />
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Note Scientifiche ({backendAnalysis.warnings.length})
                  </div>
                </div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {backendAnalysis.warnings.map((warning, i) => (
                    <div key={i} className="flex items-start gap-2 text-[11px]">
                      <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5 text-amber-500" />
                      <span className="text-muted-foreground">{warning}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 5. Compatibilita Clinica (frontend) */}
            {safetyBreakdown.hasConditions && (safetyBreakdown.avoid > 0 || safetyBreakdown.modify > 0 || safetyBreakdown.caution > 0) && (
              <section>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Compatibilita Clinica
                </div>
                {safetyConditionCount > 0 && (
                  <div className="mb-2 text-[10px] text-muted-foreground">
                    {impactedConditionCount > 0
                      ? `${impactedConditionCount} condizioni impattano la scheda corrente su ${safetyConditionCount} rilevate in anamnesi.`
                      : `${safetyConditionCount} condizioni rilevate in anamnesi, nessuna attualmente triggerata dagli esercizi selezionati.`}
                  </div>
                )}
                <div className="space-y-1.5">
                  {safetyBreakdown.avoid > 0 && (
                    <div className="flex items-center gap-2 text-xs">
                      <div className="h-2 w-2 rounded-full bg-red-500 shrink-0" />
                      <span className="font-medium text-red-700 dark:text-red-400">{safetyBreakdown.avoid} da evitare</span>
                      <span className="text-muted-foreground">— controindicati per il profilo</span>
                    </div>
                  )}
                  {safetyBreakdown.modify > 0 && (
                    <div className="flex items-center gap-2 text-xs">
                      <div className="h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                      <span className="font-medium text-blue-700 dark:text-blue-400">{safetyBreakdown.modify} da adattare</span>
                      <span className="text-muted-foreground">— richiedono modifica ROM/carico</span>
                    </div>
                  )}
                  {safetyBreakdown.caution > 0 && (
                    <div className="flex items-center gap-2 text-xs">
                      <div className="h-2 w-2 rounded-full bg-amber-500 shrink-0" />
                      <span className="font-medium text-amber-700 dark:text-amber-400">{safetyBreakdown.caution} cautela</span>
                      <span className="text-muted-foreground">— monitorare durante esecuzione</span>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Score breakdown (backend) */}
            {backendAnalysis && (
              <section>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Punteggio Composito
                </div>
                <div className="text-[10px] text-muted-foreground">
                  Volume 40pt + Bilanciamento 25pt + Frequenza 20pt + Recupero 15pt
                </div>
              </section>
            )}
          </CollapsibleContent>
        </CardContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function VolumeRow({ data }: { data: TSVolumeEffettivo }) {
  const status = mapBackendVolumeStatus(data.stato);
  const colors = STATUS_COLORS[status];
  const pct = data.target_mrv > 0
    ? Math.min(100, (data.serie_effettive / data.target_mrv) * 100)
    : 0;

  // MEV..MAV range indicator as % of MRV
  const mevPct = data.target_mrv > 0 ? (data.target_mev / data.target_mrv) * 100 : 0;
  const mavMaxPct = data.target_mrv > 0 ? (data.target_mav_max / data.target_mrv) * 100 : 0;

  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] w-24 truncate text-right text-muted-foreground">
        {MUSCLE_LABELS[data.muscolo] ?? data.muscolo}
      </span>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden relative">
        {/* MEV..MAV optimal zone (subtle background) */}
        <div
          className="absolute top-0 h-full bg-emerald-200/30 dark:bg-emerald-800/20"
          style={{ left: `${mevPct}%`, width: `${mavMaxPct - mevPct}%` }}
        />
        {/* Actual volume bar */}
        <div
          className={`h-full rounded-full transition-all duration-300 ${colors.bar} relative z-10`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[10px] font-medium tabular-nums w-8 text-right ${colors.text}`}>
        {data.serie_effettive}
      </span>
      <Badge variant="outline" className={`text-[8px] px-1 py-0 h-3.5 ${colors.text}`}>
        {STATUS_LABELS[status]}
      </Badge>
    </div>
  );
}

function BalanceRow({
  name,
  value,
  target,
  isBalanced,
}: {
  name: string;
  value: number;
  target: number;
  isBalanced: boolean;
}) {
  const color = isBalanced
    ? "text-emerald-600 dark:text-emerald-400"
    : "text-amber-600 dark:text-amber-400";

  return (
    <div className="flex items-center gap-2 text-[11px]">
      <div className={`h-2 w-2 rounded-full shrink-0 ${isBalanced ? "bg-emerald-500" : "bg-amber-500"}`} />
      <span className="flex-1 text-muted-foreground">{name}</span>
      <span className={`font-medium tabular-nums ${color}`}>{value.toFixed(2)}</span>
      <span className="text-muted-foreground/60 tabular-nums">/ {target.toFixed(2)}</span>
      <Badge variant="outline" className={`text-[8px] px-1 py-0 h-3.5 ${color}`}>
        {isBalanced ? "OK" : "Squilibrio"}
      </Badge>
    </div>
  );
}

function BiomechanicsChip({ label, data }: { label: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  const variety = entries.length;

  return (
    <div className="rounded-lg bg-muted/50 px-2 py-1.5 text-center">
      <div className="text-xs font-semibold tabular-nums">{variety}</div>
      <div className="text-[10px] text-muted-foreground">{label}</div>
      {entries.length > 0 && total > 0 && (
        <div className="text-[9px] text-muted-foreground mt-0.5 truncate" title={entries.map(([k, v]) => `${k}: ${v}`).join(", ")}>
          {entries.slice(0, 2).map(([k, v]) => `${k} ${Math.round(v / total * 100)}%`).join(", ")}
        </div>
      )}
    </div>
  );
}
