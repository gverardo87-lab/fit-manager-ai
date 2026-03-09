// src/components/clients/profile/OnboardingChecklist.tsx
"use client";

/**
 * Onboarding Hub — pannello visivamente prominente per guidare
 * il trainer attraverso la configurazione del cliente.
 *
 * Hero CTA per il prossimo step incompleto + stepper numerato.
 * Si nasconde quando tutti gli step sono completati.
 * Stile ispirato a Linear/Notion onboarding.
 */

import Link from "next/link";
import { Check, ChevronRight, ListChecks } from "lucide-react";
import type { OnboardingStep } from "@/hooks/useClientReadiness";

/** CTA verb per step — specifico, non generico "Inizia". */
const STEP_CTA: Record<string, string> = {
  contratto: "Crea contratto",
  anamnesi: "Compila",
  misurazioni: "Registra",
  scheda: "Crea programma",
  sessione: "Prenota",
};

interface OnboardingChecklistProps {
  steps: OnboardingStep[];
}

/** Colore per ogni step nell'ordine (contratto, anamnesi, misurazioni, scheda, sessione). */
const STEP_COLORS = [
  { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-600 dark:text-blue-400", ring: "ring-blue-200 dark:ring-blue-800", heroBg: "bg-gradient-to-r from-white to-blue-50 dark:from-zinc-800/80 dark:to-blue-950/30" },
  { bg: "bg-rose-100 dark:bg-rose-900/30", text: "text-rose-600 dark:text-rose-400", ring: "ring-rose-200 dark:ring-rose-800", heroBg: "bg-gradient-to-r from-white to-rose-50 dark:from-zinc-800/80 dark:to-rose-950/30" },
  { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-600 dark:text-amber-400", ring: "ring-amber-200 dark:ring-amber-800", heroBg: "bg-gradient-to-r from-white to-amber-50 dark:from-zinc-800/80 dark:to-amber-950/30" },
  { bg: "bg-violet-100 dark:bg-violet-900/30", text: "text-violet-600 dark:text-violet-400", ring: "ring-violet-200 dark:ring-violet-800", heroBg: "bg-gradient-to-r from-white to-violet-50 dark:from-zinc-800/80 dark:to-violet-950/30" },
  { bg: "bg-teal-100 dark:bg-teal-900/30", text: "text-teal-600 dark:text-teal-400", ring: "ring-teal-200 dark:ring-teal-800", heroBg: "bg-gradient-to-r from-white to-teal-50 dark:from-zinc-800/80 dark:to-teal-950/30" },
] as const;

export function OnboardingChecklist({ steps }: OnboardingChecklistProps) {
  const completed = steps.filter((s) => s.completed).length;
  const total = steps.length;
  if (completed === total) return null;

  const pct = Math.round((completed / total) * 100);
  const nextStep = steps.find((s) => !s.completed);
  const nextStepIdx = nextStep ? steps.indexOf(nextStep) : 0;
  const nextColor = STEP_COLORS[nextStepIdx] ?? STEP_COLORS[0];

  return (
    <div className="overflow-hidden rounded-xl border bg-gradient-to-br from-white via-white to-primary/[0.03] shadow-sm transition-all duration-300 dark:from-zinc-900 dark:via-zinc-900 dark:to-primary/[0.06]">
      {/* ── Header con progress ── */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <ListChecks className="h-4 w-4 text-primary" />
          </div>
          <h3 className="text-sm font-bold tracking-tight">Configurazione cliente</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tabular-nums text-muted-foreground">
            {completed}/{total}
          </span>
          <div className="h-2 w-20 overflow-hidden rounded-full bg-muted sm:w-28">
            <div
              className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── Hero CTA — prossimo step ── */}
      {nextStep && (
        <div className="px-5 pb-4">
          <HeroCard step={nextStep} color={nextColor} />
        </div>
      )}

      {/* ── Steps numerati ── */}
      <div className="border-t bg-muted/20 px-5 py-3 dark:bg-muted/5">
        <div className="flex flex-wrap gap-x-1 gap-y-0.5 sm:flex-nowrap sm:gap-x-0">
          {steps.map((step, idx) => {
            const isNext = step === nextStep;
            return (
              <StepPill
                key={step.key}
                step={step}
                index={idx}
                isNext={isNext}
                color={STEP_COLORS[idx] ?? STEP_COLORS[0]}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

function HeroCardInner({ step, color }: { step: OnboardingStep; color: typeof STEP_COLORS[number] }) {
  return (
    <div className={`relative overflow-hidden rounded-xl border ${color.ring} ring-1 ring-inset ${color.heroBg} p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}>
      <div className="flex items-center gap-4">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${color.bg}`}>
          <step.icon className={`h-6 w-6 ${color.text}`} />
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Prossimo passo
          </p>
          <p className="text-base font-bold tracking-tight">{step.label}</p>
          <p className="text-xs text-muted-foreground">{step.description}</p>
        </div>
        {/* div styled come bottone — MAI <Button> qui: wrapper puo' essere <button> (onAction) */}
        <div className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-sm">
          {STEP_CTA[step.key] ?? "Inizia"}
          <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </div>
      </div>
    </div>
  );
}

function HeroCard({ step, color }: { step: OnboardingStep; color: typeof STEP_COLORS[number] }) {
  if (step.onAction) {
    return (
      <button type="button" onClick={step.onAction} className="group block w-full text-left">
        <HeroCardInner step={step} color={color} />
      </button>
    );
  }
  return (
    <Link href={step.href} className="group block">
      <HeroCardInner step={step} color={color} />
    </Link>
  );
}

function StepPill({
  step,
  index,
  isNext,
  color,
}: {
  step: OnboardingStep;
  index: number;
  isNext: boolean;
  color: typeof STEP_COLORS[number];
}) {
  const Icon = step.icon;

  if (step.completed) {
    return (
      <div className="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-muted-foreground/70">
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40">
          <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
        </div>
        <span className="text-xs line-through">{step.label}</span>
      </div>
    );
  }

  if (isNext) {
    return (
      <div className={`flex items-center gap-1.5 rounded-full ${color.bg} px-2.5 py-1.5`}>
        <div className={`flex h-5 w-5 items-center justify-center rounded-full bg-white dark:bg-zinc-800`}>
          <span className={`text-[10px] font-bold ${color.text}`}>{index + 1}</span>
        </div>
        <span className={`text-xs font-semibold ${color.text}`}>{step.label}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-muted-foreground/50">
      <div className="flex h-5 w-5 items-center justify-center rounded-full border border-dashed border-muted-foreground/20">
        <span className="text-[10px]">{index + 1}</span>
      </div>
      <span className="text-xs">{step.label}</span>
    </div>
  );
}
