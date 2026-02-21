// src/hooks/useDashboard.ts
/**
 * Custom hook per i KPI della dashboard.
 *
 * Usa useQuery di React Query per chiamare GET /api/dashboard/summary.
 * Il componente non deve MAI usare useEffect per le chiamate API.
 *
 * Re-fetch automatico ogni 60 secondi (i KPI cambiano lentamente).
 */

import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import type { DashboardSummary } from "@/types/api";

export function useDashboard() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>(
        "/dashboard/summary"
      );
      return data;
    },
    // I KPI cambiano lentamente — refetch ogni 60 secondi
    refetchInterval: 60_000,
  });
}
