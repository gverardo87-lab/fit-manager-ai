// src/app/(dashboard)/guida/page.tsx
"use client";

/**
 * Guida FitManager — Hub operativo.
 *
 * Struttura:
 * 1. Hero card con CTA "Lancia il tour guidato"
 * 2. Scorciatoie da tastiera
 * 3. FAQ reali con risposte actionable (Collapsible)
 * 4. Feature discovery cards
 */

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Brain,
  CheckCircle2,
  ChevronDown,
  Compass,
  FileDown,
  Keyboard,
  MessageCircleQuestion,
  Shield,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useGuideProgress } from "@/hooks/useGuideProgress";
import {
  GUIDE_FAQ,
  KEYBOARD_SHORTCUTS,
  FEATURE_CARDS,
  type FeatureCard,
} from "@/lib/guide-tours";

// ── Icon map per feature cards (evita import dinamico) ──

const FEATURE_ICON_MAP: Record<FeatureCard["iconName"], typeof Bot> = {
  bot: Bot,
  brain: Brain,
  shield: Shield,
  "file-down": FileDown,
};

// ── FAQ Item ──

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between gap-3 rounded-lg border border-border/70 px-4 py-3 text-left transition-colors hover:bg-muted/30"
        >
          <span className="text-sm font-medium">{question}</span>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="px-4 pb-1 pt-2 text-sm leading-relaxed text-muted-foreground">
          {answer}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

// ── Page ──

export default function GuidaPage() {
  const { isTourCompleted, resetProgress } = useGuideProgress();
  const tourDone = isTourCompleted("scopri-fitmanager");

  const launchTour = () => {
    // Reset progress se il tour era gia' completato, cosi' shouldShowOnboarding
    // non blocca il re-trigger (il layout ascolta il custom event direttamente)
    window.dispatchEvent(new Event("start-guide-tour"));
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
          <BookOpen className="h-5 w-5 text-teal-600 dark:text-teal-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Guida FitManager</h1>
          <p className="text-sm text-muted-foreground">
            Tour interattivo, scorciatoie e risposte operative.
          </p>
        </div>
      </div>

      {/* ── Hero: Tour guidato ── */}
      <Card data-guide="guida-hero" className="overflow-hidden border-primary/20">
        <div className="bg-gradient-to-br from-primary/5 via-primary/3 to-transparent">
          <CardHeader className="space-y-3">
            <div className="flex items-center gap-2">
              <Compass className="h-5 w-5 text-primary" />
              <CardTitle>Scopri l&apos;intero ciclo cliente</CardTitle>
              {tourDone && (
                <Badge
                  variant="outline"
                  className="gap-1 border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300"
                >
                  <CheckCircle2 className="h-3 w-3" />
                  Completato
                </Badge>
              )}
            </div>
            <CardDescription className="max-w-xl">
              Tour interattivo in 19 passi che ti guida attraverso l&apos;intero ciclo operativo:
              clienti, contratti, agenda, cassa, esercizi, schede allenamento, monitoraggio e backup.
              Il tour naviga automaticamente tra le pagine.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-3">
              <Button size="lg" className="gap-2" onClick={launchTour}>
                <Compass className="h-4.5 w-4.5" />
                {tourDone ? "Rifai il tour" : "Lancia il tour guidato"}
              </Button>
              {tourDone && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-muted-foreground"
                  onClick={resetProgress}
                >
                  Reset progresso
                </Button>
              )}
            </div>
          </CardContent>
        </div>
      </Card>

      {/* ── Scorciatoie da tastiera ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Keyboard className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">Scorciatoie da tastiera</h2>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {KEYBOARD_SHORTCUTS.map((shortcut) => (
            <div
              key={shortcut.label}
              className="flex items-center gap-3 rounded-lg border border-border/70 bg-card px-3 py-2.5"
            >
              <div className="flex items-center gap-1">
                {shortcut.keys.map((key) => (
                  <kbd
                    key={key}
                    className="inline-flex h-7 min-w-7 items-center justify-center rounded-md border bg-muted px-1.5 text-xs font-medium text-muted-foreground"
                  >
                    {key}
                  </kbd>
                ))}
              </div>
              <span className="text-sm text-muted-foreground">{shortcut.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <MessageCircleQuestion className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">Domande frequenti</h2>
        </div>
        <div className="space-y-2">
          {GUIDE_FAQ.map((faq) => (
            <FaqItem key={faq.question} question={faq.question} answer={faq.answer} />
          ))}
        </div>
      </section>

      {/* ── Feature Discovery ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">Scopri le funzionalita' avanzate</h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {FEATURE_CARDS.map((card) => {
            const Icon = FEATURE_ICON_MAP[card.iconName];
            return (
              <Card key={card.id} className="border-border/70 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
                <CardHeader className="space-y-2 pb-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <CardTitle className="text-sm">{card.title}</CardTitle>
                  </div>
                  <CardDescription className="text-xs">
                    {card.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button asChild variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
                    <Link href={card.href}>
                      Scopri
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
