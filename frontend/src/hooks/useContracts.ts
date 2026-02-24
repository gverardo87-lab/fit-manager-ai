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
  ContractListItem,
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
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
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
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Contratto aggiornato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento del contratto"));
    },
  });
}

// ── Mutation: elimina contratto ──

export function useDeleteContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/contracts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Contratto eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del contratto"));
    },
  });
}
