// src/components/ui/semaphore-dot.tsx
/**
 * Colored dot for semaphore status (green/amber/red).
 */

import { cn } from "@/lib/utils";

const SEMAPHORE_COLORS = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
} as const;

export function SemaphoreDot({ status }: { status: "green" | "amber" | "red" }) {
  return <span className={cn("inline-block h-2 w-2 shrink-0 rounded-full", SEMAPHORE_COLORS[status])} />;
}
