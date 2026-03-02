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
  const prevPathnameRef = useRef(pathname);
  const scrollTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  // Track back/forward navigation via popstate + set sessionStorage flag for pages
  useEffect(() => {
    const handler = () => {
      isPopRef.current = true;
      try { sessionStorage.setItem("nav:back", "1"); } catch { /* ignore */ }
    };
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  // Continuously save scroll position via scroll event (always up-to-date for back-nav)
  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    let rafId: number | null = null;
    const handleScroll = () => {
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        sessionStorage.setItem(`scroll:${pathname}`, String(main.scrollTop));
        rafId = null;
      });
    };

    main.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      main.removeEventListener("scroll", handleScroll);
      if (rafId !== null) cancelAnimationFrame(rafId);
    };
  }, [pathname]);

  // Restore scroll on back-nav, reset on forward-nav
  // prevPathnameRef guard prevents React Strict Mode double-invocation from scrolling to 0
  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    // Strict Mode guard: skip if we already processed this pathname
    if (prevPathnameRef.current === pathname) return;
    prevPathnameRef.current = pathname;

    // Clear any previous scroll timers
    scrollTimersRef.current.forEach(clearTimeout);
    scrollTimersRef.current = [];

    if (isPopRef.current) {
      isPopRef.current = false;
      // Back/forward navigation → restore saved position with retries
      const saved = sessionStorage.getItem(`scroll:${pathname}`);
      if (saved) {
        const target = parseInt(saved, 10);
        const tryRestore = () => { main.scrollTop = target; };
        // Multiple retries at increasing intervals (waits for React Query async data)
        [0, 50, 100, 250, 500, 1000, 2000].forEach(delay => {
          scrollTimersRef.current.push(setTimeout(tryRestore, delay));
        });
      }
      // Clear nav:back flag (pages have already read it in their useState init)
      try { sessionStorage.removeItem("nav:back"); } catch { /* ignore */ }
    } else {
      // Forward navigation → scroll to top
      main.scrollTop = 0;
    }
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
