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
  ClipboardList,
  Search,
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
// NAVIGAZIONE — Section Labels pattern (Linear/Notion style)
// ════════════════════════════════════════════════════════════

type NavLink = { href: string; label: string; icon: React.ComponentType<{ className?: string }> };
type NavSection = { section: string; items: NavLink[] };
type NavEntry = NavLink | NavSection;

const NAV_TOP: NavEntry[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agenda", label: "Agenda", icon: Calendar },
  {
    section: "Clienti",
    items: [
      { href: "/clienti", label: "Clienti", icon: Users },
    ],
  },
  {
    section: "Contabilità",
    items: [
      { href: "/contratti", label: "Contratti", icon: FileText },
      { href: "/cassa", label: "Cassa", icon: Wallet },
    ],
  },
  {
    section: "Allenamento",
    items: [
      { href: "/esercizi", label: "Esercizi", icon: Dumbbell },
      { href: "/schede", label: "Schede", icon: ClipboardList },
    ],
  },
];

const NAV_BOTTOM: NavLink[] = [
  { href: "/impostazioni", label: "Impostazioni", icon: Settings },
];

// ════════════════════════════════════════════════════════════
// NAV ITEM
// ════════════════════════════════════════════════════════════

function NavItem({
  item,
  pathname,
  onNavigate,
}: {
  item: NavLink;
  pathname: string;
  onNavigate?: () => void;
}) {
  const isActive =
    item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          href={item.href}
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
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
}

// ════════════════════════════════════════════════════════════
// SIDEBAR
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

      {/* ── Search trigger (apre Command Palette) ── */}
      <div className="px-3 pt-3">
        <Button
          variant="outline"
          className="w-full justify-start gap-2 text-sm text-muted-foreground"
          onClick={() => window.dispatchEvent(new Event("open-command-palette"))}
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 text-left">Cerca...</span>
          <kbd className="pointer-events-none rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            Ctrl K
          </kbd>
        </Button>
      </div>

      {/* ── Navigation Links ── */}
      <nav className="flex flex-1 flex-col overflow-y-auto px-3 py-4">
        <div className="space-y-1">
          {NAV_TOP.map((entry) =>
            "section" in entry ? (
              <div key={entry.section} className="pt-4 first:pt-0">
                <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/60">
                  {entry.section}
                </p>
                <div className="space-y-0.5">
                  {entry.items.map((item) => (
                    <NavItem
                      key={item.href}
                      item={item}
                      pathname={pathname}
                      onNavigate={onNavigate}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <NavItem
                key={entry.href}
                item={entry}
                pathname={pathname}
                onNavigate={onNavigate}
              />
            )
          )}
        </div>

        {/* ── Bottom nav (Impostazioni) ── */}
        <div className="mt-auto pt-4">
          <Separator className="mb-3" />
          {NAV_BOTTOM.map((item) => (
            <NavItem
              key={item.href}
              item={item}
              pathname={pathname}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </nav>

      {/* ── Trainer info + Logout ── */}
      <div className="border-t p-4">
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
