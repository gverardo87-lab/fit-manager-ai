import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  InstallationConnectivityConfigRequest,
  InstallationConnectivityConfigResponse,
} from "@/types/api";

async function applyConnectivityConfig(payload: InstallationConnectivityConfigRequest) {
  const { data } = await apiClient.post<InstallationConnectivityConfigResponse>(
    "/system/connectivity-config",
    payload,
  );
  return data;
}

export function useApplyConnectivityConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: applyConnectivityConfig,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["system", "connectivity-status"] });
      queryClient.invalidateQueries({ queryKey: ["system", "health"] });
      toast.success(data.message);
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nel salvataggio della configurazione di connettivita"),
      );
    },
  });
}
