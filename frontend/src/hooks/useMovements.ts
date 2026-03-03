// src/hooks/useMovements.ts
/**
 * Custom hooks per le operazioni sui Movimenti di Cassa.
 *
 * - useMovements(anno, mese, tipo): lista paginata con filtri server-side
 * - useCreateMovement(): inserisce movimento manuale
 * - useDeleteMovement(): elimina movimento (solo manuali — Ledger Integrity)
 * - useCashBalance(): saldo di cassa attuale (computed on read)
 * - useUpdateSaldoIniziale(): configura saldo iniziale
 *
 * Ogni mutation invalida ["movements"], ["dashboard"], e ["cash-balance"].
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  CashMovement,
  MovementManualCreate,
  MovementStats,
  MovementsPaginatedResponse,
  ImpactPreviewResponse,
  CashAuditTimelineResponse,
  PendingExpensesResponse,
  ForecastResponse,
  BalanceResponse,
  SaldoInizialeUpdate,
  SaldoInizialeResponse,
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

interface UseCashAuditLogParams {
  data_da?: string;
  data_a?: string;
  action?: string;
  entity_type?: string;
  flow?: "ENTRATA" | "USCITA";
  limit?: number;
  offset?: number;
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
  return useQuery<MovementsPaginatedResponse>({
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

      const { data } = await apiClient.get<MovementsPaginatedResponse>(
        `/movements?${params.toString()}`
      );
      return data;
    },
  });
}

// ── Query: statistiche mensili (KPI + chart + saldi mese) ──

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

// ── Query: saldo di cassa attuale ──

export function useCashBalance() {
  return useQuery<BalanceResponse>({
    queryKey: ["cash-balance"],
    queryFn: async () => {
      const { data } = await apiClient.get<BalanceResponse>("/movements/balance");
      return data;
    },
  });
}

// ── Query: configurazione saldo iniziale ──

export function useSaldoIniziale() {
  return useQuery<SaldoInizialeResponse>({
    queryKey: ["saldo-iniziale"],
    queryFn: async () => {
      const { data } = await apiClient.get<SaldoInizialeResponse>("/movements/saldo-iniziale");
      return data;
    },
  });
}

// ── Mutation: aggiorna saldo iniziale ──

export function useUpdateSaldoIniziale() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: SaldoInizialeUpdate) => {
      const { data } = await apiClient.put<SaldoInizialeResponse>(
        "/movements/saldo-iniziale",
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saldo-iniziale"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["forecast"] });
      toast.success("Saldo iniziale aggiornato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento del saldo iniziale"));
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
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success("Movimento registrato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella registrazione del movimento"));
    },
  });
}

// ── Mutation: elimina movimento (solo manuali) ──

export function usePreviewCreateMovement() {
  return useMutation({
    mutationFn: async (payload: MovementManualCreate) => {
      const { data } = await apiClient.post<ImpactPreviewResponse>(
        "/movements/impact-preview/manual-create",
        payload
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel calcolo anteprima movimento"));
    },
  });
}

export function useCashAuditLog(
  {
    data_da,
    data_a,
    action,
    entity_type,
    flow,
    limit = 80,
    offset = 0,
  }: UseCashAuditLogParams = {},
  enabled: boolean = true
) {
  return useQuery<CashAuditTimelineResponse>({
    queryKey: ["cash-audit-log", { data_da, data_a, action, entity_type, flow, limit, offset }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (data_da) params.set("data_da", data_da);
      if (data_a) params.set("data_a", data_a);
      if (action) params.set("action", action);
      if (entity_type) params.set("entity_type", entity_type);
      if (flow) params.set("flow", flow);
      params.set("limit", String(limit));
      params.set("offset", String(offset));

      const { data } = await apiClient.get<CashAuditTimelineResponse>(
        `/movements/audit-log?${params.toString()}`
      );
      return data;
    },
    enabled,
  });
}

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
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success("Movimento eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del movimento"));
    },
  });
}

// ── Query: spese ricorrenti in attesa di conferma ──

export function usePreviewDeleteMovement() {
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await apiClient.post<ImpactPreviewResponse>(
        `/movements/impact-preview/delete/${id}`
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel calcolo anteprima eliminazione"));
    },
  });
}

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
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success(`${result.created} ${result.created === 1 ? "spesa registrata" : "spese registrate"}`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella conferma delle spese"));
    },
  });
}

// ── Query: forecast proiezione finanziaria ──

export function usePreviewConfirmExpenses() {
  return useMutation({
    mutationFn: async (items: { id_spesa: number; mese_anno_key: string }[]) => {
      const { data } = await apiClient.post<ImpactPreviewResponse>(
        "/movements/impact-preview/confirm-expenses",
        { items }
      );
      return data;
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel calcolo anteprima spese"));
    },
  });
}

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
