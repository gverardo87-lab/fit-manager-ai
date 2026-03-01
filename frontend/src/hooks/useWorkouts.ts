// src/hooks/useWorkouts.ts
/**
 * Custom hooks per il modulo Schede Allenamento.
 *
 * Pattern: una funzione per operazione, ognuna con la propria queryKey.
 * Le mutations invalidano ["workouts"] / ["workout", id] su successo.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  WorkoutPlan,
  WorkoutPlanCreate,
  WorkoutPlanUpdate,
  WorkoutPlanListResponse,
  WorkoutSessionInput,
  WorkoutLog,
  WorkoutLogCreate,
  WorkoutLogListResponse,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// QUERY: Lista schede (paginata + filtri)
// ════════════════════════════════════════════════════════════

export interface WorkoutFilters {
  id_cliente?: number;
  obiettivo?: string;
  livello?: string;
}

export function useWorkouts(filters?: WorkoutFilters) {
  return useQuery<WorkoutPlanListResponse>({
    queryKey: ["workouts", filters],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page: 1,
        page_size: 200,
      };
      if (filters?.id_cliente) params.id_cliente = filters.id_cliente;
      if (filters?.obiettivo) params.obiettivo = filters.obiettivo;
      if (filters?.livello) params.livello = filters.livello;

      const { data } = await apiClient.get<WorkoutPlanListResponse>("/workouts", { params });
      return data;
    },
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Schede di un singolo cliente (profilo)
// ════════════════════════════════════════════════════════════

export function useClientWorkouts(idCliente: number | null) {
  return useQuery<WorkoutPlanListResponse>({
    queryKey: ["workouts", { idCliente }],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkoutPlanListResponse>("/workouts", {
        params: { page: 1, page_size: 100, id_cliente: idCliente },
      });
      return data;
    },
    enabled: idCliente !== null,
  });
}

// ════════════════════════════════════════════════════════════
// QUERY: Singola scheda (con sessioni + esercizi enriched)
// ════════════════════════════════════════════════════════════

export function useWorkout(id: number | null) {
  return useQuery<WorkoutPlan>({
    queryKey: ["workout", id],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkoutPlan>(`/workouts/${id}`);
      return data;
    },
    enabled: id !== null,
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Crea scheda
// ════════════════════════════════════════════════════════════

export function useCreateWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: WorkoutPlanCreate) => {
      const { data } = await apiClient.post<WorkoutPlan>("/workouts", payload);
      return data;
    },
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      toast.success(`Scheda "${plan.nome}" creata`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione della scheda"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Aggiorna metadati scheda
// ════════════════════════════════════════════════════════════

export function useUpdateWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: WorkoutPlanUpdate & { id: number }) => {
      const { data } = await apiClient.put<WorkoutPlan>(`/workouts/${id}`, payload);
      return data;
    },
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      queryClient.invalidateQueries({ queryKey: ["workout", plan.id] });
      toast.success("Scheda aggiornata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento della scheda"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Full-replace sessioni + esercizi
// ════════════════════════════════════════════════════════════

export function useUpdateWorkoutSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, sessions }: { id: number; sessions: WorkoutSessionInput[] }) => {
      const { data } = await apiClient.put<WorkoutPlan>(`/workouts/${id}/sessions`, sessions);
      return data;
    },
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      queryClient.invalidateQueries({ queryKey: ["workout", plan.id] });
      toast.success("Sessioni aggiornate");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento delle sessioni"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Soft delete scheda
// ════════════════════════════════════════════════════════════

export function useDeleteWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/workouts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      toast.success("Scheda eliminata");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione della scheda"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Duplica scheda
// ════════════════════════════════════════════════════════════

export function useDuplicateWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, id_cliente }: { id: number; id_cliente?: number }) => {
      const params = id_cliente ? { id_cliente } : {};
      const { data } = await apiClient.post<WorkoutPlan>(`/workouts/${id}/duplicate`, null, { params });
      return data;
    },
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      toast.success(`Scheda duplicata: "${plan.nome}"`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella duplicazione della scheda"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// WORKOUT LOGS — Esecuzione sessioni
// ════════════════════════════════════════════════════════════

/**
 * Lista log esecuzione per un cliente (profilo cliente, SchedeTab).
 * Filtro opzionale per scheda specifica.
 */
export function useClientWorkoutLogs(
  clientId: number | null,
  idScheda?: number,
) {
  return useQuery<WorkoutLogListResponse>({
    queryKey: ["workout-logs", clientId, { id_scheda: idScheda }],
    queryFn: async () => {
      const params: Record<string, number> = {};
      if (idScheda) params.id_scheda = idScheda;
      const { data } = await apiClient.get<WorkoutLogListResponse>(
        `/clients/${clientId}/workout-logs`,
        { params },
      );
      return data;
    },
    enabled: clientId !== null,
  });
}

/**
 * Lista log esecuzione per una scheda (builder page).
 */
export function useWorkoutLogs(workoutId: number | null) {
  return useQuery<WorkoutLogListResponse>({
    queryKey: ["workout-logs", { workoutId }],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkoutLogListResponse>(
        `/workouts/${workoutId}/logs`,
      );
      return data;
    },
    enabled: workoutId !== null,
  });
}

/**
 * Mutation: registra esecuzione sessione.
 */
export function useCreateWorkoutLog(clientId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: WorkoutLogCreate) => {
      const { data } = await apiClient.post<WorkoutLog>(
        `/clients/${clientId}/workout-logs`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workout-logs"] });
      toast.success("Sessione registrata");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella registrazione della sessione"),
      );
    },
  });
}

/**
 * Mutation: elimina log esecuzione (soft delete).
 */
export function useDeleteWorkoutLog(clientId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (logId: number) => {
      await apiClient.delete(`/clients/${clientId}/workout-logs/${logId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workout-logs"] });
      toast.success("Registrazione rimossa");
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella rimozione della registrazione"),
      );
    },
  });
}
