// src/hooks/useTodos.ts
/**
 * Custom hooks per il modulo Todo.
 *
 * - useTodos(): lista todo attivi (non completati prima, poi per scadenza)
 * - useCreateTodo(): crea todo
 * - useToggleTodo(): toggle completato/non completato
 * - useDeleteTodo(): soft-delete todo
 *
 * Ogni mutation invalida ["todos"].
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type { Todo, TodoCreate, ListResponse } from "@/types/api";

// ── Query: lista todo ──

export function useTodos(completato?: boolean) {
  return useQuery({
    queryKey: ["todos", { completato }],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (completato !== undefined) params.completato = String(completato);
      const { data } = await apiClient.get<ListResponse<Todo>>("/todos", { params });
      return data;
    },
  });
}

// ── Mutation: crea todo ──

export function useCreateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TodoCreate) => {
      const { data } = await apiClient.post<Todo>("/todos", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Promemoria creato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione del promemoria"));
    },
  });
}

// ── Mutation: toggle completato ──

export function useToggleTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (todoId: number) => {
      const { data } = await apiClient.patch<Todo>(`/todos/${todoId}/toggle`);
      return data;
    },
    onSuccess: (todo) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(todo.completato ? "Completato!" : "Riaperto");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento"));
    },
  });
}

// ── Mutation: elimina todo ──

export function useDeleteTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (todoId: number) => {
      await apiClient.delete(`/todos/${todoId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Promemoria eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione"));
    },
  });
}
