// src/hooks/useWorkspace.ts
/**
 * Read-only hooks for the operational workspace.
 */

import { useQuery } from "@tanstack/react-query";

import apiClient from "@/lib/api-client";
import type {
  ClientAvatar,
  ClientAvatarBatchResponse,
  SessionPrepResponse,
  WorkspaceCaseDetailResponse,
  WorkspaceCaseListResponse,
  WorkspaceTodayResponse,
} from "@/types/api";

export function useWorkspaceToday(enabled = true) {
  return useQuery<WorkspaceTodayResponse>({
    queryKey: ["workspace", "today"],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkspaceTodayResponse>("/workspace/today");
      return data;
    },
    refetchInterval: 60_000,
    enabled,
  });
}

export interface WorkspaceCasesQuery {
  workspace?: "today" | "onboarding" | "programmi" | "renewals_cash";
  page?: number;
  page_size?: number;
  bucket?: "now" | "today" | "upcoming_3d" | "upcoming_7d" | "waiting";
  severity?: "critical" | "high" | "medium" | "low";
  case_kind?:
    | "onboarding_readiness"
    | "session_imminent"
    | "followup_post_session"
    | "todo_manual"
    | "plan_activation"
    | "plan_review_due"
    | "plan_compliance_risk"
    | "plan_cycle_closing"
    | "payment_overdue"
    | "payment_due_soon"
    | "contract_renewal_due"
    | "recurring_expense_due"
    | "client_reactivation"
    | "ops_anomaly"
    | "portal_questionnaire_pending";
  search?: string;
  sort_by?: "priority" | "due_date";
}

export function useWorkspaceCases(query: WorkspaceCasesQuery = {}, enabled = true) {
  const params = {
    workspace: query.workspace ?? "today",
    page: query.page ?? 1,
    page_size: query.page_size ?? 25,
    bucket: query.bucket,
    severity: query.severity,
    case_kind: query.case_kind,
    search: query.search?.trim() || undefined,
    sort_by: query.sort_by ?? "priority",
  };

  return useQuery<WorkspaceCaseListResponse>({
    queryKey: ["workspace", "cases", params],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkspaceCaseListResponse>("/workspace/cases", {
        params,
      });
      return data;
    },
    refetchInterval: 60_000,
    enabled,
  });
}

export interface WorkspaceCaseDetailQuery {
  caseId: string;
  workspace?: "today" | "onboarding" | "programmi" | "renewals_cash";
}

export function useSessionPrep(enabled = true) {
  return useQuery<SessionPrepResponse>({
    queryKey: ["workspace", "session-prep"],
    queryFn: async () => {
      const { data } = await apiClient.get<SessionPrepResponse>("/workspace/today/session-prep");
      return data;
    },
    refetchInterval: 60_000,
    enabled,
  });
}

export function useWorkspaceCaseDetail(query: WorkspaceCaseDetailQuery, enabled = true) {
  const workspace = query.workspace ?? "today";
  const caseId = query.caseId;

  return useQuery<WorkspaceCaseDetailResponse>({
    queryKey: ["workspace", "case-detail", workspace, caseId],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkspaceCaseDetailResponse>(
        `/workspace/cases/${encodeURIComponent(caseId)}`,
        {
          params: { workspace },
        },
      );
      return data;
    },
    refetchInterval: 60_000,
    enabled: enabled && caseId.trim().length > 0,
  });
}

export function useClientAvatar(clientId: number, enabled = true) {
  return useQuery<ClientAvatar>({
    queryKey: ["client-avatar", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<ClientAvatar>(`/clients/${clientId}/avatar`);
      return data;
    },
    refetchInterval: 60_000,
    enabled: enabled && clientId > 0,
  });
}

export function useClientAvatars(clientIds: number[], enabled = true) {
  const sortedIds = [...clientIds].sort((a, b) => a - b);
  const key = sortedIds.join(",");

  return useQuery<Map<number, ClientAvatar>>({
    queryKey: ["client-avatars", key],
    queryFn: async () => {
      if (sortedIds.length === 0) return new Map();
      const { data } = await apiClient.post<ClientAvatarBatchResponse>(
        "/clients/avatars",
        { client_ids: sortedIds },
      );
      return new Map(data.avatars.map((a) => [a.client_id, a]));
    },
    refetchInterval: 60_000,
    enabled: enabled && sortedIds.length > 0,
  });
}
