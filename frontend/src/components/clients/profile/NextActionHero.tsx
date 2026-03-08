// src/components/clients/profile/NextActionHero.tsx
"use client";

/**
 * Card hero con la prossima azione suggerita per il cliente.
 *
 * Usa i dati clinical readiness per mostrare un CTA prominente
 * color-coded per priorita'. Se il profilo e' completo, mostra
 * un messaggio celebrativo verde.
 */

import Link from "next/link";
import { ArrowRight, CheckCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ClinicalReadinessClientItem } from "@/types/api";

interface NextActionHeroProps {
  readiness: ClinicalReadinessClientItem;
}

const PRIORITY_STYLES: Record<string, {
  border: string;
  bg: string;
  icon: string;
  badge: string;
}> = {
  high: {
    border: "border-l-red-500",
    bg: "bg-red-50 dark:bg-red-950/20",
    icon: "text-red-500",
    badge: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  },
  medium: {
    border: "border-l-amber-500",
    bg: "bg-amber-50 dark:bg-amber-950/20",
    icon: "text-amber-500",
    badge: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  },
  low: {
    border: "border-l-blue-500",
    bg: "bg-blue-50 dark:bg-blue-950/20",
    icon: "text-blue-500",
    badge: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  },
};

export function NextActionHero({ readiness }: NextActionHeroProps) {
  // Profilo completo — celebrazione
  if (readiness.next_action_code === "ready") {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-l-4 border-l-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 p-4">
        <CheckCircle className="h-5 w-5 shrink-0 text-emerald-500" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
            Profilo completo
          </p>
          <p className="text-xs text-emerald-600/80 dark:text-emerald-400/60">
            Anamnesi, misurazioni e scheda allenamento sono configurati
          </p>
        </div>
      </div>
    );
  }

  const style = PRIORITY_STYLES[readiness.priority] ?? PRIORITY_STYLES.low;

  return (
    <div className={`flex items-center gap-3 rounded-lg border border-l-4 ${style.border} ${style.bg} p-4`}>
      <Sparkles className={`h-5 w-5 shrink-0 ${style.icon}`} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">Prossimo passo</p>
        <p className="text-xs text-muted-foreground">
          {readiness.next_action_label}
        </p>
      </div>
      <Button asChild size="sm" variant="outline" className="shrink-0">
        <Link href={readiness.next_action_href}>
          Vai
          <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
        </Link>
      </Button>
    </div>
  );
}
