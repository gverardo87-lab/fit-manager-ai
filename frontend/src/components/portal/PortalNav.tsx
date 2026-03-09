"use client";

/**
 * PortalNav — Barra anchor sticky con scrollspy per sezioni portale.
 */

import { useEffect, useRef, useState } from "react";
import { User, Target, Activity, Dumbbell, Scale, TrendingUp, Ruler, ClipboardList } from "lucide-react";

const SECTIONS = [
  { id: "panoramica", label: "Panoramica", icon: User },
  { id: "obiettivi", label: "Obiettivi", icon: Target },
  { id: "misurazioni", label: "Misurazioni", icon: Activity },
  { id: "programma", label: "Programma", icon: Dumbbell },
  { id: "composizione", label: "Composizione", icon: Scale },
  { id: "progressi", label: "Progressi", icon: TrendingUp },
  { id: "simmetria", label: "Simmetria", icon: Ruler },
  { id: "anamnesi", label: "Anamnesi", icon: ClipboardList },
] as const;

export function PortalNav() {
  const [activeSection, setActiveSection] = useState<string>("");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    // Scrollspy via IntersectionObserver
    const entries = new Map<string, IntersectionObserverEntry>();

    observerRef.current = new IntersectionObserver(
      (observedEntries) => {
        for (const entry of observedEntries) {
          entries.set(entry.target.id, entry);
        }
        // Trova la sezione piu' visibile (ratio piu' alto)
        let best: string | null = null;
        let bestRatio = 0;
        for (const [id, entry] of entries) {
          if (entry.isIntersecting && entry.intersectionRatio > bestRatio) {
            bestRatio = entry.intersectionRatio;
            best = id;
          }
        }
        // Fallback: la prima visibile dall'alto
        if (!best) {
          for (const section of SECTIONS) {
            const e = entries.get(section.id);
            if (e?.isIntersecting) {
              best = section.id;
              break;
            }
          }
        }
        if (best) setActiveSection(best);
      },
      { rootMargin: "-80px 0px -50% 0px", threshold: [0, 0.25, 0.5] },
    );

    for (const section of SECTIONS) {
      const el = document.getElementById(section.id);
      if (el) observerRef.current.observe(el);
    }

    return () => observerRef.current?.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="sticky top-0 z-20 -mx-1 overflow-x-auto rounded-lg border bg-white/80 px-1 py-1.5 shadow-sm backdrop-blur-sm dark:bg-zinc-900/80">
      <div className="flex items-center gap-1">
        {SECTIONS.map((section) => {
          const Icon = section.icon;
          const isActive = activeSection === section.id;
          return (
            <button
              key={section.id}
              type="button"
              onClick={() => scrollToSection(section.id)}
              className={`flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
                isActive
                  ? "bg-teal-100 text-teal-700 shadow-sm dark:bg-teal-900/30 dark:text-teal-300"
                  : "text-muted-foreground hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-800"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{section.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
