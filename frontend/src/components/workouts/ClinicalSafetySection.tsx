// src/components/workouts/ClinicalSafetySection.tsx
"use client";

/**
 * Sezione 3 — Profilo Clinico-Safety.
 *
 * Incrocia la safety map del cliente (condizioni mediche × esercizi)
 * con gli esercizi presenti nella scheda. Mostra:
 * - KPI: condizioni rilevate, esercizi da evitare/adattare/cautela
 * - Drill-down per condizione: lista esercizi impattati con severita'
 *
 * Dati: safetyMap (gia' fetchata dal builder), exerciseMap (in memoria).
 * Fonte: ACSM 2021 cap. popolazioni speciali.
 */

import { useMemo, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Info,
} from "lucide-react";

import type { Exercise, ExerciseSafetyEntry } from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface ClinicalSafetySectionProps {
  safetyMap: Record<number, ExerciseSafetyEntry> | null;
  sessions: Array<{
    nome_sessione: string;
    esercizi: Array<{ id_esercizio: number; serie: number }>;
  }>;
  exerciseMap: Map<number, Exercise>;
}

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

interface ConditionGroup {
  conditionId: number;
  nome: string;
  categoria: string;
  exercises: Array<{
    exerciseId: number;
    nome: string;
    pattern: string;
    sessione: string;
    severity: "avoid" | "modify" | "caution";
    nota: string | null;
  }>;
  worstSeverity: "avoid" | "modify" | "caution";
}

// ════════════════════════════════════════════════════════════
// SEVERITY CONFIG
// ════════════════════════════════════════════════════════════

const SEVERITY_ORDER: Record<string, number> = { avoid: 3, modify: 2, caution: 1 };

