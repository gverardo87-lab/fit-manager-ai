// src/hooks/useMeasurements.ts
/**
 * Custom hooks per il modulo Misurazioni Corporee.
 *
 * Pattern: useQuery per lettura, useMutation per scrittura.
 * Ogni mutation invalida ["measurements", clientId] + toast.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Metric,
  Measurement,
  MeasurementCreate,
  MeasurementUpdate,
  MeasurementListResponse,
} from "@/types/api";

// ── Query: catalogo metriche (globale, raramente cambia) ──

export function useMetrics() {
  return useQuery<Metric[]>({
    queryKey: ["metrics"],
    queryFn: async () => {
      const { data } = await apiClient.get<Metric[]>("/metrics");
      return data;
    },
    staleTime: 1000 * 60 * 30, // 30 min — catalogo statico
  });
}

// ── Query: lista misurazioni per cliente ──

export function useClientMeasurements(clientId: number | null) {
  return useQuery<MeasurementListResponse>({
    queryKey: ["measurements", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<MeasurementListResponse>(
        `/clients/${clientId}/measurements`
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

// ── Query: ultima misurazione per KPI/preview ──

export function useLatestMeasurement(clientId: number | null) {
  return useQuery<Measurement | null>({
    queryKey: ["measurements", clientId, "latest"],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get<Measurement>(
          `/clients/${clientId}/measurements/latest`
        );
        return data;
      } catch {
        // 404 = nessuna misurazione — non e' un errore
        return null;
      }
    },
    enabled: clientId !== null,
  });
}

// ── Mutation: crea sessione di misurazione ──

export function useCreateMeasurement(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: MeasurementCreate) => {
      const { data } = await apiClient.post<Measurement>(
        `/clients/${clientId}/measurements`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["measurements", clientId] });
      toast.success("Misurazione registrata");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nel salvataggio della misurazione")
      );
    },
  });
}

// ── Mutation: aggiorna sessione di misurazione ──

export function useUpdateMeasurement(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      measurementId,
      payload,
    }: {
      measurementId: number;
      payload: MeasurementUpdate;
    }) => {
      const { data } = await apiClient.put<Measurement>(
        `/clients/${clientId}/measurements/${measurementId}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["measurements", clientId] });
      toast.success("Misurazione aggiornata");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nell'aggiornamento della misurazione")
      );
    },
  });
}

// ── Mutation: elimina sessione di misurazione ──

export function useDeleteMeasurement(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (measurementId: number) => {
      await apiClient.delete(
        `/clients/${clientId}/measurements/${measurementId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["measurements", clientId] });
      toast.success("Misurazione eliminata");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nell'eliminazione della misurazione")
      );
    },
  });
}
