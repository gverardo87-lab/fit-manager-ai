// src/hooks/useRecurringExpenses.ts
/**
 * Custom hooks per le Spese Ricorrenti.
 *
 * - useRecurringExpenses(): lista spese fisse del trainer
 * - useCreateRecurringExpense(): crea nuova spesa fissa
 * - useUpdateRecurringExpense(): aggiorna (toggle attiva, modifica importo)
 * - useDeleteRecurringExpense(): elimina spesa fissa
 *
 * Ogni mutation invalida ["recurring-expenses"] e ["movement-stats"].
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  RecurringExpense,
  RecurringExpenseCreate,
  RecurringExpenseUpdate,
  ListResponse,
} from "@/types/api";

// ── Query: lista spese ricorrenti ──

export function useRecurringExpenses() {
  return useQuery<ListResponse<RecurringExpense>>({
    queryKey: ["recurring-expenses"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<RecurringExpense>>(
        "/recurring-expenses"
      );
      return data;
    },
  });
}

// ── Mutation: crea spesa ricorrente ──

export function useCreateRecurringExpense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RecurringExpenseCreate) => {
      const { data } = await apiClient.post<RecurringExpense>(
        "/recurring-expenses",
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring-expenses"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      toast.success("Spesa ricorrente creata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione della spesa ricorrente"));
    },
  });
}

// ── Mutation: aggiorna spesa ricorrente ──

export function useUpdateRecurringExpense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: RecurringExpenseUpdate & { id: number }) => {
      const { data } = await apiClient.put<RecurringExpense>(
        `/recurring-expenses/${id}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring-expenses"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      toast.success("Spesa ricorrente aggiornata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento della spesa ricorrente"));
    },
  });
}

// ── Mutation: elimina spesa ricorrente ──

export function useDeleteRecurringExpense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/recurring-expenses/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring-expenses"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      toast.success("Spesa ricorrente eliminata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione della spesa ricorrente"));
    },
  });
}
