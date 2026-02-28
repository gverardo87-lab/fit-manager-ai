// src/hooks/useGoals.ts
/**
 * Custom hooks per il modulo Obiettivi Cliente.
 *
 * Pattern: useQuery per lettura, useMutation per scrittura.
 * Ogni mutation invalida ["goals", clientId] + toast.
 *
 * Cross-invalidation: le mutation di misurazioni invalidano anche
 * ["goals", clientId] perche' il progresso dipende dalle misurazioni.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  ClientGoal,
  GoalCreate,
  GoalUpdate,
  GoalListResponse,
} from "@/types/api";

// ── Query: lista obiettivi per cliente (con progresso) ──

export function useClientGoals(clientId: number | null) {
  return useQuery<GoalListResponse>({
    queryKey: ["goals", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<GoalListResponse>(
        `/clients/${clientId}/goals`
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

// ── Mutation: crea obiettivo ──

export function useCreateGoal(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: GoalCreate) => {
      const { data } = await apiClient.post<ClientGoal>(
        `/clients/${clientId}/goals`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", clientId] });
      queryClient.invalidateQueries({ queryKey: ["client", clientId] });
      toast.success("Obiettivo creato");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella creazione dell'obiettivo")
      );
    },
  });
}

// ── Mutation: aggiorna obiettivo ──

export function useUpdateGoal(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      goalId,
      payload,
    }: {
      goalId: number;
      payload: GoalUpdate;
    }) => {
      const { data } = await apiClient.put<ClientGoal>(
        `/clients/${clientId}/goals/${goalId}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", clientId] });
      toast.success("Obiettivo aggiornato");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nell'aggiornamento dell'obiettivo")
      );
    },
  });
}

// ── Mutation: elimina obiettivo ──

export function useDeleteGoal(clientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (goalId: number) => {
      await apiClient.delete(
        `/clients/${clientId}/goals/${goalId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals", clientId] });
      toast.success("Obiettivo eliminato");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nell'eliminazione dell'obiettivo")
      );
    },
  });
}
