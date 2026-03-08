// src/hooks/useClientReadiness.ts
/**
 * Hook per readiness clinica di un singolo cliente.
 *
 * Wrappa useClinicalReadiness() (cache condivisa, refetch 60s) ed estrae
 * il record del cliente via .find(). Zero API call aggiuntive.
 *
 * Esporta anche computeOnboardingSteps() per calcolare la checklist
 * di onboarding basata su dati reali.
 */

import { useMemo } from "react";
import {
  HeartPulse,
  Ruler,
  Dumbbell,
  Calendar,
  FileText,
  type LucideIcon,
} from "lucide-react";
import { useClinicalReadiness } from "./useDashboard";
import type { ClinicalReadinessClientItem } from "@/types/api";

export interface OnboardingStep {
  key: string;
  label: string;
  description: string;
  completed: boolean;
  href: string;
  icon: LucideIcon;
}

interface OnboardingContext {
  hasContracts: boolean;
  hasEvents: boolean;
}

/** Calcola la checklist onboarding da dati reali. */
export function computeOnboardingSteps(
  clientId: number,
  readiness: ClinicalReadinessClientItem | null,
  ctx: OnboardingContext,
): OnboardingStep[] {
  const anamnesiDone = readiness?.anamnesi_state === "structured";
  const measurementsDone = readiness?.has_measurements ?? false;
  const workoutDone = readiness?.has_workout_plan ?? false;

  return [
    {
      key: "anamnesi",
      label: "Anamnesi",
      description: "Questionario clinico e stile di vita",
      completed: anamnesiDone,
      href: `/clienti/${clientId}/anamnesi`,
      icon: HeartPulse,
    },
    {
      key: "misurazioni",
      label: "Misurazioni base",
      description: "Peso, composizione corporea, circonferenze",
      completed: measurementsDone,
      href: `/clienti/${clientId}/misurazioni`,
      icon: Ruler,
    },
    {
      key: "scheda",
      label: "Scheda allenamento",
      description: "Programma personalizzato",
      completed: workoutDone,
      href: `/clienti/${clientId}?tab=schede&startScheda=1`,
      icon: Dumbbell,
    },
    {
      key: "sessione",
      label: "Prima sessione",
      description: "Prenota in agenda",
      completed: ctx.hasEvents,
      href: `/agenda?newEvent=1&clientId=${clientId}`,
      icon: Calendar,
    },
    {
      key: "contratto",
      label: "Contratto",
      description: "Pacchetto e piano pagamento",
      completed: ctx.hasContracts,
      href: `/contratti?new=1&cliente=${clientId}`,
      icon: FileText,
    },
  ];
}

/** Hook: readiness di un singolo cliente dalla cache condivisa. */
export function useClientReadiness(clientId: number) {
  const { data, isLoading } = useClinicalReadiness();

  const readiness = useMemo(() => {
    if (!data?.items) return null;
    return data.items.find((i) => i.client_id === clientId) ?? null;
  }, [data, clientId]);

  return { readiness, isLoading };
}
