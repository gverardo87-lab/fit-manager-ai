// src/hooks/useExercises.ts
/**
 * Custom hooks per il modulo Esercizi.
 *
 * Pattern: una funzione per operazione, ognuna con la propria queryKey.
 * Le mutations invalidano ["exercises"] su successo.
 *
 * Ogni mutation mostra un toast (sonner) di successo o errore.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Exercise,
  ExerciseCreate,
  ExerciseUpdate,
  ExerciseListResponse,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// QUERY: Lista esercizi con filtri
// ════════════════════════════════════════════════════════════

export interface ExerciseFilters {
  search?: string;
  categoria?: string;
  attrezzatura?: string;
  difficolta?: string;
  pattern_movimento?: string;
  muscolo?: string;
}

export function useExercises(filters?: ExerciseFilters) {
  return useQuery<ExerciseListResponse>({
    queryKey: ["exercises", filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: 1,
        page_size: 500,
      };
      if (filters?.search) params.search = filters.search;
      if (filters?.categoria) params.categoria = filters.categoria;
      if (filters?.attrezzatura) params.attrezzatura = filters.attrezzatura;
      if (filters?.difficolta) params.difficolta = filters.difficolta;
      if (filters?.pattern_movimento) params.pattern_movimento = filters.pattern_movimento;
      if (filters?.muscolo) params.muscolo = filters.muscolo;

      const { data } = await apiClient.get<ExerciseListResponse>("/exercises", { params });
      return data;
    },
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Singolo esercizio
// ════════════════════════════════════════════════════════════

export function useExercise(id: number | null) {
  return useQuery<Exercise>({
    queryKey: ["exercise", id],
    queryFn: async () => {
      const { data } = await apiClient.get<Exercise>(`/exercises/${id}`);
      return data;
    },
    enabled: id !== null,
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Crea esercizio
// ════════════════════════════════════════════════════════════

export function useCreateExercise() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExerciseCreate) => {
      const { data } = await apiClient.post<Exercise>("/exercises", payload);
      return data;
    },
    onSuccess: (exercise) => {
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
      toast.success(`Esercizio "${exercise.nome}" creato`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione dell'esercizio"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Aggiorna esercizio
// ════════════════════════════════════════════════════════════

export function useUpdateExercise() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: ExerciseUpdate & { id: number }) => {
      const { data } = await apiClient.put<Exercise>(`/exercises/${id}`, payload);
      return data;
    },
    onSuccess: (exercise) => {
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
      queryClient.invalidateQueries({ queryKey: ["exercise", exercise.id] });
      toast.success(`Esercizio "${exercise.nome}" aggiornato`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento dell'esercizio"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Elimina esercizio
// ════════════════════════════════════════════════════════════

export function useDeleteExercise() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/exercises/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
      toast.success("Esercizio eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione dell'esercizio"));
    },
  });
}
