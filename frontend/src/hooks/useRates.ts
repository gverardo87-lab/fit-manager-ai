// src/hooks/useRates.ts
/**
 * Custom hooks per le operazioni sulle Rate.
 *
 * Ogni mutation invalida:
 * - ["contract", contractId] → aggiorna il dettaglio con rate
 * - ["contracts"] → aggiorna la lista contratti (stato_pagamento puo' cambiare)
 * - ["dashboard"] → le rate pendenti e revenue cambiano
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "@/lib/api-client";
import type {
  Rate,
  RateCreate,
  RateUpdate,
  PaymentPlanCreate,
  RatePayment,
  ListResponse,
} from "@/types/api";

// ── Mutation: genera piano rate automatico ──

export function useGeneratePaymentPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      ...payload
    }: PaymentPlanCreate & { contractId: number }) => {
      const { data } = await apiClient.post<ListResponse<Rate>>(
        `/rates/generate-plan/${contractId}`,
        payload
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Piano generato: ${data.total} rate create`);
    },
    onError: () => {
      toast.error("Errore nella generazione del piano rate");
    },
  });
}

// ── Mutation: crea rata manuale ──

export function useCreateRate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RateCreate) => {
      const { data } = await apiClient.post<Rate>("/rates", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Rata aggiunta");
    },
    onError: () => {
      toast.error("Errore nella creazione della rata");
    },
  });
}

// ── Mutation: aggiorna rata ──

export function useUpdateRate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      rateId,
      ...payload
    }: RateUpdate & { rateId: number }) => {
      const { data } = await apiClient.put<Rate>(`/rates/${rateId}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Rata aggiornata");
    },
    onError: () => {
      toast.error("Errore nell'aggiornamento della rata");
    },
  });
}

// ── Mutation: elimina rata ──

export function useDeleteRate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (rateId: number) => {
      await apiClient.delete(`/rates/${rateId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Rata eliminata");
    },
    onError: () => {
      toast.error("Errore nell'eliminazione della rata");
    },
  });
}

// ── Mutation: pagamento rata (atomico) ──

export function usePayRate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      rateId,
      ...payload
    }: RatePayment & { rateId: number }) => {
      const { data } = await apiClient.post<Rate>(
        `/rates/${rateId}/pay`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Pagamento registrato");
    },
    onError: () => {
      toast.error("Errore nel pagamento della rata");
    },
  });
}
