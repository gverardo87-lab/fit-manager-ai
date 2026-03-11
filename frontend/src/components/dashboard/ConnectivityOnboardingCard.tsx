"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Globe, Router, X } from "lucide-react";

import { useConnectivityStatus } from "@/hooks/useConnectivityStatus";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getConnectivityOnboardingPrompt } from "@/components/dashboard/connectivity-onboarding";

const STORAGE_KEY = "fitmanager.connectivity.onboarding.dismissed.v1";
const SETTINGS_HREF = "/impostazioni?from=dashboard#connettivita";

export function ConnectivityOnboardingCard() {
  const { data, isLoading, isError } = useConnectivityStatus();
  const [dismissedPromptId, setDismissedPromptId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });

  const prompt = useMemo(() => {
    if (!data) return null;
    return getConnectivityOnboardingPrompt(data.profile);
  }, [data]);

  if (isLoading) {
    return <Skeleton className="h-28 w-full rounded-2xl" />;
  }

  if (isError || !data || !prompt || dismissedPromptId === prompt.id) {
    return null;
  }

  const Icon = prompt.id === "configure-public-portal" ? Globe : Router;
  const profileLabel =
    data.profile === "trusted_devices" ? "Dispositivi fidati" : "Solo locale";

  const handleDismiss = () => {
    setDismissedPromptId(prompt.id);
    try {
      window.localStorage.setItem(STORAGE_KEY, prompt.id);
    } catch {
      // Best effort: il prompt resta dismissibile anche se localStorage fallisce.
    }
  };

  return (
    <div className="rounded-2xl border border-teal-200/70 bg-gradient-to-br from-teal-50 via-background to-teal-100/40 p-4 shadow-sm dark:border-teal-900/50 dark:from-teal-950/30 dark:to-zinc-950">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300">
            <Icon className="h-5 w-5" />
          </div>
          <div className="space-y-2">
            <p className="text-sm font-semibold text-foreground">{prompt.title}</p>
            <p className="text-sm text-muted-foreground">{prompt.description}</p>
            <p className="text-xs text-muted-foreground">
              Stato attuale:{" "}
              <span className="font-medium text-foreground">{profileLabel}</span>
              {data.tailscale_dns_name ? ` - nodo ${data.tailscale_dns_name}` : ""}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Button asChild size="sm">
            <Link href={SETTINGS_HREF}>{prompt.ctaLabel}</Link>
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDismiss}>
            <X className="mr-2 h-4 w-4" />
            Non ora
          </Button>
        </div>
      </div>
    </div>
  );
}
