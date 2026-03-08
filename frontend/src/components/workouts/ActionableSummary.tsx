// src/components/workouts/ActionableSummary.tsx
"use client";

/**
 * Sezione 4 — Riepilogo Operativo.
 *
 * Aggrega i risultati delle sezioni 1-3 in una lista di azioni prioritizzate.
 * Priorita' deterministica:
 * 1. Safety avoid — esercizi controindicati
 * 2. Safety modify — esercizi da adattare
 * 3. Squilibri biomeccanici — rapporti fuori tolleranza
 * 4. Muscoli sotto MEV — deficit di volume
 * 5. Frequenza < 2x — stimolazione insufficiente
 * 6. Recovery overlap — sovrapposizione tra sessioni
 *
 * Le voci "tutto ok" (check verdi) in fondo.
 */

import { useMemo } from "react";
import {
  CheckCircle2,
  ShieldAlert,
  AlertTriangle,
  Scale,
  Dumbbell,
  Clock,
  Zap,
} from "lucide-react";

import type {
  TSAnalisiPiano,
  ExerciseSafetyEntry,
  Exercise,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface ActionableSummaryProps {
  analysis: TSAnalisiPiano;
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

interface ActionItem {
  priority: number;
  type: "critical" | "warning" | "info";
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  fonte: string;
}

interface OkItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

export function ActionableSummary({
  analysis,
  safetyMap,
  sessions,
  exerciseMap,
}: ActionableSummaryProps) {
  const { actions, okItems } = useMemo(() => {
    const acts: ActionItem[] = [];
    const oks: OkItem[] = [];

    // Collect exercise IDs in plan
    const exIdsInPlan = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) exIdsInPlan.add(e.id_esercizio);
    }

    // ── 1. Safety avoid ──
    if (safetyMap) {
      const avoidExercises: string[] = [];
      const modifyExercises: string[] = [];
      for (const exId of exIdsInPlan) {
        const entry = safetyMap[exId];
        if (!entry) continue;
        const ex = exerciseMap.get(exId);
        const name = ex?.nome ?? `#${exId}`;
        if (entry.severity === "avoid") avoidExercises.push(name);
        else if (entry.severity === "modify") modifyExercises.push(name);
      }

      if (avoidExercises.length > 0) {
        acts.push({
          priority: 1,
          type: "critical",
          icon: ShieldAlert,
          title: `${avoidExercises.length} ${avoidExercises.length === 1 ? "esercizio controindicato" : "esercizi controindicati"}`,
          description: `${avoidExercises.join(", ")}. Considerare sostituzione con alternative sicure.`,
          fonte: "ACSM 2021",
        });
      }

      // ── 2. Safety modify ──
      if (modifyExercises.length > 0) {
        acts.push({
          priority: 2,
          type: "warning",
          icon: AlertTriangle,
          title: `${modifyExercises.length} ${modifyExercises.length === 1 ? "esercizio da adattare" : "esercizi da adattare"}`,
          description: `${modifyExercises.join(", ")}. Verificare ROM, carico o grip.`,
          fonte: "ACSM 2021",
        });
      }

      if (avoidExercises.length === 0 && modifyExercises.length === 0) {
        oks.push({ icon: ShieldAlert, label: "Nessuna controindicazione clinica" });
      }
    }

    // ── 3. Squilibri biomeccanici ──
    const unbalanced = (analysis.dettaglio_rapporti ?? []).filter((r) => !r.in_tolleranza);
    if (unbalanced.length > 0) {
      for (const r of unbalanced) {
        acts.push({
          priority: 3,
          type: "warning",
          icon: Scale,
          title: `Squilibrio ${r.nome}`,
          description: `Valore ${r.valore.toFixed(2)} vs target ${r.target.toFixed(2)} (±${r.tolleranza.toFixed(2)}). Riequilibrare il volume tra i due lati.`,
          fonte: r.fonte,
        });
      }
    } else if ((analysis.dettaglio_rapporti ?? []).length > 0) {
      oks.push({ icon: Scale, label: "Rapporti biomeccanici bilanciati" });
    }

    // ── 4. Muscoli sotto MEV ──
    const deficit = (analysis.dettaglio_muscoli ?? []).filter(
      (m) => m.stato === "sotto_mev"
    );
    if (deficit.length > 0) {
      const names = deficit.map((m) => m.muscolo).join(", ");
      acts.push({
        priority: 4,
        type: "warning",
        icon: Dumbbell,
        title: `${deficit.length} ${deficit.length === 1 ? "muscolo sotto volume minimo" : "muscoli sotto volume minimo"}`,
        description: `${names}. Volume sotto MEV — stimolo insufficiente per adattamento.`,
        fonte: "Schoenfeld 2017",
      });
    } else if ((analysis.dettaglio_muscoli ?? []).length > 0) {
      const optimal = (analysis.dettaglio_muscoli ?? []).filter(
        (m) => m.stato === "ottimale" || m.stato === "mev_mav"
      ).length;
      oks.push({
        icon: Dumbbell,
        label: `${optimal}/${(analysis.dettaglio_muscoli ?? []).length} muscoli con volume adeguato`,
      });
    }

    // ── 5. Frequenza < 2x ──
    const freqMap = analysis.frequenza_per_muscolo ?? {};
    const lowFreq = Object.entries(freqMap).filter(([, f]) => f < 2);
    if (lowFreq.length > 0) {
      const names = lowFreq.map(([m]) => m).join(", ");
      acts.push({
        priority: 5,
        type: "info",
        icon: Clock,
        title: `${lowFreq.length} ${lowFreq.length === 1 ? "muscolo" : "muscoli"} con frequenza < 2x/sett`,
        description: `${names}. Frequenza minima 2x/settimana raccomandata per ipertrofia.`,
        fonte: "Schoenfeld 2016",
      });
    } else if (Object.keys(freqMap).length > 0) {
      oks.push({ icon: Clock, label: "Frequenza muscolare >= 2x/settimana" });
    }

    // ── 6. Recovery overlap ──
    const overlaps = analysis.recovery_overlaps ?? [];
    if (overlaps.length > 0) {
      const worst = overlaps.reduce((a, b) =>
        b.muscoli_overlap.length > a.muscoli_overlap.length ? b : a
      );
      acts.push({
        priority: 6,
        type: "info",
        icon: Zap,
        title: `Sovrapposizione recupero: ${worst.sessione_a} ↔ ${worst.sessione_b}`,
        description: `${worst.muscoli_overlap.length} muscoli in comune (${worst.muscoli_overlap.slice(0, 3).join(", ")}${worst.muscoli_overlap.length > 3 ? "..." : ""}). Valutare distanziamento sessioni.`,
        fonte: "NSCA 2016",
      });
    } else if (sessions.length > 1) {
      oks.push({ icon: Zap, label: "Nessun overlap critico tra sessioni" });
    }

    acts.sort((a, b) => a.priority - b.priority);
    return { actions: acts, okItems: oks };
  }, [analysis, safetyMap, sessions, exerciseMap]);

  const TYPE_STYLES = {
    critical: "border-l-red-500 bg-red-50/50 dark:bg-red-950/20",
    warning: "border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20",
    info: "border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20",
  };

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">
          Riepilogo Operativo
        </h4>
        {actions.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {actions.length} {actions.length === 1 ? "azione" : "azioni"}
          </span>
        )}
      </div>

      {/* Action items */}
      {actions.length > 0 && (
        <div className="space-y-2">
          {actions.map((action, i) => {
            const Icon = action.icon;
            return (
              <div
                key={i}
                className={`rounded-md border-l-4 px-3 py-2 ${TYPE_STYLES[action.type]}`}
              >
                <div className="flex items-start gap-2">
                  <Icon className="h-4 w-4 shrink-0 mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{action.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {action.description}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {action.fonte}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* OK items */}
      {okItems.length > 0 && (
        <div className="space-y-1 pt-1">
          {okItems.map((ok, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              <span>{ok.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* All clear */}
      {actions.length === 0 && okItems.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          <span>Nessuna azione richiesta — scheda ben bilanciata.</span>
        </div>
      )}
    </div>
  );
}
