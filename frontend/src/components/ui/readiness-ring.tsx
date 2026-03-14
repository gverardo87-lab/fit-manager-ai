// src/components/ui/readiness-ring.tsx
/**
 * Circular progress ring for readiness score (0-100).
 * oklch color scale: green >= 80, yellow >= 50, red < 50.
 */

interface ReadinessRingProps {
  score: number;
  size?: number;
}

export function ReadinessRing({ score, size = 54 }: ReadinessRingProps) {
  const sw = 3.5;
  const r = (size - sw) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - Math.min(score / 100, 1) * circ;
  const hue = score >= 80 ? 155 : score >= 50 ? 85 : 25;
  const chroma = score >= 80 ? 0.17 : 0.18;
  const l = score >= 80 ? 0.72 : score >= 50 ? 0.73 : 0.65;

  const readinessLabel = score >= 80 ? "pronto" : score >= 50 ? "da verificare" : "critico";

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`Prontezza: ${score}% — ${readinessLabel}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth={sw} className="dark:stroke-white/[0.06]" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={`oklch(${l} ${chroma} ${hue})`}
          strokeWidth={sw} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[12px] font-extrabold tabular-nums text-foreground">{score}</span>
      </div>
    </div>
  );
}
