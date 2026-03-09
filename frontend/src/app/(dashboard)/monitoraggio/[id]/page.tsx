// src/app/(dashboard)/monitoraggio/[id]/page.tsx
"use client";

/**
 * Portale Clinico 360° del Chinesiologo.
 *
 * Pagina scrollabile singola con 6 sezioni cliniche + header con Health Score.
 * Orchestratore dati: 9 hook, 3 engine client-side, zero nuovi endpoint.
 *
 * Sezioni: Composizione | Cardiovascolare | Simmetria | Programma | Obiettivi | Anamnesi
 */

import { use, useMemo } from "react";
import { useSearchParams } from "next/navigation";

import { PortalHeader } from "@/components/portal/PortalHeader";
import { PortalNav } from "@/components/portal/PortalNav";
import { CompositionSection } from "@/components/portal/CompositionSection";
import { CardiovascularSection } from "@/components/portal/CardiovascularSection";
import { SymmetrySection } from "@/components/portal/SymmetrySection";
import { ProgramSection } from "@/components/portal/ProgramSection";
import { GoalsSection } from "@/components/portal/GoalsSection";
import { AnamnesiSection } from "@/components/portal/AnamnesiSection";
import { Skeleton } from "@/components/ui/skeleton";

import { useClient } from "@/hooks/useClients";
import { useClientMeasurements, useLatestMeasurement, useMetrics } from "@/hooks/useMeasurements";
import { useClientGoals } from "@/hooks/useGoals";
import { useClientWorkouts, useClientWorkoutLogs } from "@/hooks/useWorkouts";
import { useExerciseSafetyMap } from "@/hooks/useExercises";
import { useClinicalReadiness } from "@/hooks/useDashboard";

import { generateClinicalReport } from "@/lib/clinical-analysis";
import { analyzeCorrelations } from "@/lib/metric-correlations";
import { computeWeeklyRate } from "@/lib/measurement-analytics";
import { computeAge, classifyValue } from "@/lib/normative-ranges";
import { getLatestValue } from "@/lib/derived-metrics";
import { computeHealthScore } from "@/lib/health-score";
import { getProgramStatus, computeWeeks, computeCompliance } from "@/lib/workout-monitoring";
import { usePageReveal } from "@/lib/page-reveal";

// Metric IDs da clinical-analysis.ts
const ID_PESO = 1;
const ID_GRASSO_PCT = 3;
const ID_BMI = 5;

