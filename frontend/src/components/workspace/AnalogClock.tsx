"use client";

/**
 * AnalogClock — orologio analogico stile Apple Watch.
 *
 * Lancette ore/minuti, tick marks, dot secondi.
 * Aggiorna ogni 10s. Monocromatico, si adatta al tema.
 */

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const HOUR_TICKS = Array.from({ length: 12 }, (_, i) => i);

interface AnalogClockProps {
  className?: string;
}

export function AnalogClock({ className }: AnalogClockProps) {
  const [now, setNow] = useState(new Date(0));

  useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const hydrated = now.getTime() > 0;
  const hours = now.getHours() % 12;
  const minutes = now.getMinutes();

  const hourAngle = hours * 30 + minutes * 0.5;
  const minuteAngle = minutes * 6;

  return (
    <div className={cn("relative transition-opacity duration-500", hydrated ? "opacity-100" : "opacity-0", className)}>
      <svg viewBox="0 0 100 100" className="h-full w-full drop-shadow-lg" role="img" aria-label={hydrated ? `Orologio: ${hours === 0 ? 12 : hours}:${String(minutes).padStart(2, "0")}` : "Orologio"}>
        {/* Outer ring */}
        <circle
          cx="50" cy="50" r="48"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-primary/20"
        />

        {/* Glass face */}
        <circle
          cx="50" cy="50" r="46"
          fill="currentColor"
          className="text-background"
          opacity="0.85"
        />

        {/* Inner subtle ring */}
        <circle
          cx="50" cy="50" r="44"
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
          className="text-primary/10"
        />

        {/* Hour ticks */}
        {HOUR_TICKS.map((i) => {
          const angle = (i * 30 - 90) * (Math.PI / 180);
          const isQuarter = i % 3 === 0;
          const outerR = 42;
          const innerR = isQuarter ? 36 : 38.5;
          return (
            <line
              key={i}
              x1={50 + Math.cos(angle) * innerR}
              y1={50 + Math.sin(angle) * innerR}
              x2={50 + Math.cos(angle) * outerR}
              y2={50 + Math.sin(angle) * outerR}
              stroke="currentColor"
              strokeWidth={isQuarter ? "2.2" : "0.8"}
              strokeLinecap="round"
              className={isQuarter ? "text-foreground/70" : "text-foreground/25"}
            />
          );
        })}

        {/* Hour hand */}
        <line
          x1="50" y1="50"
          x2={50 + Math.cos((hourAngle - 90) * (Math.PI / 180)) * 24}
          y2={50 + Math.sin((hourAngle - 90) * (Math.PI / 180)) * 24}
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          className="text-foreground/80 transition-all duration-700 ease-out"
        />

        {/* Minute hand */}
        <line
          x1="50" y1="50"
          x2={50 + Math.cos((minuteAngle - 90) * (Math.PI / 180)) * 34}
          y2={50 + Math.sin((minuteAngle - 90) * (Math.PI / 180)) * 34}
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          className="text-foreground/60 transition-all duration-700 ease-out"
        />

        {/* Center dot */}
        <circle cx="50" cy="50" r="2.5" fill="currentColor" className="text-primary" />
        <circle cx="50" cy="50" r="1" fill="currentColor" className="text-primary-foreground" />
      </svg>
    </div>
  );
}
