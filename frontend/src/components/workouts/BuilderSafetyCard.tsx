// src/components/workouts/BuilderSafetyCard.tsx
"use client";

/**
 * Pannello clinico collapsibile per il builder schede.
 *
 * Collapsed: singola riga compatta (icona + nome + mini KPI inline + chevron).
 * Expanded: KPI grid, condition badges, Risk Body Map, medication flags,
 *           condizioni raggruppate per categoria con esercizi coinvolti.
 */

import { useState } from "react";
import { Shield, ShieldAlert, AlertTriangle, Info as InfoIcon, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { RiskBodyMap } from "./RiskBodyMap";
import { CONDITION_CATEGORY_LABELS } from "@/lib/builder-utils";
import type { SafetyConditionDetail, SafetyMapResponse, MedicationFlag } from "@/types/api";

interface GroupedCondition {
  nome: string;
  worstSeverity: string;
  exercises: { nome: string; severity: string }[];
}

interface BuilderSafetyCardProps {
  safetyMap: SafetyMapResponse;
  safetyStats: { avoid: number; caution: number; modify: number; total: number };
  safetyConditionStats: { detected: number; mapped: number; bodyTagged: number; planImpacted: number };
  groupedConditions: Map<string, GroupedCondition[]>;
  uniqueConditionsForMap: SafetyConditionDetail[];
  clientId: number | null;
  onNavigateToClient: (clientId: number) => void;
}

export function BuilderSafetyCard({
  safetyMap,
  safetyStats,
  safetyConditionStats,
  groupedConditions,
  uniqueConditionsForMap,
  clientId,
  onNavigateToClient,
}: BuilderSafetyCardProps) {
  const [expanded, setExpanded] = useState(false);
  const hasAvoid = safetyStats.avoid > 0;
  const hasCaution = safetyStats.caution > 0;
  const borderColor = hasAvoid ? "border-l-red-500" : hasCaution ? "border-l-amber-400" : "border-l-blue-400";
  const iconColor = hasAvoid ? "text-red-500" : hasCaution ? "text-amber-500" : "text-blue-500";

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <Card className={`border-l-4 ${borderColor} transition-all duration-200 shadow-sm`}>
        <CardContent className="p-0">
          {/* ── Collapsed: single compact row ── */}
          <CollapsibleTrigger asChild>
            <button className="flex items-center justify-between w-full text-left px-4 py-2 group hover:bg-muted/20 transition-colors rounded-r-xl">
              <div className="flex items-center gap-2 min-w-0">
                <Shield className={`h-3.5 w-3.5 shrink-0 ${iconColor}`} />
                <span className="text-xs font-semibold tracking-tight truncate">Profilo Clinico</span>
                <span className="text-[11px] text-muted-foreground/60 truncate hidden sm:inline">— {safetyMap.client_nome}</span>
              </div>
              {/* Mini KPI inline (visible when collapsed) */}
              <div className="flex items-center gap-2.5">
                {!expanded && (
                  <div className="flex items-center gap-2 text-[10px] font-semibold tabular-nums">
                    <span className="text-muted-foreground/70">{safetyMap.condition_count} cond.</span>
                    {safetyStats.avoid > 0 && (
                      <span className="text-red-600 dark:text-red-400">{safetyStats.avoid} evit.</span>
                    )}
                    {safetyStats.modify > 0 && (
                      <span className="text-blue-600 dark:text-blue-400">{safetyStats.modify} adatt.</span>
                    )}
                    {safetyStats.caution > 0 && (
                      <span className="text-amber-600 dark:text-amber-400">{safetyStats.caution} caut.</span>
                    )}
                  </div>
                )}
                <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-muted-foreground/40 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`} />
              </div>
            </button>
          </CollapsibleTrigger>

          {/* ── Expanded section ── */}
          <CollapsibleContent>
            <div className="px-4 pb-4 space-y-3">
              <Separator className="opacity-50" />

              {/* KPI grid */}
              <div className="grid grid-cols-4 gap-2">
                <KpiBadge label="Condizioni" value={safetyMap.condition_count} variant="muted" />
                <KpiBadge label="Evitare" value={safetyStats.avoid} variant="red" />
                <KpiBadge label="Cautela" value={safetyStats.caution} variant="amber" />
                <KpiBadge label="Adattare" value={safetyStats.modify} variant="blue" />
              </div>

              {/* Badge condizioni */}
              <div className="flex flex-wrap gap-1.5">
                {safetyMap.condition_names.map((name) => (
                  <Badge key={name} variant="outline" className="text-[10px] font-normal">{name}</Badge>
                ))}
              </div>

              <div className="text-[10px] text-muted-foreground/70 leading-relaxed">
                {safetyConditionStats.planImpacted} condizioni impattano la scheda corrente su {safetyConditionStats.detected} rilevate.
                {safetyConditionStats.mapped < safetyConditionStats.detected && (
                  <span> {safetyConditionStats.mapped} sono gia&apos; mappate nel catalogo safety.</span>
                )}
                {safetyConditionStats.bodyTagged < safetyConditionStats.mapped && (
                  <span> {safetyConditionStats.bodyTagged} hanno body tags anatomici renderizzabili.</span>
                )}
              </div>

              {/* Risk Body Map */}
              {uniqueConditionsForMap.length > 0 && (
                <div className="flex flex-col items-center">
                  <RiskBodyMap conditions={uniqueConditionsForMap} />
                  <div className="flex items-center gap-3 mt-1">
                    <LegendDot color="bg-red-500" label="Evitare" />
                    <LegendDot color="bg-amber-500" label="Cautela" />
                    <LegendDot color="bg-blue-500" label="Adattare" />
                  </div>
                </div>
              )}

              {/* Medication flags */}
              {safetyMap.medication_flags && safetyMap.medication_flags.length > 0 && (
                <div>
                  <div className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground/60 mb-1.5">
                    Farmaci Rilevanti
                  </div>
                  <div className="space-y-1.5">
                    {safetyMap.medication_flags.map((mf: MedicationFlag) => (
                      <div key={mf.flag} className="flex items-start gap-2 text-xs">
                        <InfoIcon className="h-3.5 w-3.5 shrink-0 mt-0.5 text-purple-500" />
                        <p className="text-muted-foreground/80 leading-relaxed">{mf.nota}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Grouped conditions */}
              {Array.from(groupedConditions.entries()).map(([categoria, conditions]) => (
                <div key={categoria}>
                  <div className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground/60 mb-1.5">
                    {CONDITION_CATEGORY_LABELS[categoria] ?? categoria}
                  </div>
                  <div className="space-y-2.5">
                    {conditions.map((cond) => (
                      <ConditionRow key={cond.nome} cond={cond} />
                    ))}
                  </div>
                </div>
              ))}

              {clientId && (
                <button
                  onClick={() => onNavigateToClient(clientId)}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline mt-1"
                >
                  Vai al profilo di {safetyMap.client_nome.split(" ")[0]}
                </button>
              )}
            </div>
          </CollapsibleContent>
        </CardContent>
      </Card>
    </Collapsible>
  );
}

// ── Sub-components ──

const KPI_VARIANTS = {
  muted: { bg: "bg-muted/40", text: "", label: "text-muted-foreground" },
  red: { bg: "bg-red-50 dark:bg-red-950/30", text: "text-red-600 dark:text-red-400", label: "text-red-600/70 dark:text-red-400/70" },
  amber: { bg: "bg-amber-50 dark:bg-amber-950/30", text: "text-amber-600 dark:text-amber-400", label: "text-amber-600/70 dark:text-amber-400/70" },
  blue: { bg: "bg-blue-50 dark:bg-blue-950/30", text: "text-blue-600 dark:text-blue-400", label: "text-blue-600/70 dark:text-blue-400/70" },
} as const;

function KpiBadge({ label, value, variant }: { label: string; value: number; variant: keyof typeof KPI_VARIANTS }) {
  const v = KPI_VARIANTS[variant];
  return (
    <div className={`rounded-lg ${v.bg} px-3 py-2 text-center ring-1 ring-inset ring-black/[0.03] dark:ring-white/[0.05]`}>
      <div className={`text-lg font-extrabold tracking-tighter tabular-nums ${v.text}`}>{value}</div>
      <div className={`text-[9px] ${v.label} uppercase tracking-widest font-semibold`}>{label}</div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1 text-[9px] text-muted-foreground/70 font-medium">
      <span className={`h-2 w-2 rounded-full ${color}`} /> {label}
    </span>
  );
}

function ConditionRow({ cond }: { cond: GroupedCondition }) {
  const SevIcon = cond.worstSeverity === "avoid" ? ShieldAlert : cond.worstSeverity === "caution" ? AlertTriangle : InfoIcon;
  const sevColor = cond.worstSeverity === "avoid" ? "text-red-500" : cond.worstSeverity === "caution" ? "text-amber-500" : "text-blue-500";
  const sevLabelColor = cond.worstSeverity === "avoid" ? "text-red-600 dark:text-red-400" : cond.worstSeverity === "caution" ? "text-amber-600 dark:text-amber-400" : "text-blue-600 dark:text-blue-400";
  const sevLabel = cond.worstSeverity === "avoid" ? "Evitare" : cond.worstSeverity === "caution" ? "Cautela" : "Adattare";

  return (
    <div>
      <div className="flex items-center gap-2 text-xs">
        <SevIcon className={`h-3.5 w-3.5 shrink-0 ${sevColor}`} />
        <span className="flex-1 font-medium">{cond.nome}</span>
        <span className={`text-[10px] font-semibold ${sevLabelColor}`}>{sevLabel}</span>
      </div>
      {cond.exercises.length > 0 && (
        <div className="ml-5.5 mt-1 flex flex-wrap gap-1">
          {cond.exercises.map((ex) => (
            <span
              key={ex.nome}
              className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
                ex.severity === "avoid"
                  ? "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400 ring-red-200/50 dark:ring-red-800/40"
                  : ex.severity === "caution"
                    ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 ring-amber-200/50 dark:ring-amber-800/40"
                    : "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 ring-blue-200/50 dark:ring-blue-800/40"
              }`}
            >
              {ex.nome}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
