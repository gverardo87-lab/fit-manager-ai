// src/components/nutrition/NutritionDayHeader.tsx
"use client";

/**
 * Header del DayDetailPanel con:
 * - Nome giorno + badge kcal + riga macro P/C/G/F
 * - MacroDonutRing SVG (distribuzione calorica P/C/G)
 * - Target bar kcal (se obiettivo_calorico)
 * - Target bars P / C / G (se target macro definiti nel piano)
 * - Fibra giornaliera con riferimento OMS 25g
 * - Copia giorno su altro giorno della settimana
 * - Tasto "← Torna alla griglia"
 */

import { useState } from "react";
import { ArrowLeft, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCopyDay } from "@/hooks/useNutrition";
import type { NutritionPlanDetail } from "@/types/api";
import { GIORNO_OPTIONS } from "@/types/api";

// ── MacroDonutRing ────────────────────────────────────────────────────────

const R = 38;
const CX = 50;
const CY = 50;
const CIRC = 2 * Math.PI * R; // ≈ 238.76

function MacroDonutRing({ p, c, g, kcal }: { p: number; c: number; g: number; kcal: number }) {
  const macroKcal = p * 4 + c * 4 + g * 9;
  if (macroKcal === 0) {
    return (
      <svg viewBox="0 0 100 100" className="w-[76px] h-[76px]">
        <circle cx={CX} cy={CY} r={R} fill="none" strokeWidth={8} stroke="currentColor" className="text-muted/30" />
        <text x={CX} y={CY + 4} textAnchor="middle" fontSize="11" fontWeight="600" fill="currentColor" opacity={0.4}>—</text>
      </svg>
    );
  }
  const pLen = (p * 4 / macroKcal) * CIRC;
  const cLen = (c * 4 / macroKcal) * CIRC;
  const gLen = (g * 9 / macroKcal) * CIRC;

  return (
    <svg viewBox="0 0 100 100" className="w-[76px] h-[76px]">
      {/* Track */}
      <circle cx={CX} cy={CY} r={R} fill="none" strokeWidth={8} stroke="currentColor" className="text-muted/20" />
      {/* P – blue-600 */}
      {pLen > 0.5 && (
        <circle cx={CX} cy={CY} r={R} fill="none" strokeWidth={8} stroke="#2563eb"
          strokeDasharray={`${pLen} ${CIRC}`} strokeDashoffset={0}
          transform={`rotate(-90 ${CX} ${CY})`} />
      )}
      {/* C – amber-600 */}
      {cLen > 0.5 && (
        <circle cx={CX} cy={CY} r={R} fill="none" strokeWidth={8} stroke="#d97706"
          strokeDasharray={`${cLen} ${CIRC}`} strokeDashoffset={-pLen}
          transform={`rotate(-90 ${CX} ${CY})`} />
      )}
      {/* G – rose-500 */}
      {gLen > 0.5 && (
        <circle cx={CX} cy={CY} r={R} fill="none" strokeWidth={8} stroke="#f43f5e"
          strokeDasharray={`${gLen} ${CIRC}`} strokeDashoffset={-(pLen + cLen)}
          transform={`rotate(-90 ${CX} ${CY})`} />
      )}
      {/* Center label */}
      <text x={CX} y={CY - 3} textAnchor="middle" fontSize="12" fontWeight="700" fill="currentColor">
        {Math.round(kcal)}
      </text>
      <text x={CX} y={CY + 11} textAnchor="middle" fontSize="8" fill="currentColor" opacity={0.55}>
        kcal
      </text>
    </svg>
  );
}

// ── TargetBar ─────────────────────────────────────────────────────────────

