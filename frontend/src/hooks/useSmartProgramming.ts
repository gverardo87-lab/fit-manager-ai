// src/hooks/useSmartProgramming.ts
/**
 * Hook aggregatore per il motore di Programmazione SMART.
 *
 * Raccoglie dati client (safety, misurazioni, goals, anamnesi, simmetria)
 * e costruisce un ClientProfile per il core engine.
 *
 * Pattern: composizione di hook esistenti (zero nuove API).
 */

import { useMemo } from "react";
import { useClient } from "@/hooks/useClients";
import { useExerciseSafetyMap } from "@/hooks/useExercises";
import { useLatestMeasurement, useClientMeasurements } from "@/hooks/useMeasurements";
import { useClientGoals } from "@/hooks/useGoals";
import { computeAllDerived, getLatestValue } from "@/lib/derived-metrics";
import { generateClinicalReport } from "@/lib/clinical-analysis";
import { buildClientProfile } from "@/lib/smart-programming";
import type { ClientProfile } from "@/lib/smart-programming";

export function useSmartProgramming(clientId: number | null) {
  const { data: client, isLoading: clientLoading } = useClient(clientId);
  const { data: safetyData, isLoading: safetyLoading } = useExerciseSafetyMap(clientId);
  const { data: latestMeasurement, isLoading: measurementLoading } = useLatestMeasurement(clientId);
  const { data: measurementsData, isLoading: measListLoading } = useClientMeasurements(clientId);
  const { data: goalsData, isLoading: goalsLoading } = useClientGoals(clientId);

  const profile = useMemo<ClientProfile | null>(() => {
    if (!client) return null;

    const safetyMap = safetyData?.entries ?? null;
    const measurements = measurementsData?.items ?? [];
    const goals = goalsData?.items ?? [];

    // Strength ratios da metriche derivate
    const derived = measurements.length > 0
      ? computeAllDerived(measurements, client.sesso)
      : null;
    const strengthRatios = derived?.strengthRatios ?? [];

    // Simmetria bilaterale dal report clinico
    const clinicalReport = measurements.length > 0
      ? generateClinicalReport(measurements, client.sesso, client.data_nascita, goals)
      : null;
    const symmetryDeficits = clinicalReport?.symmetry.filter(s =>
      s.severity === "warning" || s.severity === "alert"
    ) ?? [];

    const profile = buildClientProfile(
      client,
      safetyMap,
      strengthRatios,
      goals,
      symmetryDeficits,
    );

    // Arricchisci measurements nel profilo
    if (profile && latestMeasurement) {
      const peso = getLatestValue([latestMeasurement], 1);     // ID.PESO
      const altezza = getLatestValue([latestMeasurement], 2);   // ID.ALTEZZA
      const grassoPct = getLatestValue([latestMeasurement], 3); // ID.GRASSO_PCT
      profile.measurements = { peso, altezza, grassoPct };
    }

    return profile;
  }, [client, safetyData, latestMeasurement, measurementsData, goalsData]);

  const isLoading = clientLoading || safetyLoading || measurementLoading || measListLoading || goalsLoading;

  return { profile, isLoading };
}
