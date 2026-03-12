import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const surfaceRoleVariants = cva("fm-surface text-card-foreground", {
  variants: {
    role: {
      page: "fm-surface-page",
      hero: "fm-surface-hero",
      signal: "fm-surface-signal",
      context: "fm-surface-context",
      dossier: "fm-surface-dossier",
      chart: "fm-surface-chart",
    },
    tone: {
      neutral: "fm-surface-tone-neutral",
      teal: "fm-surface-tone-teal",
      amber: "fm-surface-tone-amber",
      red: "fm-surface-tone-red",
    },
    interactive: {
      true: "fm-surface-interactive",
      false: "",
    },
  },
  defaultVariants: {
    role: "context",
    tone: "neutral",
    interactive: false,
  },
});

export const surfaceChipVariants = cva("fm-chip", {
  variants: {
    tone: {
      neutral: "fm-chip-tone-neutral",
      teal: "fm-chip-tone-teal",
      amber: "fm-chip-tone-amber",
      red: "fm-chip-tone-red",
    },
    emphasis: {
      subtle: "fm-chip-emphasis-subtle",
      strong: "fm-chip-emphasis-strong",
    },
  },
  defaultVariants: {
    tone: "neutral",
    emphasis: "subtle",
  },
});

export type SurfaceTone = NonNullable<VariantProps<typeof surfaceRoleVariants>["tone"]>;

export function surfaceRoleClassName(
  props?: VariantProps<typeof surfaceRoleVariants>,
  className?: string,
) {
  return cn(surfaceRoleVariants(props), className);
}

export function surfaceChipClassName(
  props?: VariantProps<typeof surfaceChipVariants>,
  className?: string,
) {
  return cn(surfaceChipVariants(props), className);
}
