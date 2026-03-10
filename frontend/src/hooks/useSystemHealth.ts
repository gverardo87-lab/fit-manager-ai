import { useQuery } from "@tanstack/react-query";
import axios from "axios";

import type { InstallationHealthResponse } from "@/types/api";

export function useSystemHealth() {
  return useQuery<InstallationHealthResponse>({
    queryKey: ["system", "health"],
    queryFn: async () => {
      const { data } = await axios.get<InstallationHealthResponse>("/health", {
        timeout: 10_000,
      });
      return data;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
