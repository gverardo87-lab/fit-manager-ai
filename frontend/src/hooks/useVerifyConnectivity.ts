import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type { InstallationConnectivityVerifyResponse } from "@/types/api";

async function verifyConnectivity() {
  const { data } = await apiClient.post<InstallationConnectivityVerifyResponse>(
    "/system/connectivity-verify",
  );
  return data;
}

export function useVerifyConnectivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: verifyConnectivity,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["system", "connectivity-status"] });
      if (data.status === "ready") {
        toast.success(data.summary);
      } else if (data.status === "blocked") {
        toast.error(data.summary);
      } else {
        toast(data.summary);
      }
    },
    onError: (error) => {
      toast.error(
        extractErrorMessage(error, "Errore nella verifica della configurazione di connettivita"),
      );
    },
  });
}
