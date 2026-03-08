"use client";

/**
 * TrainingHeroCard — Hero card KPI per MyTrainer.
 *
 * Parallelo a ReadinessHeroCard (MyPortal): ring score + 4 KPI card.
 * Score = avg_training_score (science 60% + compliance 40%).
 */

import { AnimatedNumber } from "@/components/ui/animated-number";
import { HealthScoreRing } from "@/components/portal/HealthScoreRing";
import type { TrainingMethodologySummary } from "@/types/api";

interface TrainingHeroCardProps {
  summary: TrainingMethodologySummary;
}

export function TrainingHeroCard({ summary }: TrainingHeroCardProps) {
  return (
    <div className="rounded-xl border border-l-4 border-l-teal-500 bg-gradient-to-br from-teal-50/80 via-white to-emerald-50/60 p-5 shadow-sm dark:from-teal-950/20 dark:via-zinc-900 dark:to-emerald-950/10">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        {/* Ring */}
        <div className="shrink-0">
          <HealthScoreRing
            score={Math.round(summary.avg_training_score)}
            size={96}
            strokeWidth={8}
          />
        </div>

        {/* KPI grid */}
        <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-5">
          <div className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Con problemi
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-amber-700 dark:text-amber-300">
              <AnimatedNumber value={summary.plans_with_issues} />
            </p>
          </div>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-2 dark:border-emerald-900/40 dark:bg-emerald-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Eccellenti
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-emerald-700 dark:text-emerald-300">
              <AnimatedNumber value={summary.plans_excellent} />
            </p>
          </div>
          <div className="rounded-lg border border-blue-200 bg-blue-50/80 px-3 py-2 dark:border-blue-900/40 dark:bg-blue-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Piani attivi
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-blue-700 dark:text-blue-300">
              <AnimatedNumber value={summary.active_plans} />
            </p>
          </div>
          <div className="rounded-lg border border-teal-200 bg-teal-50/80 px-3 py-2 dark:border-teal-900/40 dark:bg-teal-950/20">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Score medio
            </p>
            <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-teal-700 dark:text-teal-300">
              <AnimatedNumber value={Math.round(summary.avg_training_score)} />
              <span className="text-base">%</span>
            </p>
          </div>
          {summary.avg_effective_score > 0 && (
            <div className="rounded-lg border border-violet-200 bg-violet-50/80 px-3 py-2 dark:border-violet-900/40 dark:bg-violet-950/20">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Effettivo medio
              </p>
              <p className="mt-1 text-2xl font-extrabold leading-none tabular-nums text-violet-700 dark:text-violet-300">
                <AnimatedNumber value={Math.round(summary.avg_effective_score)} />
                <span className="text-base">%</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
