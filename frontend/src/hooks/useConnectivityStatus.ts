import { useQuery } from "@tanstack/react-query";

import apiClient from "@/lib/api-client";
import type { InstallationConnectivityStatusResponse } from "@/types/api";

export function useConnectivityStatus() {
  return useQuery<InstallationConnectivityStatusResponse>({
    queryKey: ["system", "connectivity-status"],
    queryFn: async () => {
      const { data } = await apiClient.get<InstallationConnectivityStatusResponse>(
        "/system/connectivity-status",
      );
      return data;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
