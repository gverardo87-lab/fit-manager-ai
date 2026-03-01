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

import { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import { Sidebar } from "@/components/layout/Sidebar";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { AuthGuard } from "@/components/auth/AuthGuard";
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
  const mainRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const isPopRef = useRef(false);

  // Track back/forward navigation via popstate
  useEffect(() => {
    const handler = () => {
      isPopRef.current = true;
    };
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  // Save/restore scroll position for <main> container
  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    const timers: ReturnType<typeof setTimeout>[] = [];

    if (isPopRef.current) {
      // Back/forward navigation → restore saved position
      // Retry: content may still be loading (React Query cache hit is fast but async)
      const saved = sessionStorage.getItem(`scroll:${pathname}`);
      if (saved) {
        const target = parseInt(saved, 10);
        const tryRestore = () => {
          main.scrollTop = target;
        };
        requestAnimationFrame(tryRestore);
        timers.push(setTimeout(tryRestore, 100));
        timers.push(setTimeout(tryRestore, 300));
      }
      isPopRef.current = false;
    } else {
      // Forward navigation → scroll to top
      main.scrollTop = 0;
    }

    return () => {
      timers.forEach(clearTimeout);
      // Save scroll before leaving this page
      sessionStorage.setItem(`scroll:${pathname}`, String(main.scrollTop));
    };
  }, [pathname]);

  return (
    <AuthGuard>
    <CommandPalette />
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
        <main ref={mainRef} className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
    </AuthGuard>
  );
}
