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
import type {
  DashboardSummary,
  DashboardAlerts,
  Event,
  ListResponse,
  OverdueRateItem,
  ExpiringContractItem,
  InactiveClientItem,
} from "@/types/api";

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

export function useOverdueRates(enabled = true) {
  return useQuery<ListResponse<OverdueRateItem>>({
    queryKey: ["dashboard", "overdue-rates"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<OverdueRateItem>>(
        "/dashboard/overdue-rates"
      );
      return data;
    },
    enabled,
  });
}

export function useExpiringContracts(enabled = true) {
  return useQuery<ListResponse<ExpiringContractItem>>({
    queryKey: ["dashboard", "expiring-contracts"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<ExpiringContractItem>>(
        "/dashboard/expiring-contracts"
      );
      return data;
    },
    enabled,
  });
}

export function useInactiveClients(enabled = true) {
  return useQuery<ListResponse<InactiveClientItem>>({
    queryKey: ["dashboard", "inactive-clients"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<InactiveClientItem>>(
        "/dashboard/inactive-clients"
      );
      return data;
    },
    enabled,
  });
}
