/**
 * confetti.ts — Celebrazioni visive per momenti chiave del CRM
 *
 * Due livelli di intensità:
 * - celebrateRatePaid():       rata completamente saldata (burst centrale)
 * - celebrateContractSaldato(): contratto chiuso al 100% (cannoni laterali)
 *
 * Usa canvas-confetti (3KB). Chiamate fire-and-forget, zero await.
 * Colori: palette teal/emerald/violet allineata all'identità visiva.
 */

import type confettiLib from "canvas-confetti";

// Lazy import per non bloccare il bundle principale
let _confetti: typeof confettiLib | null = null;

async function getConfetti(): Promise<typeof confettiLib> {
  if (!_confetti) {
    const mod = await import("canvas-confetti");
    _confetti = mod.default;
  }
  return _confetti;
}

/** Palette colori allineata all'identità teal del prodotto */
const COLORS = {
  primary: ["#2dd4bf", "#14b8a6", "#0d9488"],   // teal
  success: ["#34d399", "#10b981", "#059669"],    // emerald
  accent:  ["#818cf8", "#60a5fa", "#a78bfa"],   // blue/violet
};

/**
 * Rata pagata completamente (SALDATA) — burst singolo dal basso.
 * Discreto ma visibile. Durata ~1.5s.
 */
export async function celebrateRatePaid(): Promise<void> {
  const confetti = await getConfetti();
  confetti({
    particleCount: 70,
    spread: 55,
    origin: { y: 0.75 },
    colors: [...COLORS.primary, ...COLORS.success],
    ticks: 180,
    gravity: 1.2,
    scalar: 0.9,
  });
}

/**
 * Contratto completamente saldato (chiuso) — cannoni da entrambi i lati.
 * Più drammatico, per un evento raro e significativo. Durata ~2.5s.
 */
export async function celebrateContractSaldato(): Promise<void> {
  const confetti = await getConfetti();

  // Cannone sinistro
  confetti({
    particleCount: 60,
    angle: 60,
    spread: 50,
    origin: { x: 0, y: 0.75 },
    colors: [...COLORS.primary, ...COLORS.success],
    ticks: 250,
    gravity: 1.0,
  });

  // Cannone destro (leggero ritardo per effetto a cascata)
  setTimeout(() => {
    confetti({
      particleCount: 60,
      angle: 120,
      spread: 50,
      origin: { x: 1, y: 0.75 },
      colors: [...COLORS.accent, ...COLORS.primary],
      ticks: 250,
      gravity: 1.0,
    });
  }, 150);
}
