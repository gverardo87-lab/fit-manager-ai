// src/app/(dashboard)/layout.tsx
"use client";

/**
 * Layout condiviso per tutte le pagine del dashboard.
 *
 * Desktop (lg+): sidebar fissa a sinistra (w-64) + contenuto a destra.
 * Mobile (<lg): header con hamburger menu che apre la Sidebar in un Sheet.
 *
 * Questo layout NON appare nell'URL grazie al Route Group (dashboard).
 */

import { useState } from "react";
import { Menu } from "lucide-react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* ── Sidebar desktop (fissa, visibile da lg in su) ── */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:bg-white dark:lg:bg-zinc-900">
        <Sidebar />
      </aside>

      {/* ── Contenuto principale ── */}
      <div className="flex flex-1 flex-col">
        {/* ── Header mobile (visibile sotto lg) ── */}
        <header className="flex h-14 items-center gap-3 border-b bg-white px-4 lg:hidden dark:bg-zinc-900">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon-sm">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <SheetTitle className="sr-only">Menu navigazione</SheetTitle>
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>
          <span className="text-sm font-semibold">ProFit AI Studio</span>
        </header>

        {/* ── Page content ── */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
