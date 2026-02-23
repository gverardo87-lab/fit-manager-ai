// src/hooks/useDashboard.ts
/**
 * Custom hooks per la dashboard.
 *
 * - useDashboard(): KPI aggregati (GET /api/dashboard/summary)
 * - useDashboardAlerts(): warning proattivi (GET /api/dashboard/alerts)
 * - useGhostEvents(): eventi fantasma per risoluzione inline (GET /api/dashboard/ghost-events)
 *
 * Re-fetch automatico ogni 60 secondi.
 */

import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import type { DashboardSummary, DashboardAlerts, Event, ListResponse } from "@/types/api";

export function useDashboard() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>(
        "/dashboard/summary"
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

export function useDashboardAlerts() {
  return useQuery<DashboardAlerts>({
    queryKey: ["dashboard", "alerts"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardAlerts>(
        "/dashboard/alerts"
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

export function useGhostEvents(enabled = true) {
  return useQuery<ListResponse<Event>>({
    queryKey: ["dashboard", "ghost-events"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>(
        "/dashboard/ghost-events"
      );
      return data;
    },
    enabled,
  });
}
