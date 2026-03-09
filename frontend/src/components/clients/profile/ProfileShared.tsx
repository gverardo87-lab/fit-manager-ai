// src/components/clients/profile/ProfileShared.tsx
"use client";

/**
 * Componenti condivisi per i tab del profilo cliente.
 * EmptyTab, TabSkeleton, ProfileSkeleton.
 */

import Link from "next/link";
import { AlertTriangle, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

interface EmptyTabProps {
  icon?: LucideIcon;
  message: string;
  /** Breve spiegazione contestuale (opzionale). */
  hint?: string;
  /** CTA button (opzionale). */
  action?: {
    label: string;
    onClick?: () => void;
    href?: string;
  };
}

export function EmptyTab({ icon: Icon, message, hint, action }: EmptyTabProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
      {Icon && <Icon className="h-10 w-10 text-muted-foreground/25" />}
      <p className="text-sm font-medium text-muted-foreground">{message}</p>
      {hint && (
        <p className="max-w-xs text-center text-xs text-muted-foreground/70">{hint}</p>
      )}
      {action && (
        <div className="mt-1">
          {action.href ? (
            <Button variant="outline" size="sm" asChild>
              <Link href={action.href}>{action.label}</Link>
            </Button>
          ) : action.onClick ? (
            <Button variant="outline" size="sm" onClick={action.onClick}>
              {action.label}
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function TabSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

export function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

export function NotFoundState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <AlertTriangle className="h-12 w-12 text-muted-foreground/30" />
      <p className="text-lg font-medium">Cliente non trovato</p>
    </div>
  );
}
