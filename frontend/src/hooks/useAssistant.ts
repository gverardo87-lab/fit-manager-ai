/**
 * Hook per l'Assistant CRM — parse + commit.
 *
 * - useParseAssistant(): parse testo → operazioni strutturate (read-only)
 * - useCommitAssistant(): conferma operazione → esegue azione + invalidation
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  AssistantCommitRequest,
  AssistantCommitResponse,
  AssistantParseRequest,
  AssistantParseResponse,
} from "@/types/api";

export function useParseAssistant() {
  return useMutation({
    mutationFn: async (payload: AssistantParseRequest) => {
      const { data } = await apiClient.post<AssistantParseResponse>(
        "/assistant/parse",
        payload,
      );
      return data;
    },
    // No toast on parse — e' un'operazione read-only di preview
  });
}

export function useCommitAssistant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AssistantCommitRequest) => {
      const { data } = await apiClient.post<AssistantCommitResponse>(
        "/assistant/commit",
        payload,
      );
      return data;
    },
    onSuccess: (data) => {
      if (data.success) {
        for (const key of data.invalidate) {
          queryClient.invalidateQueries({ queryKey: [key] });
        }
        toast.success(data.message);
      } else {
        toast.error(data.message);
      }
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nell'esecuzione del comando"),
      );
    },
  });
}
