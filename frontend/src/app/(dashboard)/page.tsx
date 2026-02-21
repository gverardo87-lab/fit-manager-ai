// src/app/(dashboard)/page.tsx
"use client";

/**
 * Dashboard — pagina principale con KPI aggregati.
 *
 * Mostra 4 metriche dal backend (GET /api/dashboard/summary):
 * - Clienti attivi
 * - Entrate mese corrente
 * - Rate pendenti / in scadenza
 * - Appuntamenti oggi
 *
 * Loading: skeleton animati.
 * Error: messaggio con retry.
 * Success: card con icone tematiche e colori.
 */

import { Users, Euro, AlertTriangle, CalendarCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";

// ════════════════════════════════════════════════════════════
// KPI CONFIG
// ════════════════════════════════════════════════════════════

const KPI_CONFIG = [
  {
    key: "active_clients" as const,
    label: "Clienti Attivi",
    icon: Users,
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-600 dark:text-blue-400",
    format: (v: number) => v.toString(),
  },
  {
    key: "monthly_revenue" as const,
    label: "Entrate Mese",
    icon: Euro,
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    format: (v: number) =>
      v.toLocaleString("it-IT", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }),
  },
  {
    key: "pending_rates" as const,
    label: "Rate in Scadenza",
    icon: AlertTriangle,
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-600 dark:text-amber-400",
    format: (v: number) => v.toString(),
  },
  {
    key: "todays_appointments" as const,
    label: "Appuntamenti Oggi",
    icon: CalendarCheck,
    iconBg: "bg-violet-500/10",
    iconColor: "text-violet-600 dark:text-violet-400",
    format: (v: number) => v.toString(),
  },
] as const;

// ════════════════════════════════════════════════════════════
// SKELETON LOADING
// ════════════════════════════════════════════════════════════

function KpiSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-9 rounded-lg" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-20" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPALE
// ════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useDashboard();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Panoramica della tua attivita'
        </p>
      </div>

      {/* KPI Cards */}
      {isLoading && <KpiSkeleton />}

      {isError && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="flex items-center justify-between py-6">
            <p className="text-sm text-destructive">
              Impossibile caricare i dati della dashboard.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Riprova
            </Button>
          </CardContent>
        </Card>
      )}

      {data && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {KPI_CONFIG.map((kpi) => (
            <Card
              key={kpi.key}
              className="transition-shadow hover:shadow-md"
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {kpi.label}
                </CardTitle>
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-lg ${kpi.iconBg}`}
                >
                  <kpi.icon className={`h-4.5 w-4.5 ${kpi.iconColor}`} />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold tracking-tight">
                  {kpi.format(data[kpi.key])}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
