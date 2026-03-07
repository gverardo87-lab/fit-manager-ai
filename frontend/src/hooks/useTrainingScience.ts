// src/hooks/useTrainingScience.ts
/**
 * Hook per il Training Science Engine — motore scientifico backend.
 *
 * 5 hook che consumano i 5 endpoint REST computazionali puri (zero DB).
 * Tutti richiedono JWT auth. I dati sono deterministici e cacheable.
 *
 * Endpoint:
 *   POST /training-science/plan         -> genera piano settimanale
 *   POST /training-science/analyze      -> analisi 4D di un piano
 *   POST /training-science/mesocycle    -> genera mesociclo da piano base
 *   GET  /training-science/parameters   -> parametri carico per obiettivo
 *   GET  /training-science/volume-targets -> target volume per livello x obiettivo
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  TSObjective,
  TSLevel,
  TSTemplatePiano,
  TSAnalisiPiano,
  TSMesociclo,
  TSParametriCarico,
  TSPlanPackage,
  TSPlanPackageRequest,
  TSVolumeTarget,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// MUTATION: Genera piano settimanale volume-driven
// ════════════════════════════════════════════════════════════

export interface GeneratePlanInput {
  frequenza: number;
  obiettivo: TSObjective;
  livello: TSLevel;
}

export function useGenerateScientificPlan() {
  return useMutation<TSTemplatePiano, Error, GeneratePlanInput>({
    mutationFn: async (input) => {
      const { data } = await apiClient.post<TSTemplatePiano>(
        "/training-science/plan",
        input,
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella generazione del piano"));
    },
  });
}

export function useGeneratePlanPackage() {
  return useMutation<TSPlanPackage, Error, TSPlanPackageRequest>({
    mutationFn: async (input) => {
      const { data } = await apiClient.post<TSPlanPackage>(
        "/training-science/plan-package",
        input,
      );
      return data;
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella generazione del plan package"),
      );
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Analisi 4D di un piano esistente
// ════════════════════════════════════════════════════════════

export function useAnalyzePlan() {
  return useMutation<TSAnalisiPiano, Error, TSTemplatePiano>({
    mutationFn: async (piano) => {
      const { data } = await apiClient.post<TSAnalisiPiano>(
        "/training-science/analyze",
        { piano },
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'analisi del piano"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Genera mesociclo da piano base
// ════════════════════════════════════════════════════════════

export function useGenerateMesocycle() {
  return useMutation<TSMesociclo, Error, TSTemplatePiano>({
    mutationFn: async (pianoBase) => {
      const { data } = await apiClient.post<TSMesociclo>(
        "/training-science/mesocycle",
        { piano_base: pianoBase },
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella generazione del mesociclo"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Parametri di carico per obiettivo
// ════════════════════════════════════════════════════════════

export function useLoadParameters(obiettivo: TSObjective | null) {
  return useQuery<TSParametriCarico>({
    queryKey: ["training-science", "parameters", obiettivo],
    queryFn: async () => {
      const { data } = await apiClient.get<TSParametriCarico>(
        `/training-science/parameters/${obiettivo}`,
      );
      return data;
    },
    enabled: obiettivo !== null,
    staleTime: 5 * 60 * 1000, // 5 min — dati statici deterministici
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Volume targets per livello x obiettivo
// ════════════════════════════════════════════════════════════

export function useVolumeTargets(
  livello: TSLevel | null,
  obiettivo: TSObjective | null,
) {
  return useQuery<TSVolumeTarget[]>({
    queryKey: ["training-science", "volume-targets", livello, obiettivo],
    queryFn: async () => {
      const { data } = await apiClient.get<TSVolumeTarget[]>(
        "/training-science/volume-targets",
        { params: { livello, obiettivo } },
      );
      return data;
    },
    enabled: livello !== null && obiettivo !== null,
    staleTime: 5 * 60 * 1000, // 5 min — dati statici deterministici
  });
}
