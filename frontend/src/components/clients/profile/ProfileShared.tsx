// src/components/clients/profile/ProfileShared.tsx
"use client";

/**
 * Componenti condivisi per i tab del profilo cliente.
 * EmptyTab, TabSkeleton, ProfileSkeleton.
 */

import { AlertTriangle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function EmptyTab({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
      <p className="text-sm text-muted-foreground">{message}</p>
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
