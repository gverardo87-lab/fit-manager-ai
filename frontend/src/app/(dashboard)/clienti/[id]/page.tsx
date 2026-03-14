// src/app/(dashboard)/clienti/[id]/page.tsx
"use client";

/**
 * Profilo Cliente — Hub Operativo.
 *
 * Layout:
 * - ProfileHeader (persistente): avatar, nome, contatti, stato, modifica
 * - OnboardingChecklist: hero CTA + stepper 5 step (solo se profilo incompleto)
 * - ProfileKpi: 4 card KPI
 * - Tabs: Panoramica (Journey Hub) | Contratti | Sessioni | Movimenti | Schede
 *   con dot di completamento sui tab label
 */

import { use, useState, useCallback, useMemo, useRef, useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  FileText, Calendar, Wallet, User,
  ClipboardList, UtensilsCrossed,
} from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { AvatarHero } from "@/components/clients/AvatarHero";
import { ClientSheet } from "@/components/clients/ClientSheet";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { TemplateSelector } from "@/components/workouts/TemplateSelector";
import { OnboardingChecklist } from "@/components/clients/profile/OnboardingChecklist";
import { PanoramicaTab } from "@/components/clients/profile/PanoramicaTab";
import { ContrattiTab } from "@/components/clients/profile/ContrattiTab";
import { SessioniTab } from "@/components/clients/profile/SessioniTab";
import { MovimentiTab } from "@/components/clients/profile/MovimentiTab";
import { SchedeTab } from "@/components/clients/profile/SchedeTab";
import { NutrizioneTab } from "@/components/clients/profile/NutrizioneTab";
import { ProfileSkeleton, NotFoundState } from "@/components/clients/profile/ProfileShared";

