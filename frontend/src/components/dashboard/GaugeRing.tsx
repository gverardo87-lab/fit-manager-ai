"use client";

/**
 * GaugeRing — Mini SVG ring gauge per la CommandStrip dashboard.
 *
 * Piu' leggero di HealthScoreRing: nessun mount delay, label integrata.
 */

interface GaugeRingProps {
  value: number;
  max: number;
  label: string;
  suffix?: string;
  size?: number;
  strokeWidth?: number;
  color?: string;
  className?: string;
}

export function GaugeRing({
  value,
  max,
  label,
  suffix,
  size = 56,
  strokeWidth = 5,
  color = "oklch(0.85 0.12 170)",
  className = "",
}: GaugeRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(max, value));
  const ratio = max > 0 ? clamped / max : 0;
  const offset = circumference - ratio * circumference;

  return (
    <div className={`flex flex-col items-center gap-1 ${className}`}>
      <div className="relative">
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
            stroke="rgba(255,255,255,0.15)"
            strokeWidth={strokeWidth}
          />
          {/* Value arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
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
        {/* Center value */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-extrabold tabular-nums text-white leading-none">
            {Math.round(clamped)}{suffix ?? ""}
          </span>
        </div>
      </div>
      <span className="text-[9px] font-semibold uppercase tracking-wider text-white/70">
        {label}
      </span>
    </div>
  );
}
