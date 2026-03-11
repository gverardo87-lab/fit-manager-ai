"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  HeartPulse,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { SessionPrepItem } from "@/types/api";

/* ── Time helpers ── */

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

function minutesUntil(isoDate: string): number | null {
  const target = new Date(isoDate);
  if (Number.isNaN(target.getTime())) return null;
  return Math.round((target.getTime() - Date.now()) / 60_000);
}

function formatCountdown(mins: number): string {
  if (mins <= 0) return "In corso";
  if (mins < 60) return `tra ${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `tra ${h}h ${m}m` : `tra ${h}h`;
}

/* ── Conic ReadinessRing (OLED-feel) ── */

function ReadinessRing({ score, size = 48 }: { score: number; size?: number }) {
  const strokeWidth = 3.5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const ratio = Math.min(score / 100, 1);
  const offset = circumference - ratio * circumference;

  const hue = score >= 80 ? 155 : score >= 50 ? 85 : 25;
  const chroma = score >= 80 ? 0.17 : score >= 50 ? 0.15 : 0.20;
  const lightness = score >= 80 ? 0.72 : score >= 50 ? 0.75 : 0.65;
  const strokeColor = `oklch(${lightness} ${chroma} ${hue})`;
  const conicAngle = ratio * 360;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Conic gradient glow (OLED) */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `conic-gradient(from -90deg, oklch(${lightness} ${chroma * 0.8} ${hue}) 0deg, oklch(${lightness + 0.1} ${chroma * 0.6} ${hue}) ${conicAngle * 0.5}deg, oklch(${lightness} ${chroma * 0.8} ${hue}) ${conicAngle}deg, transparent ${conicAngle}deg)`,
          mask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth}px, #000 ${radius - strokeWidth}px ${radius + strokeWidth}px, transparent ${radius + strokeWidth}px)`,
          WebkitMask: `radial-gradient(farthest-side, transparent ${radius - strokeWidth}px, #000 ${radius - strokeWidth}px ${radius + strokeWidth}px, transparent ${radius + strokeWidth}px)`,
          opacity: 0.25,
        }}
      />
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="rgba(0,0,0,0.05)" strokeWidth={strokeWidth}
          className="dark:stroke-white/[0.06]"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={strokeColor}
          strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
          style={{ transformOrigin: "center", transform: "rotate(-90deg)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[13px] font-extrabold tabular-nums text-stone-800 dark:text-zinc-100">
          {score}
        </span>
      </div>
    </div>
  );
}

/* ── Health dots ── */

