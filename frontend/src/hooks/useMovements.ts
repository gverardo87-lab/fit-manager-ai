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
import apiClient from "@/lib/api-client";
import type {
  CashMovement,
  MovementManualCreate,
  MovementStats,
  PaginatedResponse,
} from "@/types/api";

// ── Query: lista movimenti filtrata ──

interface UseMovementsParams {
  anno?: number;
  mese?: number;
  tipo?: string;
  page?: number;
  pageSize?: number;
}

export function useMovements({
  anno,
  mese,
  tipo,
  page = 1,
  pageSize = 100,
}: UseMovementsParams = {}) {
  return useQuery<PaginatedResponse<CashMovement>>({
    queryKey: ["movements", { anno, mese, tipo, page, pageSize }],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      if (anno) params.set("anno", String(anno));
      if (mese) params.set("mese", String(mese));
      if (tipo) params.set("tipo", tipo);

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
    onError: () => {
      toast.error("Errore nella registrazione del movimento");
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
    onError: () => {
      toast.error("Errore nell'eliminazione del movimento");
    },
  });
}
