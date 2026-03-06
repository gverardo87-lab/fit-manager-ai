// src/components/ui/logo.tsx
/**
 * LogoIcon — versione SVG stilizzata del logo FitManager AI Studio.
 *
 * Elementi chiave del logo originale:
 * - Spirale onda teal (salute, flusso, fitness)
 * - Grafico trend ascendente con nodi (gestione, crescita)
 * - Accento foglia (benessere naturale)
 *
 * Usa `currentColor` — eredita il colore dal parent.
 * Funziona da 20px (sidebar) a 200px+ (login hero).
 */

interface LogoIconProps {
  className?: string;
}

export function LogoIcon({ className }: LogoIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* ── Wave spiral — forma dominante del logo ── */}
      <path
        d="M3 20 C1 16, 1 10, 4 6 C7 2, 12 2, 14 5 C11 3, 7 4, 5 8 C3 12, 4 17, 8 19 Z"
        fill="currentColor"
        opacity="0.85"
      />
      {/* Inner spiral detail */}
      <path
        d="M7 14 C7 10, 10 8, 12 9"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        opacity="0.4"
      />
      {/* Leaf accent inside wave */}
      <path
        d="M8 11 C9 8, 12 8, 11 11 C10 11, 9 11.5, 8 11 Z"
        fill="currentColor"
        opacity="0.3"
      />

      {/* ── Ascending bar chart ── */}
      <rect x="14" y="15" width="2" height="5" rx="0.5" fill="currentColor" opacity="0.45" />
      <rect x="17.5" y="11" width="2" height="9" rx="0.5" fill="currentColor" opacity="0.6" />
      <rect x="21" y="7" width="2" height="13" rx="0.5" fill="currentColor" opacity="0.8" />

      {/* ── Trend line with peak dot ── */}
      <path
        d="M15 14 L18.5 10 L22 6"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="22" cy="6" r="1.2" fill="currentColor" />
    </svg>
  );
}