function TargetBar({ value, target, color }: { value: number; target: number; color: string }) {
  const pct = Math.min(Math.round((value / target) * 100), 100);
  const over = value > target;
  return (
    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
      <div className={`h-full rounded-full transition-all ${over ? "bg-rose-400" : color}`}
        style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── MacroTargetRow ────────────────────────────────────────────────────────

function MacroTargetRow({ label, value, target, colorText, colorBar }: {
  label: string; value: number; target: number; colorText: string; colorBar: string;
}) {
  const pct = Math.round((value / target) * 100);
  const over = value > target;
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-xs">
        <span className={`font-medium ${colorText}`}>{label} {Math.round(value)}g</span>
        <span className={over ? "text-rose-500 font-medium" : "text-muted-foreground"}>
          / {target}g ({pct}%)
        </span>
      </div>
      <TargetBar value={value} target={target} color={colorBar} />
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

export interface DayTotals {
  kcal: number;
  p: number;
  c: number;
  g: number;
  fibra: number;
}

interface NutritionDayHeaderProps {
  plan: NutritionPlanDetail;
  planId: number;
  giorno: number;
  totals: DayTotals;
  onBack: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────

export function NutritionDayHeader({ plan, planId, giorno, totals, onBack }: NutritionDayHeaderProps) {
  const [copyOpen, setCopyOpen] = useState(false);
  const copyDay = useCopyDay();

  const giornoLabel = GIORNO_OPTIONS.find((g) => g.value === giorno)?.label ?? "Giorno";
  const copyTargets = GIORNO_OPTIONS.filter((g) => g.value !== giorno);
  const hasData = totals.kcal > 0;

  const handleCopy = (targetGiorno: number) => {
    setCopyOpen(false);
    copyDay.mutate({ planId, sourceGiorno: giorno, targetGiorno });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        {/* Left: labels + target bars */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Title */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <h3 className="text-lg font-bold">{giornoLabel}</h3>
            {hasData && (
              <Badge variant="secondary" className="text-sm font-bold text-emerald-700 bg-emerald-50 px-2.5">
                {Math.round(totals.kcal)} kcal
              </Badge>
            )}
          </div>

          {/* Macro row */}
          {hasData && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-blue-600 tabular-nums">P {Math.round(totals.p)}g</span>
              <span className="text-muted-foreground/40 text-xs">·</span>
              <span className="text-sm font-medium text-amber-600 tabular-nums">C {Math.round(totals.c)}g</span>
              <span className="text-muted-foreground/40 text-xs">·</span>
              <span className="text-sm font-medium text-rose-500 tabular-nums">G {Math.round(totals.g)}g</span>
              {totals.fibra > 0 && (
                <>
                  <span className="text-muted-foreground/40 text-xs">·</span>
                  <span className={`text-sm font-medium tabular-nums ${totals.fibra >= 25 ? "text-emerald-600" : "text-violet-600"}`}>
                    F {Math.round(totals.fibra)}g
                  </span>
                </>
              )}
            </div>
          )}

          {/* Kcal target bar */}
          {plan.obiettivo_calorico && hasData && (
            <div className="space-y-0.5 max-w-xs">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Target: {plan.obiettivo_calorico} kcal</span>
                <span className={totals.kcal > plan.obiettivo_calorico ? "text-rose-500 font-medium" : "text-emerald-600 font-medium"}>
                  {Math.round((totals.kcal / plan.obiettivo_calorico) * 100)}%
                </span>
              </div>
              <TargetBar value={totals.kcal} target={plan.obiettivo_calorico} color="bg-emerald-500" />
            </div>
          )}

          {/* Macro target bars */}
          {hasData && (plan.proteine_g_target || plan.carboidrati_g_target || plan.grassi_g_target) && (
            <div className="space-y-1.5 max-w-xs pt-0.5">
              {plan.proteine_g_target && (
                <MacroTargetRow label="P" value={totals.p} target={plan.proteine_g_target}
                  colorText="text-blue-600" colorBar="bg-blue-500" />
              )}
              {plan.carboidrati_g_target && (
                <MacroTargetRow label="C" value={totals.c} target={plan.carboidrati_g_target}
                  colorText="text-amber-600" colorBar="bg-amber-500" />
              )}
              {plan.grassi_g_target && (
                <MacroTargetRow label="G" value={totals.g} target={plan.grassi_g_target}
                  colorText="text-rose-500" colorBar="bg-rose-400" />
              )}
            </div>
          )}

          {/* Fibra OMS */}
          {totals.fibra > 0 && (
            <div className="space-y-0.5 max-w-xs">
              <div className="flex items-center justify-between text-xs">
                <span className="text-violet-600 font-medium">Fibra {Math.round(totals.fibra)}g</span>
                <span className={totals.fibra >= 25 ? "text-emerald-600 font-medium" : "text-muted-foreground"}>
                  OMS 25g ({Math.round((totals.fibra / 25) * 100)}%)
                </span>
              </div>
              <TargetBar value={totals.fibra} target={25} color="bg-violet-500" />
            </div>
          )}

          {/* Cosa manca al target? */}
          {hasData && (() => {
            const items: { label: string; color: string }[] = [];
            if (plan.obiettivo_calorico && totals.kcal < plan.obiettivo_calorico)
              items.push({ label: `+${Math.round(plan.obiettivo_calorico - totals.kcal)} kcal`, color: "text-foreground font-semibold" });
            if (plan.proteine_g_target && totals.p < plan.proteine_g_target)
              items.push({ label: `P +${Math.round(plan.proteine_g_target - totals.p)}g`, color: "text-blue-600" });
            if (plan.carboidrati_g_target && totals.c < plan.carboidrati_g_target)
              items.push({ label: `C +${Math.round(plan.carboidrati_g_target - totals.c)}g`, color: "text-amber-600" });
            if (plan.grassi_g_target && totals.g < plan.grassi_g_target)
              items.push({ label: `G +${Math.round(plan.grassi_g_target - totals.g)}g`, color: "text-rose-500" });
            if (items.length === 0) return null;
            return (
              <div className="rounded-md border border-amber-200 bg-amber-50/60 px-3 py-2 max-w-xs">
                <p className="text-xs font-semibold text-amber-700 mb-1">Mancante al target</p>
                <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                  {items.map((item) => (
                    <span key={item.label} className={`text-xs tabular-nums font-medium ${item.color}`}>{item.label}</span>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>

        {/* Right: donut + buttons */}
        <div className="flex flex-col items-end gap-2 shrink-0">
          {hasData && <MacroDonutRing p={totals.p} c={totals.c} g={totals.g} kcal={totals.kcal} />}
          <div className="flex items-center gap-1">
            {/* Copy day dropdown */}
            <div className="relative">
              <Button variant="ghost" size="sm"
                className="gap-1 text-xs text-muted-foreground hover:text-foreground h-7 px-2"
                onClick={() => setCopyOpen((v) => !v)}
                disabled={copyDay.isPending}
                title="Copia tutti i pasti su un altro giorno"
              >
                <Copy className="h-3.5 w-3.5" />
                Copia
              </Button>
              {copyOpen && (
                <div className="absolute right-0 top-8 z-20 min-w-[148px] rounded-lg border bg-popover shadow-md">
                  <p className="px-3 py-2 text-xs uppercase tracking-wide text-muted-foreground border-b">
                    Copia su
                  </p>
                  {copyTargets.map((opt) => (
                    <button key={opt.value} onClick={() => handleCopy(opt.value)}
                      className="w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent"
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {/* Back */}
            <Button variant="ghost" size="sm"
              className="gap-1 text-xs text-muted-foreground hover:text-foreground h-7 px-2"
              onClick={onBack}
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Griglia
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
