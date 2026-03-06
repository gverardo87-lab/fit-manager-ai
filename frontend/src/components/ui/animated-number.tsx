"use client";

/**
 * AnimatedNumber — KPI counter con animazione fluida
 *
 * Anima da 0 → valore al mount, e da vecchio → nuovo valore ad ogni cambio.
 * Usa requestAnimationFrame + ease-out-cubic. Zero dipendenze esterne.
 *
 * Uso:
 *   <AnimatedNumber value={1234.56} format="currency" />
 *   <AnimatedNumber value={42} format="number" />
 */

import { useEffect, useRef, useState } from "react";
import { formatCurrency } from "@/lib/format";

interface AnimatedNumberProps {
  value: number;
  format?: "number" | "currency";
  /** Durata animazione in ms. Default 800. */
  duration?: number;
  className?: string;
}

/** Decelerazione cubica — parte veloce, finisce morbida */
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export function AnimatedNumber({
  value,
  format = "number",
  duration = 800,
  className,
}: AnimatedNumberProps) {
  // Valore corrente mostrato (interpolato durante animazione)
  const [displayed, setDisplayed] = useState(0);

  // Ref per evitare stale closure nel loop rAF
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const startValueRef = useRef(0);
  const prevDisplayedRef = useRef(0);

  useEffect(() => {
    // Cancella animazione precedente se ancora in corso
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }

    // Parti dal valore attualmente mostrato (non da 0) per transizioni mid-flight
    startValueRef.current = prevDisplayedRef.current;
    startTimeRef.current = null;
    const target = value;

    // Ottimizzazione: se delta è trascurabile, aggiorna direttamente
    if (Math.abs(target - startValueRef.current) < 0.01) {
      prevDisplayedRef.current = target;
      rafRef.current = requestAnimationFrame(() => {
        setDisplayed(target);
        rafRef.current = null;
      });
      return;
    }

    function animate(now: number) {
      if (startTimeRef.current === null) startTimeRef.current = now;

      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(progress);
      const current = startValueRef.current + (target - startValueRef.current) * eased;

      prevDisplayedRef.current = current;
      setDisplayed(current);

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        // Snap al valore esatto a fine animazione
        prevDisplayedRef.current = target;
        setDisplayed(target);
        rafRef.current = null;
      }
    }

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [value, duration]);

  // Formattazione: currency usa 2 decimali, number arrotonda all'intero
  const formatted =
    format === "currency"
      ? formatCurrency(displayed)
      : Math.round(displayed).toLocaleString("it-IT");

  return <span className={className}>{formatted}</span>;
}
