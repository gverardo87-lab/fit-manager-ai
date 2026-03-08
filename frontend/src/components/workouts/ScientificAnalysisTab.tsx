// src/components/workouts/ScientificAnalysisTab.tsx
"use client";

/**
 * Tab di analisi scientifica per il builder schede allenamento.
 *
 * Orchestratore delle 4 sezioni:
 * 1. Copertura Muscolare — body map + drill-down volume per muscolo
 * 2. Equilibrio Biomeccanico — 2A demand profile + 2B force ratios
 * 3. Profilo Clinico-Safety — condizioni x esercizi (Sprint 3)
 * 4. Riepilogo Operativo — azioni prioritizzate (Sprint 3)
 *
 * Consuma il backend Training Science Engine via POST /training-science/analyze.
 * Il bridge converte gli esercizi del builder in TSTemplatePiano.
 */

import { useMemo, useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";

import { useAnalyzePlan } from "@/hooks/useTrainingScience";
import { MuscleCoverageSection } from "./MuscleCoverageSection";
import { BiomechanicalBalance } from "./BiomechanicalBalance";
import { ClinicalSafetySection } from "./ClinicalSafetySection";
import { ActionableSummary } from "./ActionableSummary";
import { Badge } from "@/components/ui/badge";
import type {
  Exercise,
  ExerciseSafetyEntry,
  TSTemplatePiano,
  TSObjective,
  TSLevel,
  TSPattern,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface ScientificAnalysisTabProps {
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number; carico_kg?: number | null }>;
  }>;
  exerciseMap: Map<number, Exercise>;
  livello: string;
  obiettivo: string;
  sessioniPerSettimana: number;
  safetyMap: Record<number, ExerciseSafetyEntry> | null;
  /** Sesso del cliente ('M' o 'F') — scala target volume per differenze ormonali */
  clientSesso?: string | null;
  /** Data di nascita del cliente — calcola eta' per scaling volume */
  clientDataNascita?: string | null;
}

// ════════════════════════════════════════════════════════════
// BRIDGE — Workout exercises -> TSTemplatePiano
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

const VALID_PATTERNS = new Set<TSPattern>([
  "push_h", "push_v", "squat", "hinge", "pull_h", "pull_v", "core", "rotation", "carry",
  "hip_thrust", "curl", "extension_tri", "lateral_raise", "face_pull",
  "calf_raise", "leg_curl", "leg_extension", "adductor",
]);

function computeAge(dataNascita: string | null | undefined): number | null {
  if (!dataNascita) return null;
  const birth = new Date(dataNascita);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age >= 10 && age <= 100 ? age : null;
}

function buildTemplatePiano(
  sessions: ScientificAnalysisTabProps["sessions"],
  exerciseMap: Map<number, Exercise>,
  livello: string,
  obiettivo: string,
  sessioniPerSettimana: number,
  clientSesso?: string | null,
  clientDataNascita?: string | null,
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
          carico_kg: e.carico_kg ?? null,
        };
      })
      .filter((s): s is NonNullable<typeof s> => s !== null);

    return { nome: s.nome_sessione, ruolo: "full_body" as const, focus: "", slots };
  });

  if (!sessioni.some((s) => s.slots.length > 0)) return null;

  const eta = computeAge(clientDataNascita);

  return {
    frequenza: Math.max(2, Math.min(6, sessioniPerSettimana)),
    obiettivo: mappedObiettivo,
    livello: mappedLivello,
    tipo_split: "full_body",
    sessioni,
    note_generazione: [],
    sesso: clientSesso || null,
    eta,
  };
}

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export function ScientificAnalysisTab({
  sessions,
  exerciseMap,
  livello,
  obiettivo,
  sessioniPerSettimana,
  safetyMap,
  clientSesso,
  clientDataNascita,
}: ScientificAnalysisTabProps) {
  const analyzeMutation = useAnalyzePlan();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Bridge: converti esercizi builder -> TSTemplatePiano
  const templatePiano = useMemo(
    () => buildTemplatePiano(
      sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana,
      clientSesso, clientDataNascita,
    ),
    [sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana, clientSesso, clientDataNascita],
  );

  // Fingerprint per debounce: cambia solo quando cambia la composizione reale
  const fingerprint = useMemo(() => {
    if (!templatePiano) return "";
    const slotsKey = templatePiano.sessioni.map((s) =>
      s.slots.map((sl) => `${sl.pattern}:${sl.serie}:${sl.carico_kg ?? ""}`).join(","),
    ).join("|");
    return `${slotsKey}|${templatePiano.sesso ?? ""}|${templatePiano.eta ?? ""}`;
  }, [templatePiano]);

  // Analisi con debounce 1s
  useEffect(() => {
    if (!templatePiano || !fingerprint) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      analyzeMutation.mutate(templatePiano);
    }, 1000);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fingerprint]);

  const analysis = analyzeMutation.data ?? null;

  if (!templatePiano) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Aggiungi esercizi alla scheda per visualizzare l&apos;analisi scientifica.
      </div>
    );
  }

  if (analyzeMutation.isPending && !analysis) {
    return (
      <div className="flex items-center justify-center py-12 gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Analisi in corso...</span>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="space-y-4">
      {/* Score badge + load indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Analisi Scientifica
          </h3>
          {analysis.volume.has_load_data && (
            <Badge className="text-[10px] px-1.5 py-0 bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">
              Dose-Response
            </Badge>
          )}
        </div>
        <ScoreBadge score={analysis.score} />
      </div>

      {/* Sezione 1: Copertura Muscolare */}
      <MuscleCoverageSection analysis={analysis} />

      {/* Sezione 2: Equilibrio Biomeccanico */}
      <BiomechanicalBalance
        analysis={analysis}
        sessions={sessions}
        exerciseMap={exerciseMap}
      />

      {/* Sezione 3: Profilo Clinico-Safety */}
      <ClinicalSafetySection
        safetyMap={safetyMap}
        sessions={sessions}
        exerciseMap={exerciseMap}
      />

      {/* Sezione 4: Riepilogo Operativo */}
      <ActionableSummary
        analysis={analysis}
        safetyMap={safetyMap}
        sessions={sessions}
        exerciseMap={exerciseMap}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SCORE BADGE
// ════════════════════════════════════════════════════════════

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
      : score >= 50
        ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
        : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300";

  return (
    <span className={`text-xs font-bold px-2.5 py-1 rounded-full tabular-nums ${color}`}>
      {Math.round(score)}/100
    </span>
  );
}