export default function MonitoraggioClientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);
  const searchParams = useSearchParams();
  const fromParam = searchParams.get("from");
  const { revealClass, revealStyle } = usePageReveal();

  // Context-aware back navigation
  const backNav = useMemo(() => {
    if (fromParam?.startsWith("clienti-")) {
      const cId = fromParam.replace("clienti-", "");
      return { href: `/clienti/${cId}`, label: "Profilo cliente" };
    }
    return undefined;
  }, [fromParam]);

  // Data loading — 9 hook
  const { data: client, isLoading: clientLoading } = useClient(clientId);
  const { data: measurementsData } = useClientMeasurements(clientId);
  const { data: latestMeasurement } = useLatestMeasurement(clientId);
  const { data: metricsData } = useMetrics();
  const { data: goalsData } = useClientGoals(clientId);
  const { data: workoutsData } = useClientWorkouts(clientId);
  const { data: workoutLogsData } = useClientWorkoutLogs(clientId);
  const { data: safetyData } = useExerciseSafetyMap(clientId);
  const { data: readinessData } = useClinicalReadiness();

  // Computed values
  const measurements = useMemo(() => measurementsData?.items ?? [], [measurementsData?.items]);
  const metrics = useMemo(() => metricsData ?? [], [metricsData]);
  const goals = useMemo(() => goalsData?.items ?? [], [goalsData?.items]);
  const workouts = useMemo(() => workoutsData?.items ?? [], [workoutsData?.items]);
  const workoutLogs = useMemo(() => workoutLogsData?.items ?? [], [workoutLogsData?.items]);

  const sesso = client?.sesso ?? null;
  const dataNascita = client?.data_nascita ?? null;

  const clinicalReport = useMemo(
    () => generateClinicalReport(measurements, sesso, dataNascita, goals),
    [measurements, sesso, dataNascita, goals],
  );

  const correlations = useMemo(
    () => analyzeCorrelations(measurements, sesso),
    [measurements, sesso],
  );

  const readinessItem = useMemo(
    () => readinessData?.items.find((item) => item.client_id === clientId) ?? null,
    [readinessData, clientId],
  );

  const anamnesiState = useMemo((): "missing" | "legacy" | "structured" => {
    if (readinessItem) return readinessItem.anamnesi_state;
    if (!client?.anamnesi) return "missing";
    try {
      const parsed = typeof client.anamnesi === "string"
        ? JSON.parse(client.anamnesi)
        : client.anamnesi;
      if (parsed && "data_compilazione" in parsed &&
          "obiettivo_principale" in parsed) {
        return "structured";
      }
      return "legacy";
    } catch {
      return "missing";
    }
  }, [client, readinessItem]);

  const activeProgram = useMemo(
    () => workouts.find((w) => getProgramStatus(w) === "attivo") ?? null,
    [workouts],
  );

  const compliancePct = useMemo(() => {
    if (!activeProgram?.data_inizio || !activeProgram?.data_fine) return null;
    const weeks = computeWeeks(activeProgram.data_inizio, activeProgram.data_fine);
    const sessionCount = activeProgram.sessioni?.length ?? activeProgram.sessioni_per_settimana;
    const planLogs = workoutLogs.filter((l) => l.id_scheda === activeProgram.id);
    const now = new Date();
    const pastWeeks = weeks.filter((w) => new Date(w.startDate) <= now);
    const expected = pastWeeks.length * sessionCount;
    if (expected === 0) return null;
    return Math.round(computeCompliance(expected, planLogs.length));
  }, [activeProgram, workoutLogs]);

  const pesoAttuale = getLatestValue(measurements, ID_PESO);
  const pesoRate = useMemo(() => computeWeeklyRate(measurements, ID_PESO), [measurements]);
  const grassoPct = getLatestValue(measurements, ID_GRASSO_PCT);
  const age = computeAge(dataNascita);

  const grassoClassifica = useMemo(() => {
    if (grassoPct === null) return null;
    return classifyValue(ID_GRASSO_PCT, grassoPct, sesso, age)?.label ?? null;
  }, [grassoPct, sesso, age]);

  const bmiValue = useMemo(() => {
    const bmi = clinicalReport.derived.metrics.find((m) => m.id === "bmi");
    return bmi ? Math.round(bmi.value * 10) / 10 : null;
  }, [clinicalReport]);

  const bmiClassifica = useMemo(() => {
    if (bmiValue === null) return null;
    return classifyValue(ID_BMI, bmiValue, sesso, age)?.label ?? null;
  }, [bmiValue, sesso, age]);

  const healthScore = useMemo(
    () =>
      computeHealthScore({
        composition: clinicalReport.composition,
        riskProfile: clinicalReport.riskProfile,
        symmetry: clinicalReport.symmetry,
        goals,
        workoutCompliance: compliancePct,
        anamnesiState,
        hasMeasurements: measurements.length > 0,
      }),
    [clinicalReport, goals, compliancePct, anamnesiState, measurements.length],
  );

  // Loading state
  if (clientLoading || !client) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-xl" />
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <div className={revealClass(0)} style={revealStyle(0)}>
        <PortalHeader
          client={client}
          healthScore={healthScore}
          composition={clinicalReport.composition}
          readinessItem={readinessItem}
          pesoAttuale={pesoAttuale}
          pesoRate={pesoRate}
          grassoPct={grassoPct}
          grassoClassifica={grassoClassifica}
          bmi={bmiValue}
          bmiClassifica={bmiClassifica}
          compliancePct={compliancePct}
          backHref={backNav?.href}
          backLabel={backNav?.label}
        />
      </div>

      <div className={revealClass(30)} style={revealStyle(30)}>
        <PortalNav />
      </div>

      <section id="composizione" className={revealClass(70)} style={revealStyle(70)}>
        <CompositionSection
          measurements={measurements}
          metrics={metrics}
          clinicalReport={clinicalReport}
          correlations={correlations}
          sesso={sesso}
          dataNascita={dataNascita}
          clientId={clientId}
          measurementFreshness={readinessItem?.measurement_freshness ?? null}
        />
      </section>

      <section id="cardiovascolare" className={revealClass(110)} style={revealStyle(110)}>
        <CardiovascularSection
          measurements={measurements}
          metrics={metrics}
          riskProfile={clinicalReport.riskProfile}
          sesso={sesso}
          dataNascita={dataNascita}
          clientId={clientId}
        />
      </section>

      <section id="simmetria" className={revealClass(150)} style={revealStyle(150)}>
        <SymmetrySection
          symmetry={clinicalReport.symmetry}
          clientId={clientId}
        />
      </section>

      <section id="programma" className={revealClass(190)} style={revealStyle(190)}>
        <ProgramSection
          workouts={workouts}
          workoutLogs={workoutLogs}
          safetyData={safetyData ?? null}
          clientId={clientId}
          compliancePct={compliancePct}
          workoutFreshness={readinessItem?.workout_freshness ?? null}
        />
      </section>

      <section id="obiettivi" className={revealClass(230)} style={revealStyle(230)}>
        <GoalsSection
          clientId={clientId}
          goals={goals}
          latestMeasurement={latestMeasurement ?? null}
          metrics={metrics}
          sesso={sesso}
          dataNascita={dataNascita}
        />
      </section>

      <section id="anamnesi" className={revealClass(270)} style={revealStyle(270)}>
        <AnamnesiSection
          client={client}
          anamnesiState={anamnesiState}
          readinessItem={readinessItem}
          clientId={clientId}
        />
      </section>
    </div>
  );
}
