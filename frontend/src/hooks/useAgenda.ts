// src/hooks/useAgenda.ts
/**
 * Custom hooks per il modulo Agenda.
 *
 * - useEvents({ start, end }): lista eventi con date idratate (Date objects)
 * - useCreateEvent(): crea evento (gestisce 409 sovrapposizione)
 * - useUpdateEvent(): aggiorna evento (gestisce 409 sovrapposizione)
 * - useDeleteEvent(): elimina evento
 *
 * Ogni mutation invalida ["events"] + ["dashboard"] + ["clients"] (crediti).
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

// ── Evento con date idratate (Date objects, non stringhe) ──

export interface EventHydrated extends Omit<Event, "data_inizio" | "data_fine"> {
  data_inizio: Date;
  data_fine: Date;
}

/** Converte stringhe ISO (o con spazio) in Date objects. */
function hydrateEvent(e: Event): EventHydrated {
  return {
    ...e,
    data_inizio: new Date(e.data_inizio.replace(" ", "T")),
    data_fine: new Date(e.data_fine.replace(" ", "T")),
  };
}

// ── Query: lista eventi per range temporale ──

interface UseEventsParams {
  start?: string; // ISO date "YYYY-MM-DD"
  end?: string;
}

export function useEvents(params: UseEventsParams = {}) {
  const { start, end } = params;

  return useQuery({
    queryKey: ["events", { start, end }],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>("/events", {
        params: { start, end },
      });
      return data;
    },
    select: (data): ListResponse<EventHydrated> => ({
      ...data,
      items: data.items.map(hydrateEvent),
    }),
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
      queryClient.invalidateQueries({ queryKey: ["clients"] });
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
      queryClient.invalidateQueries({ queryKey: ["clients"] });
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
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      toast.success("Evento eliminato");
    },
    onError: () => {
      toast.error("Errore nell'eliminazione dell'evento");
    },
  });
}
