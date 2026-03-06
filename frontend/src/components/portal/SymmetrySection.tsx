"use client";

/**
 * SymmetrySection — Simmetria bilaterale R vs L (braccia, cosce, polpacci).
 */

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Ruler, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { SymmetryPair, Severity } from "@/lib/clinical-analysis";

interface SymmetrySectionProps {
  symmetry: SymmetryPair[];
  clientId: number;
}

const SEVERITY_BADGE: Record<string, string> = {
  positive: "border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  neutral: "border-zinc-200 bg-zinc-100 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  info: "border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  warning: "border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  alert: "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  positive: "Simmetrico",
  neutral: "Neutro",
  info: "Informativo",
  warning: "Asimmetria lieve",
  alert: "Asimmetria significativa",
};

function getBarWidth(value: number, max: number): string {
  return `${Math.min(100, (value / max) * 100)}%`;
}

export function SymmetrySection({ symmetry, clientId }: SymmetrySectionProps) {
  const [open, setOpen] = useState(true);

  const hasData = symmetry.length > 0;

  // Overall severity
  const worstSeverity: Severity = symmetry.reduce<Severity>((worst, pair) => {
    const rank: Record<Severity, number> = { positive: 0, neutral: 1, info: 2, warning: 3, alert: 4 };
    return rank[pair.severity] > rank[worst] ? pair.severity : worst;
  }, "positive");

  const borderColor = !hasData
    ? "border-l-zinc-300"
    : worstSeverity === "alert"
      ? "border-l-red-500"
      : worstSeverity === "warning"
        ? "border-l-amber-500"
        : "border-l-indigo-400";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={`rounded-xl border border-l-4 ${borderColor} bg-white shadow-sm dark:bg-zinc-900`}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex w-full items-center justify-between p-4 text-left">
            <div className="flex items-center gap-2">
              <Ruler className="h-4 w-4 text-indigo-500" />
              <h2 className="text-sm font-semibold">Simmetria Bilaterale</h2>
              {hasData && (
                <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[worstSeverity]}`}>
                  {SEVERITY_LABEL[worstSeverity]}
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t px-4 pb-4 pt-3">
            {!hasData && (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm text-muted-foreground">
                  Nessuna misurazione bilaterale disponibile (braccia, cosce, polpacci)
                </p>
              </div>
            )}

            {hasData && (
              <div className="space-y-4">
                {symmetry.map((pair) => {
                  const maxVal = Math.max(pair.right, pair.left, 1);

                  return (
                    <div key={pair.label} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold">{pair.label}</p>
                        <Badge variant="outline" className={`text-[10px] ${SEVERITY_BADGE[pair.severity]}`}>
                          {pair.note}
                        </Badge>
                      </div>

                      <div className="mt-3 space-y-2">
                        {/* Right */}
                        <div className="flex items-center gap-2">
                          <span className="w-16 text-right text-xs text-muted-foreground">{pair.rightLabel}</span>
                          <div className="relative h-5 flex-1 overflow-hidden rounded bg-zinc-100 dark:bg-zinc-800">
                            <div
                              className="absolute inset-y-0 left-0 rounded bg-indigo-500/80 transition-all duration-500"
                              style={{ width: getBarWidth(pair.right, maxVal) }}
                            />
                            <span className="absolute inset-y-0 right-2 flex items-center text-[10px] font-bold tabular-nums">
                              {pair.right} cm
                            </span>
                          </div>
                        </div>

                        {/* Left */}
                        <div className="flex items-center gap-2">
                          <span className="w-16 text-right text-xs text-muted-foreground">{pair.leftLabel}</span>
                          <div className="relative h-5 flex-1 overflow-hidden rounded bg-zinc-100 dark:bg-zinc-800">
                            <div
                              className="absolute inset-y-0 left-0 rounded bg-violet-500/80 transition-all duration-500"
                              style={{ width: getBarWidth(pair.left, maxVal) }}
                            />
                            <span className="absolute inset-y-0 right-2 flex items-center text-[10px] font-bold tabular-nums">
                              {pair.left} cm
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Delta */}
                      <div className="mt-2 flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          Δ {pair.delta.toFixed(1)} cm ({pair.deltaPct.toFixed(1)}%)
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="inline-block h-2 w-2 rounded-full bg-indigo-500" /> Dx
                          <span className="ml-1 inline-block h-2 w-2 rounded-full bg-violet-500" /> Sx
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* CTA */}
            <div className="flex justify-end">
              <Link href={`/clienti/${clientId}/misurazioni?new=1`}>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  Misura Bilaterale
                </Button>
              </Link>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
