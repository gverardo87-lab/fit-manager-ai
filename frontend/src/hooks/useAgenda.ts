// src/hooks/useAgenda.ts
/**
 * Custom hooks per il modulo Agenda.
 *
 * - useEvents({ start, end }): lista eventi in un range temporale
 * - useCreateEvent(): crea evento (gestisce 409 sovrapposizione)
 * - useUpdateEvent(): aggiorna evento (gestisce 409 sovrapposizione)
 * - useDeleteEvent(): elimina evento
 *
 * Ogni mutation invalida ["events"] + ["dashboard"] (todays_appointments).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import axios from "axios";
import apiClient from "@/lib/api-client";
import type {
  Event,
  EventCreate,
  EventUpdate,
  ListResponse,
} from "@/types/api";

// ── Query: lista eventi per range temporale ──

interface UseEventsParams {
  start?: string; // ISO date "YYYY-MM-DD"
  end?: string;
}

export function useEvents(params: UseEventsParams = {}) {
  const { start, end } = params;

  return useQuery<ListResponse<Event>>({
    queryKey: ["events", { start, end }],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>("/events", {
        params: { start, end },
      });
      return data;
    },
    enabled: !!start && !!end,
  });
}

// ── Mutation: crea evento ──

export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: EventCreate) => {
      const { data } = await apiClient.post<Event>("/events", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Evento creato");
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        toast.error(
          "Sovrapposizione oraria: hai gia' un impegno in questo slot"
        );
        return;
      }
      toast.error("Errore nella creazione dell'evento");
    },
  });
}

// ── Mutation: aggiorna evento ──

export function useUpdateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: EventUpdate & { id: number }) => {
      const { data } = await apiClient.put<Event>(`/events/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Evento aggiornato");
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        toast.error(
          "Sovrapposizione oraria: hai gia' un impegno in questo slot"
        );
        return;
      }
      toast.error("Errore nell'aggiornamento dell'evento");
    },
  });
}

// ── Mutation: elimina evento ──

export function useDeleteEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/events/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Evento eliminato");
    },
    onError: () => {
      toast.error("Errore nell'eliminazione dell'evento");
    },
  });
}
