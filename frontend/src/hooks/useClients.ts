// src/hooks/useClients.ts
/**
 * Custom hooks per il modulo Clienti.
 *
 * Pattern: una funzione per operazione, ognuna con la propria queryKey.
 * Le mutations invalidano ["clients"] su successo → la tabella si aggiorna
 * istantaneamente senza ricaricare la pagina.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import type {
  Client,
  ClientCreate,
  ClientUpdate,
  PaginatedResponse,
} from "@/types/api";

// ── Query: lista clienti (paginata, filtrabile) ──

interface UseClientsParams {
  page?: number;
  pageSize?: number;
  stato?: string;
  search?: string;
}

export function useClients(params: UseClientsParams = {}) {
  const { page = 1, pageSize = 50, stato, search } = params;

  return useQuery<PaginatedResponse<Client>>({
    queryKey: ["clients", { page, pageSize, stato, search }],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Client>>(
        "/clients",
        {
          params: {
            page,
            page_size: pageSize,
            stato: stato || undefined,
            search: search || undefined,
          },
        }
      );
      return data;
    },
  });
}

// ── Mutation: crea cliente ──

export function useCreateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ClientCreate) => {
      const { data } = await apiClient.post<Client>("/clients", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Mutation: aggiorna cliente ──

export function useUpdateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: ClientUpdate & { id: number }) => {
      const { data } = await apiClient.put<Client>(
        `/clients/${id}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Mutation: elimina cliente ──

export function useDeleteClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/clients/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
