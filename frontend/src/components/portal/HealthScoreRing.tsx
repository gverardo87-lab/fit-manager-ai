"use client";

/**
 * HealthScoreRing — SVG ring gauge animato per Health Score (0-100).
 *
 * Colore shift: red (<40) → amber (40-69) → emerald (70-89) → teal (90+).
 * Animazione via CSS transition su strokeDashoffset.
 * Rispetta prefers-reduced-motion.
 */

import { useEffect, useRef, useState } from "react";

interface HealthScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

const SCORE_COLORS: Record<string, { stroke: string; text: string }> = {
  teal: {
    stroke: "oklch(0.55 0.15 170)",
    text: "text-teal-600 dark:text-teal-400",
  },
  emerald: {
    stroke: "oklch(0.55 0.15 155)",
    text: "text-emerald-600 dark:text-emerald-400",
  },
  amber: {
    stroke: "oklch(0.65 0.15 80)",
    text: "text-amber-600 dark:text-amber-400",
  },
  red: {
    stroke: "oklch(0.55 0.2 25)",
    text: "text-red-600 dark:text-red-400",
  },
};

function getColorKey(score: number): string {
  if (score >= 90) return "teal";
  if (score >= 70) return "emerald";
  if (score >= 40) return "amber";
  return "red";
}

export function HealthScoreRing({
  score,
  size = 96,
  strokeWidth = 8,
  className = "",
}: HealthScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(() => {
    if (typeof window === "undefined") return 0;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    return prefersReduced ? score : 0;
  });
  const mountedRef = useRef(false);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, animatedScore));
  const offset = circumference - (clampedScore / 100) * circumference;

  const colorKey = getColorKey(score);
  const colors = SCORE_COLORS[colorKey];

  useEffect(() => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) {
      // Score changes are handled via the callback below, not synchronously
      const timer = setTimeout(() => setAnimatedScore(score), 0);
      return () => clearTimeout(timer);
    }

    if (!mountedRef.current) {
      // Prima animazione: delay per page reveal
      mountedRef.current = true;
      const timer = setTimeout(() => setAnimatedScore(score), 300);
      return () => clearTimeout(timer);
    }

    const timer = setTimeout(() => setAnimatedScore(score), 0);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="motion-reduce:transition-none"
      >
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-zinc-200 dark:text-zinc-700"
        />
        {/* Score arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out motion-reduce:transition-none"
          style={{
            transformOrigin: "center",
            transform: "rotate(-90deg)",
          }}
        />
      </svg>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-2xl font-extrabold tabular-nums leading-none ${colors.text}`}>
          {Math.round(clampedScore)}
        </span>
      </div>
    </div>
  );
}
