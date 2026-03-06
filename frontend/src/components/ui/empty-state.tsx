import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { LucideIcon } from "lucide-react"

interface EmptyStateAction {
  label: string
  onClick: () => void
  variant?: "default" | "outline" | "link"
  icon?: React.ReactNode
}

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  subtitle?: string
  action?: EmptyStateAction
  className?: string
}

function EmptyState({ icon: Icon, title, subtitle, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-14",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <Icon className="h-6 w-6 text-muted-foreground/50" />
      </div>
      <div className="text-center">
        <p className="font-medium text-muted-foreground">{title}</p>
        {subtitle && (
          <p className="mt-1 text-sm text-muted-foreground/70">{subtitle}</p>
        )}
      </div>
      {action && (
        <Button
          variant={action.variant ?? "outline"}
          size="sm"
          onClick={action.onClick}
          className="mt-1"
        >
          {action.icon}
          {action.label}
        </Button>
      )}
    </div>
  )
}

export { EmptyState }
export type { EmptyStateProps }
