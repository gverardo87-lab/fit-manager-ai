// src/components/clients/profile/OnboardingChecklist.tsx
"use client";

/**
 * Checklist onboarding cliente — stepper visuale 5 step.
 *
 * Mostra solo se almeno 1 step e' incompleto. Progress bar in alto.
 * Ogni step completato = verde con check. Incompleto = link cliccabile.
 * Si nasconde quando il profilo e' completo.
 */

import Link from "next/link";
import { Check, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { OnboardingStep } from "@/hooks/useClientReadiness";

interface OnboardingChecklistProps {
  steps: OnboardingStep[];
}

export function OnboardingChecklist({ steps }: OnboardingChecklistProps) {
  const completed = steps.filter((s) => s.completed).length;
  const total = steps.length;
  const allDone = completed === total;

  // Non renderizzare se tutto completato
  if (allDone) return null;

  const pct = Math.round((completed / total) * 100);

  return (
    <Card className="border-l-4 border-l-primary/60 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">
            Configura il profilo
          </CardTitle>
          <span className="text-xs font-medium text-muted-foreground tabular-nums">
            {completed}/{total} completati
          </span>
        </div>
        {/* Progress bar */}
        <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-1">
          {steps.map((step) => (
            <StepRow key={step.key} step={step} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function StepRow({ step }: { step: OnboardingStep }) {
  const Icon = step.icon;

  if (step.completed) {
    return (
      <div className="flex items-center gap-3 rounded-lg px-2 py-2 text-muted-foreground">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
          <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm line-through">{step.label}</p>
        </div>
      </div>
    );
  }

  return (
    <Link
      href={step.href}
      className="group flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted/50"
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/30 group-hover:border-primary/50">
        <Icon className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{step.label}</p>
        <p className="text-xs text-muted-foreground">{step.description}</p>
      </div>
      <ChevronRight className="h-4 w-4 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
    </Link>
  );
}
