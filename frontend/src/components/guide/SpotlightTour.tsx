// ════════════════════════════════════════════════════════════
// SpotlightTour — Tour guidato con spotlight su elementi reali
//
// Overlay leggero che evidenzia un elemento alla volta con
// box-shadow cutout (singolo DOM element) e tooltip posizionato.
//
// Zero librerie esterne. CSS spotlight-cutout in globals.css.
// Portal in document.body (stesso pattern EventHoverCard).
// ════════════════════════════════════════════════════════════

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, ArrowRight, Compass, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { TourDefinition, TourStep } from "@/lib/guide-tours";

// ── Props ──

interface SpotlightTourProps {
  tour: TourDefinition;
  open: boolean;
  onComplete: () => void;
  onDismiss: () => void;
  /** Callback per navigare a una route (cross-page tour) */
  onNavigate?: (href: string) => void;
}

// ── Geometry helpers ──

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const PADDING = 8; // px around target
const GAP = 12;    // px between target and tooltip
const TOOLTIP_WIDTH = 360;
const TOOLTIP_WIDTH_MOBILE = 0; // full-width on mobile (calculated from viewport)

function getTargetRect(target: string): Rect | null {
  const el = document.querySelector<HTMLElement>(`[data-guide="${target}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {
    top: r.top - PADDING,
    left: r.left - PADDING,
    width: r.width + PADDING * 2,
    height: r.height + PADDING * 2,
  };
}

interface TooltipPosition {
  top: number;
  left: number;
  width: number;
}

function computeTooltipPosition(
  targetRect: Rect,
  placement: TourStep["placement"],
  isMobile: boolean,
): TooltipPosition {
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  // Mobile: full-width in basso
  if (isMobile) {
    return {
      top: vh - 220,
      left: 12,
      width: vw - 24,
    };
  }

  const tooltipW = Math.min(TOOLTIP_WIDTH, vw - 32);
  let top = 0;
  let left = 0;

  // Calcolo posizione base
  switch (placement) {
    case "bottom":
      top = targetRect.top + targetRect.height + GAP;
      left = targetRect.left + targetRect.width / 2 - tooltipW / 2;
      // Flip to top se non c'e' spazio
      if (top + 200 > vh) {
        top = targetRect.top - GAP - 200;
      }
      break;
    case "top":
      top = targetRect.top - GAP - 200;
      left = targetRect.left + targetRect.width / 2 - tooltipW / 2;
      // Flip to bottom
      if (top < 8) {
        top = targetRect.top + targetRect.height + GAP;
      }
      break;
    case "right":
      top = targetRect.top + targetRect.height / 2 - 100;
      left = targetRect.left + targetRect.width + GAP;
      // Flip to left
      if (left + tooltipW > vw - 8) {
        left = targetRect.left - GAP - tooltipW;
      }
      break;
    case "left":
      top = targetRect.top + targetRect.height / 2 - 100;
      left = targetRect.left - GAP - tooltipW;
      // Flip to right
      if (left < 8) {
        left = targetRect.left + targetRect.width + GAP;
      }
      break;
  }

  // Clamp entro il viewport
  left = Math.max(8, Math.min(left, vw - tooltipW - 8));
  top = Math.max(8, Math.min(top, vh - 220));

  return { top, left, width: tooltipW };
}

// ── Component ──

export function SpotlightTour({ tour, open, onComplete, onDismiss, onNavigate }: SpotlightTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<Rect | null>(null);
  const [tooltipPos, setTooltipPos] = useState<TooltipPosition | null>(null);
  const [visible, setVisible] = useState(false);
  const rafRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Filtra step per viewport
  const isMobile = typeof window !== "undefined" && window.innerWidth < 1024;
  const activeSteps = isMobile
    ? tour.steps.filter((s) => !s.desktopOnly)
    : tour.steps;

  const step = activeSteps[currentStep] as TourStep | undefined;
  const isLastStep = currentStep === activeSteps.length - 1;

  // ── Posizionamento ──

  const updatePosition = useCallback(() => {
    if (!step) return;
    const rect = getTargetRect(step.target);
    if (!rect) return;
    setTargetRect(rect);
    const isMobileNow = window.innerWidth < 640;
    setTooltipPos(computeTooltipPosition(rect, step.placement, isMobileNow));
  }, [step]);

  // ── Naviga + trova target con retry ──
  // Unico punto dove avviene la navigazione: garantisce che ogni step
  // navighi alla pagina giusta indipendentemente da come ci si arriva
  // (goNext, goBack, keyboard, skip automatico).

  useEffect(() => {
    if (!open || !step) {
      setVisible(false);
      return;
    }

    // Naviga se lo step lo richiede (no-op se gia' sulla pagina giusta)
    if (step.navigateTo && onNavigate) {
      onNavigate(step.navigateTo);
    }

    let attempts = 0;
    // Dopo navigazione serve piu' tempo per il mount della nuova pagina.
    // Per step same-page con target data-dependent (KPI, filtri), servono
    // comunque ~4s perche' i dati arrivano via React Query dopo il render.
    const maxAttempts = step.navigateTo ? 25 : 20;

    const tryFind = () => {
      const rect = getTargetRect(step.target);
      if (rect) {
        setTargetRect(rect);
        const isMobileNow = window.innerWidth < 640;
        setTooltipPos(computeTooltipPosition(rect, step.placement, isMobileNow));
        setVisible(true);
        return;
      }
      attempts++;
      if (attempts < maxAttempts) {
        retryTimerRef.current = setTimeout(tryFind, 200);
      } else {
        // Target non trovato — skip step
        if (!isLastStep) {
          setCurrentStep((prev) => prev + 1);
        } else {
          onComplete();
        }
      }
    };

    tryFind();

    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, [open, step, isLastStep, onComplete, updatePosition, onNavigate]);

  // ── Resize / scroll reposition ──

  useEffect(() => {
    if (!open || !visible) return;

    const handleReposition = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(updatePosition);
    };

    window.addEventListener("resize", handleReposition, { passive: true });
    // Ascolta scroll sul main container (non window — h-screen layout)
    const mainEl = document.querySelector("main");
    mainEl?.addEventListener("scroll", handleReposition, { passive: true });

    return () => {
      window.removeEventListener("resize", handleReposition);
      mainEl?.removeEventListener("scroll", handleReposition);
      cancelAnimationFrame(rafRef.current);
    };
  }, [open, visible, updatePosition]);

  // ── Navigation handlers ──

  const goNext = useCallback(() => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  }, [isLastStep, onComplete]);

  const goBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  // ── Keyboard ──

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "Escape":
          e.preventDefault();
          onDismiss();
          break;
        case "ArrowRight":
        case "Enter":
          e.preventDefault();
          goNext();
          break;
        case "ArrowLeft":
          e.preventDefault();
          goBack();
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown, { capture: true });
    return () => window.removeEventListener("keydown", handleKeyDown, { capture: true });
  }, [open, goNext, goBack, onDismiss]);

  // ── Reset step on open ──

  useEffect(() => {
    if (open) {
      setCurrentStep(0);
      setVisible(false);
    }
  }, [open]);

  // ── Render ──

  if (!open || !visible || !targetRect || !tooltipPos || !step) return null;

  return createPortal(
    <>
      {/* ── Overlay click = dismiss ── */}
      <div
        className="fixed inset-0 z-[10000]"
        onClick={onDismiss}
        aria-hidden="true"
      />

      {/* ── Spotlight cutout ── */}
      <div
        className="spotlight-cutout"
        style={{
          top: targetRect.top,
          left: targetRect.left,
          width: targetRect.width,
          height: targetRect.height,
        }}
      />

      {/* ── Tooltip card ── */}
      <div
        className="fixed z-[10001] animate-in fade-in-0 zoom-in-95 duration-200"
        style={{
          top: tooltipPos.top,
          left: tooltipPos.left,
          width: tooltipPos.width,
        }}
        role="dialog"
        aria-label={`Tour: ${step.title}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rounded-xl border border-border bg-card p-4 shadow-2xl">
          {/* Header */}
          <div className="mb-3 flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                <Compass className="h-4 w-4 text-primary" />
              </div>
              <h3 className="text-sm font-semibold">{step.title}</h3>
            </div>
            <button
              type="button"
              onClick={onDismiss}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label="Chiudi tour"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Description */}
          <p className="mb-4 text-sm leading-relaxed text-muted-foreground">
            {step.description}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Passo {currentStep + 1} di {activeSteps.length}
            </span>
            <div className="flex items-center gap-2">
              {currentStep > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={goBack}
                  className="h-8 gap-1 text-xs"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Indietro
                </Button>
              )}
              <Button
                size="sm"
                onClick={goNext}
                className="h-8 gap-1 text-xs"
              >
                {isLastStep ? "Fine" : "Avanti"}
                {!isLastStep && <ArrowRight className="h-3.5 w-3.5" />}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>,
    document.body,
  );
}
