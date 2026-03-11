import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  InstallationConnectivityPortalValidationRequest,
  InstallationConnectivityPortalValidationResponse,
} from "@/types/api";

async function validatePortalLink(payload: InstallationConnectivityPortalValidationRequest) {
  const { data } = await apiClient.post<InstallationConnectivityPortalValidationResponse>(
    "/system/connectivity-portal-validation",
    payload,
  );
  return data;
}

export function usePortalValidation() {
  return useMutation({
    mutationFn: validatePortalLink,
    onSuccess: (data) => {
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
        extractErrorMessage(error, "Errore nella validazione del link pubblico anamnesi"),
      );
    },
  });
}
