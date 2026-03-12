import type { CaseBucket, CaseKind, CaseSeverity } from "@/types/api";
import {
  surfaceChipClassName,
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";

export type WorkspaceVariant = "default" | "finance";

const WORKSPACE_BUCKET_TONES: Record<CaseBucket, SurfaceTone> = {
  now: "red",
  today: "amber",
  upcoming_3d: "teal",
  upcoming_7d: "neutral",
  waiting: "neutral",
};

const WORKSPACE_SEVERITY_TONES: Record<CaseSeverity, SurfaceTone> = {
  critical: "red",
  high: "amber",
  medium: "teal",
  low: "neutral",
};

const DEFAULT_CASE_KIND_TONES: Record<CaseKind, SurfaceTone> = {
  onboarding_readiness: "teal",
  session_imminent: "teal",
  followup_post_session: "teal",
  todo_manual: "amber",
  plan_activation: "teal",
  plan_review_due: "teal",
  plan_compliance_risk: "amber",
  plan_cycle_closing: "amber",
  payment_overdue: "red",
  payment_due_soon: "amber",
  contract_renewal_due: "amber",
  recurring_expense_due: "amber",
  client_reactivation: "teal",
  ops_anomaly: "red",
  portal_questionnaire_pending: "teal",
};

const FINANCE_CASE_KIND_TONE_OVERRIDES: Partial<Record<CaseKind, SurfaceTone>> = {
  payment_overdue: "red",
  payment_due_soon: "amber",
  contract_renewal_due: "teal",
  recurring_expense_due: "amber",
};

const WORKSPACE_ACCENT_CLASS: Record<CaseSeverity, string> = {
  critical: "bg-red-500",
  high: "bg-amber-500",
  medium: "bg-teal-500",
  low: "bg-stone-400",
};

const WORKSPACE_BUCKET_MARKER_CLASS: Record<CaseBucket, string> = {
  now: "bg-red-500",
  today: "bg-amber-500",
  upcoming_3d: "bg-teal-500",
  upcoming_7d: "bg-stone-300 dark:bg-zinc-600",
  waiting: "bg-stone-300 dark:bg-zinc-600",
};

const WORKSPACE_BUCKET_RAIL_CLASS: Record<CaseBucket, string> = {
  now: "border-red-200 dark:border-red-900/40",
  today: "border-amber-200 dark:border-amber-900/40",
  upcoming_3d: "border-teal-200 dark:border-teal-900/35",
  upcoming_7d: "border-stone-200/60 dark:border-zinc-800",
  waiting: "border-stone-200/60 dark:border-zinc-800",
};

export function getWorkspaceBucketTone(bucket: CaseBucket): SurfaceTone {
  return WORKSPACE_BUCKET_TONES[bucket];
}

export function getWorkspaceSeverityTone(severity: CaseSeverity): SurfaceTone {
  return WORKSPACE_SEVERITY_TONES[severity];
}

export function getWorkspaceCaseKindTone(
  caseKind: CaseKind,
  variant: WorkspaceVariant = "default",
): SurfaceTone {
  if (variant === "finance" && FINANCE_CASE_KIND_TONE_OVERRIDES[caseKind]) {
    return FINANCE_CASE_KIND_TONE_OVERRIDES[caseKind]!;
  }
  return DEFAULT_CASE_KIND_TONES[caseKind];
}

export function getWorkspaceAccentClass(severity: CaseSeverity): string {
  return WORKSPACE_ACCENT_CLASS[severity];
}

export function getWorkspaceBucketMarkerClass(bucket: CaseBucket): string {
  return WORKSPACE_BUCKET_MARKER_CLASS[bucket];
}

export function getWorkspaceBucketRailClass(bucket: CaseBucket): string {
  return WORKSPACE_BUCKET_RAIL_CLASS[bucket];
}

export function getWorkspaceCardClassName(
  {
    variant,
    selected,
  }: {
    variant: WorkspaceVariant;
    selected: boolean;
  },
  className?: string,
) {
  return cn(
    surfaceRoleClassName(
      {
        role: variant === "finance" ? "page" : "signal",
        tone: selected ? (variant === "finance" ? "amber" : "teal") : "neutral",
        interactive: true,
      },
      variant === "finance" ? "p-4" : "",
    ),
    selected && "ring-1 ring-primary/12",
    className,
  );
}

export function getWorkspacePanelClassName(
  {
    variant,
    embedded,
  }: {
    variant: WorkspaceVariant;
    embedded?: boolean;
  },
  className?: string,
) {
  return cn(
    "flex min-h-0 flex-col",
    !embedded &&
      surfaceRoleClassName({
        role: "dossier",
        tone: variant === "finance" ? "amber" : "neutral",
      }),
    className,
  );
}

export function getWorkspaceSectionClassName(
  {
    variant,
    emphasis = "neutral",
  }: {
    variant: WorkspaceVariant;
    emphasis?: "neutral" | "accent" | "subtle";
  },
  className?: string,
) {
  const role = emphasis === "subtle" ? "signal" : emphasis === "accent" ? "hero" : "context";
  const tone =
    emphasis === "accent"
      ? variant === "finance"
        ? "amber"
        : "teal"
      : variant === "finance"
        ? "amber"
        : "neutral";

  return surfaceRoleClassName({ role, tone }, className);
}

export function getWorkspaceChipClassName(
  tone: SurfaceTone,
  className?: string,
) {
  return surfaceChipClassName({ tone }, className);
}