function HealthDots({ checks }: { checks: SessionPrepItem["health_checks"] }) {
  if (checks.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5">
      {checks.map((check) => {
        const Icon = check.status === "ok" ? CheckCircle2 : XCircle;
        const color = check.status === "ok"
          ? "text-emerald-500 dark:text-emerald-400"
          : check.status === "warning"
            ? "text-amber-500 dark:text-amber-400"
            : "text-red-500 dark:text-red-400";
        return (
          <div key={check.domain} className="group/dot relative">
            <Icon className={cn("h-3.5 w-3.5", color)} />
            <div className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-stone-900 px-2.5 py-1 text-[10px] font-medium text-white opacity-0 shadow-lg transition-opacity group-hover/dot:opacity-100 dark:bg-zinc-100 dark:text-stone-900">
              {check.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Main component ── */

interface OggiNextSessionProps {
  session: SessionPrepItem;
  className?: string;
}

export function OggiNextSession({ session, className }: OggiNextSessionProps) {
  const [mins, setMins] = useState(() => minutesUntil(session.starts_at));

  useEffect(() => {
    const id = window.setInterval(() => setMins(minutesUntil(session.starts_at)), 15_000);
    return () => window.clearInterval(id);
  }, [session.starts_at]);

  const timeLabel = TIME_FMT.format(new Date(session.starts_at));
  const countdownLabel = mins !== null ? formatCountdown(mins) : null;
  const isImminent = mins !== null && mins <= 15 && mins > 0;
  const isOngoing = mins !== null && mins <= 0;

  const alertCount = session.clinical_alerts.length;
  const issueCount = session.health_checks.filter((c) => c.status !== "ok").length;
  const creditsLabel = session.contract_credits_remaining !== null && session.contract_credits_total !== null
    ? `${session.contract_credits_remaining}/${session.contract_credits_total}`
    : null;

  // State-based glow class
  const glowClass = isOngoing
    ? "oggi-glow-teal"
    : isImminent
      ? "oggi-glow-amber"
      : alertCount > 0
        ? "oggi-glow-red"
        : "oggi-glow-neutral";

  return (
    <div
      className={cn(
        "oggi-lift group relative overflow-hidden rounded-2xl",
        glowClass,
        className,
      )}
    >
      {/* Glass border — 0.5px, semantic aura via glow class */}
      <div
        className="absolute inset-0 rounded-2xl"
        style={{
          border: isOngoing
            ? "0.5px solid oklch(0.65 0.12 170 / 0.15)"
            : isImminent
              ? "0.5px solid oklch(0.75 0.12 70 / 0.12)"
              : "0.5px solid oklch(0.80 0.01 200 / 0.10)",
        }}
      />

      {/* Luminosity-based background — +2% L from page bg */}
      <div
        className="absolute inset-0 rounded-2xl"
        style={{
          background: isOngoing
            ? "linear-gradient(135deg, oklch(0.97 0.012 170 / 0.4) 0%, oklch(0.99 0.004 170 / 0.2) 100%)"
            : isImminent
              ? "linear-gradient(135deg, oklch(0.97 0.010 70 / 0.3) 0%, oklch(0.99 0.004 70 / 0.15) 100%)"
              : "linear-gradient(135deg, oklch(0.995 0.003 200 / 0.4) 0%, oklch(0.99 0.002 200 / 0.25) 100%)",
        }}
      />
      <div
        className="absolute inset-0 hidden rounded-2xl dark:block"
        style={{
          background: isOngoing
            ? "linear-gradient(135deg, oklch(0.20 0.03 170 / 0.5) 0%, oklch(0.16 0.02 170 / 0.3) 100%)"
            : isImminent
              ? "linear-gradient(135deg, oklch(0.20 0.03 70 / 0.4) 0%, oklch(0.16 0.02 70 / 0.25) 100%)"
              : "linear-gradient(135deg, oklch(0.18 0.008 200 / 0.4) 0%, oklch(0.15 0.004 200 / 0.25) 100%)",
        }}
      />

      <div className="relative flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:gap-5">
        {/* Time block */}
        <div className="flex shrink-0 items-center gap-3 sm:flex-col sm:items-center sm:gap-1.5">
          <div
            className="flex items-center gap-2 rounded-xl px-3.5 py-2.5 backdrop-blur-sm"
            style={{
              border: "0.5px solid oklch(0.80 0.01 200 / 0.10)",
              background: isOngoing
                ? "oklch(0.62 0.15 150 / 0.08)"
                : isImminent
                  ? "oklch(0.75 0.12 70 / 0.08)"
                  : "oklch(0.97 0.005 200 / 0.5)",
            }}
          >
            <Clock className={cn(
              "h-4 w-4",
              isOngoing ? "text-teal-600 dark:text-teal-400" : isImminent ? "text-amber-600 dark:text-amber-400" : "text-stone-400 dark:text-zinc-500",
            )} />
            <span className="text-xl font-extrabold tabular-nums tracking-tight text-stone-900 dark:text-zinc-50">
              {timeLabel}
            </span>
          </div>
          {countdownLabel && (
            <span className={cn(
              "text-[11px] font-bold tabular-nums",
              isOngoing
                ? "text-teal-600 dark:text-teal-400"
                : isImminent
                  ? "oggi-pulse-dot text-amber-600 dark:text-amber-400"
                  : "text-stone-400 dark:text-zinc-500",
            )}>
              {countdownLabel}
            </span>
          )}
        </div>

        {/* Client info */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <h3 className="text-lg font-extrabold leading-tight tracking-tight text-stone-900 dark:text-zinc-50">
              {session.client_name ?? session.event_title ?? session.category}
            </h3>
            {session.is_new_client && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                <Sparkles className="h-3 w-3" /> Nuovo
              </span>
            )}
          </div>

          {/* Meta row */}
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[12px] text-stone-500 dark:text-zinc-400">
            {session.active_plan_name && (
              <span className="flex items-center gap-1">
                <HeartPulse className="h-3.5 w-3.5" />
                {session.active_plan_name}
              </span>
            )}
            {creditsLabel && <span>{creditsLabel} crediti</span>}
            {session.days_since_last_session !== null && session.days_since_last_session > 0 && (
              <span>
                Ultimo {session.days_since_last_session === 1 ? "ieri" : `${session.days_since_last_session}g fa`}
              </span>
            )}
          </div>

          {/* Health + alerts row */}
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {session.readiness_score !== null && (
              <ReadinessRing score={session.readiness_score} />
            )}
            <HealthDots checks={session.health_checks} />
            {alertCount > 0 && (
              <div className="flex items-center gap-1.5 rounded-full bg-red-500/10 px-2.5 py-1 text-[10px] font-bold text-red-700 backdrop-blur-sm dark:bg-red-400/10 dark:text-red-300">
                <ShieldAlert className="h-3 w-3" />
                {alertCount} alert
              </div>
            )}
            {issueCount > 0 && alertCount === 0 && (
              <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                {issueCount} {issueCount === 1 ? "check aperto" : "check aperti"}
              </span>
            )}
          </div>
        </div>

        {/* CTA */}
        {session.client_id && (
          <div className="flex shrink-0 items-center">
            <Link
              href={`/clienti/${session.client_id}?from=oggi`}
              className="inline-flex items-center gap-1.5 rounded-full px-5 py-2.5 text-[13px] font-bold backdrop-blur-sm transition-all duration-300"
              style={{
                border: "0.5px solid oklch(0.65 0.12 170 / 0.20)",
                background: isOngoing || isImminent
                  ? "oklch(0.65 0.12 170 / 0.12)"
                  : "oklch(0.97 0.005 200 / 0.5)",
                color: isOngoing || isImminent
                  ? "oklch(0.40 0.10 170)"
                  : "oklch(0.35 0.02 200)",
              }}
            >
              Prepara
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
