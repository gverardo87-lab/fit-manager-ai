// src/hooks/useNutritionTemplates.ts
/**
 * Custom hooks per i template di pasto.
 *
 * Query keys:
 *   ["meal-templates"]  — lista template del trainer
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type { MealTemplate } from "@/types/api";

export function useMealTemplates() {
  return useQuery<MealTemplate[]>({
    queryKey: ["meal-templates"],
    queryFn: async () => {
      const { data } = await apiClient.get<MealTemplate[]>("/nutrition/meal-templates");
      return data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useDeleteMealTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (templateId: number) => {
      await apiClient.delete(`/nutrition/meal-templates/${templateId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meal-templates"] });
      toast.success("Template eliminato");
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore eliminazione template")),
  });
}

export function useSaveAsTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId, mealId, nome, tipo_pasto,
    }: { planId: number; mealId: number; nome: string; tipo_pasto?: string }) => {
      const { data } = await apiClient.post<MealTemplate>(
        `/nutrition/plans/${planId}/meals/${mealId}/save-as-template`,
        { nome, tipo_pasto }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meal-templates"] });
      toast.success("Template salvato");
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore salvataggio template")),
  });
}

export function useApplyTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId, mealId, templateId,
    }: { planId: number; mealId: number; templateId: number }) => {
      const { data } = await apiClient.post<{ componenti_aggiunti: number }>(
        `/nutrition/plans/${planId}/meals/${mealId}/apply-template/${templateId}`,
        {}
      );
      return data;
    },
    onSuccess: (data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
      const n = data.componenti_aggiunti;
      toast.success(`${n} aliment${n === 1 ? "o" : "i"} aggiunti dal template`);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore applicazione template")),
  });
}
