// src/hooks/useMovements.ts
/**
 * Custom hooks per le operazioni sui Movimenti di Cassa.
 *
 * - useMovements(anno, mese, tipo): lista paginata con filtri server-side
 * - useCreateMovement(): inserisce movimento manuale
 * - useDeleteMovement(): elimina movimento (solo manuali — Ledger Integrity)
 *
 * Ogni mutation invalida ["movements"] e ["dashboard"].
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  CashMovement,
  MovementManualCreate,
  MovementStats,
  PaginatedResponse,
  PendingExpensesResponse,
  ForecastResponse,
} from "@/types/api";

// ── Query: lista movimenti filtrata ──

interface UseMovementsParams {
  anno?: number;
  mese?: number;
  tipo?: string;
  data_da?: string;
  data_a?: string;
  id_cliente?: number;
  page?: number;
  pageSize?: number;
}

export function useMovements({
  anno,
  mese,
  tipo,
  data_da,
  data_a,
  id_cliente,
  page = 1,
  pageSize = 100,
}: UseMovementsParams = {}) {
  return useQuery<PaginatedResponse<CashMovement>>({
    queryKey: ["movements", { anno, mese, tipo, data_da, data_a, id_cliente, page, pageSize }],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      if (data_da) params.set("data_da", data_da);
      if (data_a) params.set("data_a", data_a);
      if (!data_da && !data_a) {
        if (anno) params.set("anno", String(anno));
        if (mese) params.set("mese", String(mese));
      }
      if (tipo) params.set("tipo", tipo);
      if (id_cliente) params.set("id_cliente", String(id_cliente));

      const { data } = await apiClient.get<PaginatedResponse<CashMovement>>(
        `/movements?${params.toString()}`
      );
      return data;
    },
  });
}

// ── Query: statistiche mensili (KPI + chart) ──

export function useMovementStats(anno: number, mese: number) {
  return useQuery<MovementStats>({
    queryKey: ["movement-stats", { anno, mese }],
    queryFn: async () => {
      const { data } = await apiClient.get<MovementStats>(
        `/movements/stats?anno=${anno}&mese=${mese}`
      );
      return data;
    },
  });
}

// ── Mutation: crea movimento manuale ──

export function useCreateMovement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: MovementManualCreate) => {
      const { data } = await apiClient.post<CashMovement>(
        "/movements",
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Movimento registrato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella registrazione del movimento"));
    },
  });
}

// ── Mutation: elimina movimento (solo manuali) ──

export function useDeleteMovement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/movements/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Movimento eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del movimento"));
    },
  });
}

// ── Query: spese ricorrenti in attesa di conferma ──

export function usePendingExpenses(anno: number, mese: number) {
  return useQuery<PendingExpensesResponse>({
    queryKey: ["pending-expenses", { anno, mese }],
    queryFn: async () => {
      const { data } = await apiClient.get<PendingExpensesResponse>(
        `/movements/pending-expenses?anno=${anno}&mese=${mese}`
      );
      return data;
    },
  });
}

// ── Mutation: conferma spese ricorrenti selezionate ──

export function useConfirmExpenses() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (items: { id_spesa: number; mese_anno_key: string }[]) => {
      const { data } = await apiClient.post("/movements/confirm-expenses", { items });
      return data as { created: number; totale: number };
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["pending-expenses"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`${result.created} ${result.created === 1 ? "spesa registrata" : "spese registrate"}`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella conferma delle spese"));
    },
  });
}

// ── Query: forecast proiezione finanziaria ──

export function useForecast(mesi: number = 3) {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", { mesi }],
    queryFn: async () => {
      const { data } = await apiClient.get<ForecastResponse>(
        `/movements/forecast?mesi=${mesi}`
      );
      return data;
    },
  });
}