import { useClient } from "@/hooks/useClients";
import { useClientContracts } from "@/hooks/useContracts";
import { useClientEvents } from "@/hooks/useAgenda";
import { useClientReadiness, computeOnboardingSteps } from "@/hooks/useClientReadiness";
import { useNutritionPlans } from "@/hooks/useNutrition";
import { useClientAvatar } from "@/hooks/useWorkspace";
import { resolveBackNavigation } from "@/lib/url-state";

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function ClientProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);

  const { data: client, isLoading } = useClient(clientId);
  const { data: avatar, isLoading: avatarLoading } = useClientAvatar(clientId);
  const { readiness } = useClientReadiness(clientId);
  const { data: contractsData } = useClientContracts(clientId);
  const { data: eventsData } = useClientEvents(clientId);
  const { data: nutritionPlans } = useNutritionPlans(clientId);

  const [sheetOpen, setSheetOpen] = useState(false);
  const [contractSheetOpen, setContractSheetOpen] = useState(false);
  const [templateSelectorOpen, setTemplateSelectorOpen] = useState(false);
  const autoOpenSchedaConsumedRef = useRef(false);

  // ── URL-backed tab state ──
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const activeTab = searchParams.get("tab") ?? "panoramica";
  const shouldAutoOpenScheda = searchParams.get("startScheda") === "1";
  const rawReturnTo = searchParams.get("returnTo");
  const fromParam = searchParams.get("from");
  const returnTo = rawReturnTo && rawReturnTo.startsWith("/") && !rawReturnTo.startsWith("//") ? rawReturnTo : null;
  const backNav = resolveBackNavigation(fromParam, { href: "/clienti", label: "Torna ai clienti" });
  const backHref = returnTo ?? backNav.href;
  const backLabel = returnTo?.startsWith("/rinnovi-incassi")
    ? "Torna a Rinnovi & Incassi"
    : backNav.label;

  const handleTabChange = useCallback((value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "panoramica") params.delete("tab");
    else params.set("tab", value);
    const qs = params.toString();
    router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
  }, [searchParams, pathname, router]);

  // Auto-open scheda template selector
  useEffect(() => {
    if (!shouldAutoOpenScheda || autoOpenSchedaConsumedRef.current) return;
    autoOpenSchedaConsumedRef.current = true;
    const params = new URLSearchParams(searchParams.toString());
    params.delete("startScheda");
    const qs = params.toString();
    router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    const rafId = requestAnimationFrame(() => setTemplateSelectorOpen(true));
    return () => cancelAnimationFrame(rafId);
  }, [shouldAutoOpenScheda, searchParams, router, pathname]);

  // Onboarding steps from real data — contratto opens sheet inline
  const onboardingSteps = useMemo(() => {
    const steps = computeOnboardingSteps(clientId, readiness, {
      hasContracts: (contractsData?.items?.length ?? 0) > 0,
      hasEvents: (eventsData?.items?.length ?? 0) > 0,
    });
    // Contratto step: apre la ContractSheet precompilata invece di navigare
    const contrattoStep = steps.find((s) => s.key === "contratto");
    if (contrattoStep && !contrattoStep.completed) {
      contrattoStep.onAction = () => setContractSheetOpen(true);
    }
    return steps;
  }, [clientId, readiness, contractsData, eventsData]);

  // Tab completion dots
  const tabComplete = useMemo(() => ({
    contratti: (contractsData?.items?.length ?? 0) > 0,
    sessioni: (eventsData?.items?.length ?? 0) > 0,
    schede: readiness?.has_workout_plan ?? false,
    nutrizione: (nutritionPlans ?? []).some((p) => p.attivo),
  }), [contractsData, eventsData, readiness, nutritionPlans]);

  if (isLoading) return <ProfileSkeleton />;
  if (!client) return <NotFoundState />;

  return (
    <div className="space-y-4">
      <AvatarHero
        client={client}
        avatar={avatar ?? null}
        isLoading={avatarLoading}
        onEdit={() => setSheetOpen(true)}
        onTabChange={handleTabChange}
        backHref={backHref}
        backLabel={backLabel}
      />

      {/* Onboarding Checklist — hero CTA + stepper (solo se profilo incompleto) */}
      <OnboardingChecklist steps={onboardingSteps} />

      {/* Tabs con completion dots */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="w-full overflow-x-auto">
          <TabsTrigger value="panoramica">
            <User className="mr-2 h-4 w-4" />
            Panoramica
          </TabsTrigger>
          <TabsTrigger value="contratti">
            <FileText className="mr-2 h-4 w-4" />
            Contratti
            {tabComplete.contratti && <CompletionDot />}
          </TabsTrigger>
          <TabsTrigger value="sessioni">
            <Calendar className="mr-2 h-4 w-4" />
            Sessioni
            {tabComplete.sessioni && <CompletionDot />}
          </TabsTrigger>
          <TabsTrigger value="movimenti">
            <Wallet className="mr-2 h-4 w-4" />
            Movimenti
          </TabsTrigger>
          <TabsTrigger value="schede">
            <ClipboardList className="mr-2 h-4 w-4" />
            Schede
            {tabComplete.schede && <CompletionDot />}
          </TabsTrigger>
          <TabsTrigger value="nutrizione">
            <UtensilsCrossed className="mr-2 h-4 w-4" />
            Nutrizione
            {tabComplete.nutrizione && <CompletionDot />}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="panoramica" className="mt-4">
          <PanoramicaTab
            client={client}
            clientId={clientId}
            readiness={readiness}
            hasContracts={(contractsData?.items?.length ?? 0) > 0}
            hasEvents={(eventsData?.items?.length ?? 0) > 0}
            onTabChange={handleTabChange}
          />
        </TabsContent>
        <TabsContent value="contratti" className="mt-4">
          <ContrattiTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="sessioni" className="mt-4">
          <SessioniTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="movimenti" className="mt-4">
          <MovimentiTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="schede" className="mt-4">
          <SchedeTab clientId={clientId} onNewScheda={() => setTemplateSelectorOpen(true)} fromContext={searchParams.get("from") ?? undefined} />
        </TabsContent>
        <TabsContent value="nutrizione" className="mt-4">
          <NutrizioneTab clientId={clientId} />
        </TabsContent>
      </Tabs>

      <TemplateSelector
        open={templateSelectorOpen}
        onOpenChange={setTemplateSelectorOpen}
        clientId={clientId}
        fromContext={searchParams.get("from") ?? undefined}
      />
      <ClientSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        client={client}
      />
      <ContractSheet
        open={contractSheetOpen}
        onOpenChange={setContractSheetOpen}
        defaultClientId={clientId}
      />
    </div>
  );
}

/** Dot verde accanto al label tab — indica che il tab ha contenuto. */
function CompletionDot() {
  return (
    <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
  );
}
