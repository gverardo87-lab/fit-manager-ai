// src/components/ui/logo.tsx
/**
 * LogoIcon — SVG ispirato al brand CB Chinesiologa.
 *
 * Elementi: cuore stilizzato (passione, salute) + manubrio (fitness, forza).
 * Monocromatico `currentColor` — eredita il colore dal parent.
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
      {/* ── Heart outline — cuore stilizzato (richiamo logo CB) ── */}
      <path
        d="M12 21 C12 21, 3 15, 3 8.5 C3 5.4, 5.4 3, 8.5 3 C10.2 3, 11.7 3.8, 12 5 C12.3 3.8, 13.8 3, 15.5 3 C18.6 3, 21 5.4, 21 8.5 C21 15, 12 21, 12 21 Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.35"
      />

      {/* ── Dumbbell — manubrio orizzontale centrato ── */}
      {/* Left plate */}
      <rect x="5" y="10" width="2.5" height="5" rx="0.8" fill="currentColor" opacity="0.7" />
      {/* Right plate */}
      <rect x="16.5" y="10" width="2.5" height="5" rx="0.8" fill="currentColor" opacity="0.7" />
      {/* Bar */}
      <rect x="7.5" y="11.5" width="9" height="2" rx="0.6" fill="currentColor" opacity="0.55" />
      {/* Left grip cap */}
      <rect x="3.8" y="11" width="1.2" height="3" rx="0.5" fill="currentColor" opacity="0.5" />
      {/* Right grip cap */}
      <rect x="19" y="11" width="1.2" height="3" rx="0.5" fill="currentColor" opacity="0.5" />

      {/* ── Pulse beat — battito cardiaco sopra il manubrio ── */}
      <path
        d="M8 8.5 L10 8.5 L11 6.5 L12 10 L13 7 L14 8.5 L16 8.5"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.9"
      />
    </svg>
  );
}
