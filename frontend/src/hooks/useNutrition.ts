// src/hooks/useNutrition.ts
/**
 * Custom hooks per il modulo Nutrizione.
 *
 * Query keys:
 *   ["nutrition-summary", clientId]           — snapshot nutrizionale cliente
 *   ["nutrition-plans", clientId]              — lista piani alimentari
 *   ["nutrition-plan", planId]                 — dettaglio piano con pasti e componenti
 *   ["nutrition-foods"]                        — catalogo alimenti (search)
 *   ["nutrition-categories"]                   — categorie alimentari
 *   ["nutrition-food", foodId]                 — dettaglio alimento
 *
 * Pattern: stessa struttura degli altri hook (useGoals, useMeasurements).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  FoodCategory,
  Food,
  FoodDetail,
  NutritionPlan,
  NutritionPlanCreate,
  NutritionPlanUpdate,
  NutritionPlanDetail,
  NutritionSummary,
  PlanMealDetail,
} from "@/types/api";

// ── Catalogo (read-only) ─────────────────────────────────────────────────

export function useNutritionCategories() {
  return useQuery<FoodCategory[]>({
    queryKey: ["nutrition-categories"],
    queryFn: async () => {
      const { data } = await apiClient.get<FoodCategory[]>("/nutrition/categories");
      return data;
    },
    staleTime: 5 * 60 * 1000, // categorie stabili — 5 min
  });
}

export function useFoods(q?: string, categoriaId?: number) {
  return useQuery<Food[]>({
    queryKey: ["nutrition-foods", { q, categoriaId }],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: "50" });
      if (q && q.length >= 2) params.set("q", q);
      if (categoriaId != null) params.set("categoria_id", String(categoriaId));
      const { data } = await apiClient.get<Food[]>(`/nutrition/foods?${params}`);
      return data;
    },
    enabled: !q || q.length >= 2,
    staleTime: 2 * 60 * 1000,
  });
}

export function useFoodDetail(foodId: number | null) {
  return useQuery<FoodDetail>({
    queryKey: ["nutrition-food", foodId],
    queryFn: async () => {
      const { data } = await apiClient.get<FoodDetail>(`/nutrition/foods/${foodId}`);
      return data;
    },
    enabled: foodId !== null,
  });
}

// ── Lista piani cross-client ──────────────────────────────────────────────

export function useAllNutritionPlans(attivo?: boolean) {
  return useQuery<NutritionPlan[]>({
    queryKey: ["nutrition-plans-all", { attivo }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (attivo !== undefined) params.set("attivo", String(attivo));
      const { data } = await apiClient.get<NutritionPlan[]>(
        `/nutrition/plans${params.toString() ? `?${params}` : ""}`
      );
      return data;
    },
  });
}

// ── Summary cliente ───────────────────────────────────────────────────────

export function useNutritionSummary(clientId: number | null) {
  return useQuery<NutritionSummary>({
    queryKey: ["nutrition-summary", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<NutritionSummary>(
        `/clients/${clientId}/nutrition/summary`
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

// ── Lista piani ──────────────────────────────────────────────────────────

export function useNutritionPlans(clientId: number | null) {
  return useQuery<NutritionPlan[]>({
    queryKey: ["nutrition-plans", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<NutritionPlan[]>(
        `/clients/${clientId}/nutrition/plans`
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

// ── Dettaglio piano per id diretto (senza clientId) ──────────────────────

export function useNutritionPlanById(planId: number | null) {
  return useQuery<NutritionPlanDetail>({
    queryKey: ["nutrition-plan", planId],
    queryFn: async () => {
      const { data } = await apiClient.get<NutritionPlanDetail>(
        `/nutrition/plans/${planId}`
      );
      return data;
    },
    enabled: planId !== null,
  });
}

// ── Dettaglio piano (con pasti e componenti) ──────────────────────────────

export function useNutritionPlan(clientId: number | null, planId: number | null) {
  return useQuery<NutritionPlanDetail>({
    queryKey: ["nutrition-plan", planId],
    queryFn: async () => {
      const { data } = await apiClient.get<NutritionPlanDetail>(
        `/clients/${clientId}/nutrition/plans/${planId}`
      );
      return data;
    },
    enabled: clientId !== null && planId !== null,
  });
}

// ── Mutation: crea piano ──────────────────────────────────────────────────

export function useCreateNutritionPlan(clientId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<NutritionPlanCreate, "id_cliente">) => {
      const { data } = await apiClient.post<NutritionPlan>(
        `/clients/${clientId}/nutrition/plans`,
        { ...payload, id_cliente: clientId }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plans", clientId] });
      queryClient.invalidateQueries({ queryKey: ["nutrition-summary", clientId] });
      toast.success("Piano alimentare creato");
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore creazione piano")),
  });
}

// ── Mutation: aggiorna piano ──────────────────────────────────────────────

export function useUpdateNutritionPlan(clientId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ planId, payload }: { planId: number; payload: NutritionPlanUpdate }) => {
      const { data } = await apiClient.put<NutritionPlan>(
        `/clients/${clientId}/nutrition/plans/${planId}`,
        payload
      );
      return data;
    },
    onSuccess: (_data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plans", clientId] });
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
      queryClient.invalidateQueries({ queryKey: ["nutrition-summary", clientId] });
      toast.success("Piano aggiornato");
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore aggiornamento piano")),
  });
}

// ── Mutation: elimina piano ───────────────────────────────────────────────

export function useDeleteNutritionPlan(clientId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: number) => {
      await apiClient.delete(`/clients/${clientId}/nutrition/plans/${planId}`);
    },
    onSuccess: (_data, planId) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plans", clientId] });
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
      queryClient.invalidateQueries({ queryKey: ["nutrition-summary", clientId] });
      toast.success("Piano eliminato");
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore eliminazione piano")),
  });
}

// ── Mutation: aggiungi pasto ──────────────────────────────────────────────

export function useAddMeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId,
      payload,
    }: {
      planId: number;
      payload: { giorno_settimana: number; tipo_pasto: string; ordine?: number; nome?: string; note?: string };
    }) => {
      const { data } = await apiClient.post<PlanMealDetail>(
        `/nutrition/plans/${planId}/meals`,
        payload
      );
      return data;
    },
    onSuccess: (_data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore aggiunta pasto")),
  });
}

// ── Mutation: elimina pasto ───────────────────────────────────────────────

export function useDeleteMeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ planId, mealId }: { planId: number; mealId: number }) => {
      await apiClient.delete(`/nutrition/plans/${planId}/meals/${mealId}`);
    },
    onSuccess: (_data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore eliminazione pasto")),
  });
}

// ── Mutation: aggiungi alimento al pasto ──────────────────────────────────

export function useAddComponent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId,
      mealId,
      alimento_id,
      quantita_g,
      note,
    }: {
      planId: number;
      mealId: number;
      alimento_id: number;
      quantita_g: number;
      note?: string;
    }) => {
      const { data } = await apiClient.post(
        `/nutrition/plans/${planId}/meals/${mealId}/components`,
        { alimento_id, quantita_g, note }
      );
      return data;
    },
    onSuccess: (_data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore aggiunta alimento")),
  });
}

// ── Mutation: rimuovi alimento dal pasto ──────────────────────────────────

export function useDeleteComponent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId,
      mealId,
      compId,
    }: {
      planId: number;
      mealId: number;
      compId: number;
    }) => {
      await apiClient.delete(
        `/nutrition/plans/${planId}/meals/${mealId}/components/${compId}`
      );
    },
    onSuccess: (_data, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ["nutrition-plan", planId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Errore rimozione alimento")),
  });
}
