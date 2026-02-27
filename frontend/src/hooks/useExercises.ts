// src/hooks/useExercises.ts
/**
 * Custom hooks per il modulo Esercizi.
 *
 * v2: hooks per media upload/delete e relazioni progressione/regressione.
 *
 * Pattern: una funzione per operazione, ognuna con la propria queryKey.
 * Le mutations invalidano ["exercises"] / ["exercise", id] su successo.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Exercise,
  ExerciseCreate,
  ExerciseUpdate,
  ExerciseListResponse,
  ExerciseMedia,
  ExerciseRelation,
  ExerciseRelationCreate,
  SafetyMapResponse,
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
        page_size: 1200,
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
// QUERY: Singolo esercizio (enriched: media + relazioni)
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
      // Suggerimenti validazione post-save (informativi, mai bloccanti)
      const suggerimenti = (exercise as Exercise & { suggerimenti?: string[] }).suggerimenti;
      if (suggerimenti?.length) {
        for (const s of suggerimenti) {
          toast.warning(s, { duration: 8000 });
        }
      }
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

// ════════════════════════════════════════════════════════════
// MUTATION: Upload media
// ════════════════════════════════════════════════════════════

export function useUploadMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ exerciseId, file }: { exerciseId: number; file: File }) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<ExerciseMedia>(
        `/exercises/${exerciseId}/media`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
    onSuccess: (_media, { exerciseId }) => {
      queryClient.invalidateQueries({ queryKey: ["exercise", exerciseId] });
      toast.success("Media caricato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel caricamento del media"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Elimina media
// ════════════════════════════════════════════════════════════

export function useDeleteMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ exerciseId, mediaId }: { exerciseId: number; mediaId: number }) => {
      await apiClient.delete(`/exercises/${exerciseId}/media/${mediaId}`);
      return { exerciseId };
    },
    onSuccess: ({ exerciseId }) => {
      queryClient.invalidateQueries({ queryKey: ["exercise", exerciseId] });
      toast.success("Media eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del media"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Crea relazione
// ════════════════════════════════════════════════════════════

export function useCreateRelation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ exerciseId, ...payload }: ExerciseRelationCreate & { exerciseId: number }) => {
      const { data } = await apiClient.post<ExerciseRelation>(
        `/exercises/${exerciseId}/relations`,
        payload,
      );
      return { ...data, exerciseId };
    },
    onSuccess: ({ exerciseId }) => {
      queryClient.invalidateQueries({ queryKey: ["exercise", exerciseId] });
      toast.success("Relazione creata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione della relazione"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Elimina relazione
// ════════════════════════════════════════════════════════════

export function useDeleteRelation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ exerciseId, relationId }: { exerciseId: number; relationId: number }) => {
      await apiClient.delete(`/exercises/${exerciseId}/relations/${relationId}`);
      return { exerciseId };
    },
    onSuccess: ({ exerciseId }) => {
      queryClient.invalidateQueries({ queryKey: ["exercise", exerciseId] });
      toast.success("Relazione eliminata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione della relazione"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Relazioni esercizio (leggero, per SafetyPopover)
// ════════════════════════════════════════════════════════════

export function useExerciseRelations(exerciseId: number | null) {
  return useQuery<ExerciseRelation[]>({
    queryKey: ["exercise-relations", exerciseId],
    queryFn: async () => {
      const { data } = await apiClient.get<ExerciseRelation[]>(
        `/exercises/${exerciseId}/relations`,
      );
      return data;
    },
    enabled: exerciseId !== null && exerciseId > 0,
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Safety Map (anamnesi × condizioni mediche)
// ════════════════════════════════════════════════════════════

export function useExerciseSafetyMap(clientId: number | null) {
  return useQuery<SafetyMapResponse>({
    queryKey: ["exercise-safety-map", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<SafetyMapResponse>(
        "/exercises/safety-map",
        { params: { client_id: clientId } },
      );
      return data;
    },
    enabled: clientId !== null && clientId > 0,
  });
}