const SEVERITY_CONFIG = {
  avoid: {
    label: "Evitare",
    icon: ShieldAlert,
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-200 dark:border-red-900",
    badge: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  },
  modify: {
    label: "Adattare",
    icon: AlertTriangle,
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-950/30",
    border: "border-blue-200 dark:border-blue-900",
    badge: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  caution: {
    label: "Cautela",
    icon: Info,
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-200 dark:border-amber-900",
    badge: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
} as const;

const CATEGORIA_LABELS: Record<string, string> = {
  orthopedic: "Ortopedica",
  cardiovascular: "Cardiovascolare",
  metabolic: "Metabolica",
  neurological: "Neurologica",
  respiratory: "Respiratoria",
  special: "Speciale",
};

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export function ClinicalSafetySection({
  safetyMap,
  sessions,
  exerciseMap,
}: ClinicalSafetySectionProps) {
  const [expandedConditions, setExpandedConditions] = useState<Set<number>>(new Set());

  // Raccogli tutti gli exercise ID presenti nella scheda
  const exerciseIdsInPlan = useMemo(() => {
    const ids = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) ids.add(e.id_esercizio);
    }
    return ids;
  }, [sessions]);

  // Mappa esercizio -> sessione (per mostrare in quale sessione si trova)
  const exerciseSessionMap = useMemo(() => {
    const m = new Map<number, string>();
    for (const s of sessions) {
      for (const e of s.esercizi) {
        if (!m.has(e.id_esercizio)) m.set(e.id_esercizio, s.nome_sessione);
      }
    }
    return m;
  }, [sessions]);

  // Raggruppa per condizione medica
  const conditionGroups = useMemo(() => {
    if (!safetyMap) return [];

    const groupMap = new Map<number, ConditionGroup>();

    for (const exId of exerciseIdsInPlan) {
      const entry = safetyMap[exId];
      if (!entry) continue;

      const exercise = exerciseMap.get(exId);
      if (!exercise) continue;

      for (const cond of entry.conditions) {
        let group = groupMap.get(cond.id);
        if (!group) {
          group = {
            conditionId: cond.id,
            nome: cond.nome,
            categoria: cond.categoria,
            exercises: [],
            worstSeverity: cond.severita,
          };
          groupMap.set(cond.id, group);
        }

        group.exercises.push({
          exerciseId: exId,
          nome: exercise.nome,
          pattern: exercise.pattern_movimento,
          sessione: exerciseSessionMap.get(exId) ?? "",
          severity: cond.severita,
          nota: cond.nota,
        });

        if ((SEVERITY_ORDER[cond.severita] ?? 0) > (SEVERITY_ORDER[group.worstSeverity] ?? 0)) {
          group.worstSeverity = cond.severita;
        }
      }
    }

    // Ordina per severita' (avoid first) poi per nome
    return Array.from(groupMap.values()).sort((a, b) => {
      const sevDiff = (SEVERITY_ORDER[b.worstSeverity] ?? 0) - (SEVERITY_ORDER[a.worstSeverity] ?? 0);
      if (sevDiff !== 0) return sevDiff;
      return a.nome.localeCompare(b.nome, "it");
    });
  }, [safetyMap, exerciseIdsInPlan, exerciseMap, exerciseSessionMap]);

  // KPI
  const kpi = useMemo(() => {
    let avoid = 0, modify = 0, caution = 0;
    const seen = new Set<string>();
    for (const g of conditionGroups) {
      for (const ex of g.exercises) {
        const key = `${ex.exerciseId}:${ex.severity}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (ex.severity === "avoid") avoid++;
        else if (ex.severity === "modify") modify++;
        else caution++;
      }
    }
    return { avoid, modify, caution, conditions: conditionGroups.length };
  }, [conditionGroups]);

  const toggleCondition = (id: number) => {
    setExpandedConditions((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Nessun cliente assegnato o nessuna safety map
  if (!safetyMap) {
    return (
      <div className="rounded-lg border p-4">
        <h4 className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
          <ShieldCheck className="h-4 w-4" />
          Profilo Clinico-Safety
        </h4>
        <p className="text-sm text-muted-foreground mt-2">
          Assegna un cliente con anamnesi per visualizzare il profilo clinico.
        </p>
      </div>
    );
  }

  // Nessuna condizione rilevante
  if (conditionGroups.length === 0) {
    return (
      <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20 p-4">
        <h4 className="text-sm font-semibold flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
          <ShieldCheck className="h-4 w-4" />
          Profilo Clinico-Safety
        </h4>
        <p className="text-sm text-emerald-600 dark:text-emerald-400 mt-1">
          Nessuna controindicazione rilevata per gli esercizi in scheda.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border p-4 space-y-3">
      {/* Header + KPI */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-red-500" />
          Profilo Clinico-Safety
        </h4>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">
            {kpi.conditions} {kpi.conditions === 1 ? "condizione" : "condizioni"}
          </span>
          {kpi.avoid > 0 && (
            <span className={SEVERITY_CONFIG.avoid.badge + " px-1.5 py-0.5 rounded-full font-medium"}>
              {kpi.avoid} evitare
            </span>
          )}
          {kpi.modify > 0 && (
            <span className={SEVERITY_CONFIG.modify.badge + " px-1.5 py-0.5 rounded-full font-medium"}>
              {kpi.modify} adattare
            </span>
          )}
          {kpi.caution > 0 && (
            <span className={SEVERITY_CONFIG.caution.badge + " px-1.5 py-0.5 rounded-full font-medium"}>
              {kpi.caution} cautela
            </span>
          )}
        </div>
      </div>

      {/* Condition groups */}
      <div className="space-y-2">
        {conditionGroups.map((group) => {
          const isExpanded = expandedConditions.has(group.conditionId);
          const config = SEVERITY_CONFIG[group.worstSeverity];
          const Icon = config.icon;

          return (
            <div
              key={group.conditionId}
              className={`rounded-md border ${config.border} ${config.bg}`}
            >
              {/* Condition header */}
              <button
                onClick={() => toggleCondition(group.conditionId)}
                className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm"
              >
                {isExpanded ? (
                  <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                )}
                <Icon className={`h-4 w-4 shrink-0 ${config.color}`} />
                <span className="font-medium flex-1">{group.nome}</span>
                <span className="text-xs text-muted-foreground">
                  {CATEGORIA_LABELS[group.categoria] ?? group.categoria}
                </span>
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${config.badge}`}>
                  {group.exercises.length} {group.exercises.length === 1 ? "esercizio" : "esercizi"}
                </span>
              </button>

              {/* Expanded: exercise list */}
              {isExpanded && (
                <div className="px-3 pb-3 space-y-1.5">
                  {group.exercises
                    .sort((a, b) => (SEVERITY_ORDER[b.severity] ?? 0) - (SEVERITY_ORDER[a.severity] ?? 0))
                    .map((ex) => {
                      const exConfig = SEVERITY_CONFIG[ex.severity];
                      return (
                        <div
                          key={`${group.conditionId}-${ex.exerciseId}`}
                          className="flex items-start gap-2 text-xs pl-6"
                        >
                          <span className={`font-medium shrink-0 ${exConfig.color}`}>
                            {exConfig.label}
                          </span>
                          <div className="min-w-0 flex-1">
                            <span className="font-medium">{ex.nome}</span>
                            <span className="text-muted-foreground ml-1">
                              ({ex.pattern}) — {ex.sessione}
                            </span>
                            {ex.nota && (
                              <p className="text-muted-foreground mt-0.5">{ex.nota}</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  <p className="text-[10px] text-muted-foreground pl-6 pt-1">
                    Fonte: ACSM 2021 — Popolazioni speciali
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
