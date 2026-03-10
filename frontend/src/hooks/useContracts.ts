// src/hooks/useContracts.ts
/**
 * Custom hooks per il modulo Contratti.
 *
 * Pattern identico a useClients: una funzione per operazione,
 * invalidation su ["contracts"] + ["dashboard"], toast su ogni mutation.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Contract,
  ContractCreate,
  ContractUpdate,
  ContractWithRates,
  ContractListResponse,
} from "@/types/api";

// ── Query: lista contratti (tutti, filtraggio client-side) ──

export function useContracts() {
  return useQuery<ContractListResponse>({
    queryKey: ["contracts"],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractListResponse>(
        "/contracts",
        { params: { page: 1, page_size: 200 } }
      );
      return data;
    },
  });
}

// ── Query: dettaglio contratto con rate (Master-Detail) ──

export function useContract(id: number | null) {
  return useQuery<ContractWithRates>({
    queryKey: ["contract", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractWithRates>(
        `/contracts/${id}`
      );
      return data;
    },
    enabled: id !== null,
  });
}

// ── Query: contratti di un singolo cliente (profilo) ──

export function useClientContracts(idCliente: number | null) {
  return useQuery<ContractListResponse>({
    queryKey: ["contracts", { idCliente }],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractListResponse>(
        "/contracts",
        { params: { page: 1, page_size: 100, id_cliente: idCliente } }
      );
      return data;
    },
    enabled: idCliente !== null,
  });
}

// ── Mutation: crea contratto ──

export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ContractCreate) => {
      const { data } = await apiClient.post<Contract>("/contracts", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success("Contratto creato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione del contratto"));
    },
  });
}

// ── Mutation: aggiorna contratto ──

export function useUpdateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: ContractUpdate & { id: number }) => {
      const { data } = await apiClient.put<Contract>(
        `/contracts/${id}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Contratto aggiornato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento del contratto"));
    },
  });
}

// ── Mutation: rinnova contratto ──

export function useRenewContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      ...payload
    }: ContractCreate & { contractId: number }) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/renew`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
      toast.success("Contratto rinnovato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel rinnovo del contratto"));
    },
  });
}

// ── Mutation: elimina contratto ──

export function useDeleteContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, force, keepPayments }: { id: number; force?: boolean; keepPayments?: boolean }) => {
      const params = new URLSearchParams();
      if (force) params.set("force", "true");
      if (keepPayments) params.set("keep_payments", "true");
      const qs = params.toString();
      await apiClient.delete(`/contracts/${id}${qs ? `?${qs}` : ""}`);
    },
    onSuccess: (_data, { force }) => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success(force ? "Contratto eliminato forzatamente" : "Contratto eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del contratto"));
    },
  });
}
