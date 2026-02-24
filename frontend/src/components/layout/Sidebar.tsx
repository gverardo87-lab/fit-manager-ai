// src/components/layout/Sidebar.tsx
"use client";

/**
 * Sidebar — navigazione principale dell'app.
 *
 * Desktop: sidebar fissa a sinistra (w-64, sempre visibile).
 * Mobile: nascosta, aperta via Sheet (hamburger menu nell'header).
 *
 * In basso: dati trainer loggato + bottone logout.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  FileText,
  Wallet,
  Settings,
  LogOut,
  Dumbbell,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { getStoredTrainer, logout } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ════════════════════════════════════════════════════════════
// NAVIGAZIONE
// ════════════════════════════════════════════════════════════

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agenda", label: "Agenda", icon: Calendar },
  { href: "/clienti", label: "Clienti", icon: Users },
  { href: "/contratti", label: "Contratti", icon: FileText },
  { href: "/esercizi", label: "Esercizi", icon: Dumbbell },
  { href: "/cassa", label: "Cassa", icon: Wallet },
  { href: "/impostazioni", label: "Impostazioni", icon: Settings },
] as const;

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

interface SidebarProps {
  onNavigate?: () => void; // Chiamato dopo click su mobile (chiude Sheet)
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const trainer = getStoredTrainer();

  return (
    <div className="flex h-full flex-col">
      {/* ── Logo ── */}
      <div className="flex h-16 items-center gap-3 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
          <Dumbbell className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-base font-bold leading-tight tracking-tight">
            ProFit AI
          </h1>
          <p className="text-[11px] text-muted-foreground">Studio</p>
        </div>
      </div>

      <Separator />

      {/* ── Navigation Links ── */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
          return (
            <Tooltip key={item.href}>
              <TooltipTrigger asChild>
                <Link
                  href={item.href}
                  onClick={onNavigate}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-4.5 w-4.5 shrink-0" />
                  {item.label}
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="lg:hidden">
                {item.label}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </nav>

      <Separator />

      {/* ── Trainer info + Logout ── */}
      <div className="p-4">
        {trainer && (
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 text-sm font-semibold text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
              {trainer.nome[0]}
              {trainer.cognome[0]}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {trainer.nome} {trainer.cognome}
              </p>
              <p className="text-xs text-muted-foreground">Trainer</p>
            </div>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
          onClick={() => logout()}
        >
          <LogOut className="h-4 w-4" />
          Esci
        </Button>
      </div>
    </div>
  );
}
