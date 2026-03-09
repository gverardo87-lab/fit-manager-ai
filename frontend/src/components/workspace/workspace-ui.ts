import type { CaseBucket, CaseKind, CaseSeverity, OperationalCase } from "@/types/api";

export const WORKSPACE_BUCKET_META: Record<
  CaseBucket,
  {
    label: string;
    shortLabel: string;
    tone: string;
    pillTone: string;
  }
> = {
  now: {
    label: "Adesso",
    shortLabel: "Ora",
    tone: "text-red-700 dark:text-red-300",
    pillTone: "border-red-200 bg-red-50 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300",
  },
  today: {
    label: "Oggi",
    shortLabel: "Oggi",
    tone: "text-amber-700 dark:text-amber-300",
    pillTone: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300",
  },
  upcoming_3d: {
    label: "Entro 3 giorni",
    shortLabel: "3g",
    tone: "text-blue-700 dark:text-blue-300",
    pillTone: "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300",
  },
  upcoming_7d: {
    label: "Entro 7 giorni",
    shortLabel: "7g",
    tone: "text-violet-700 dark:text-violet-300",
    pillTone: "border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-900/40 dark:bg-violet-950/20 dark:text-violet-300",
  },
  waiting: {
    label: "In attesa",
    shortLabel: "Attesa",
    tone: "text-zinc-700 dark:text-zinc-300",
    pillTone: "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/70 dark:text-zinc-300",
  },
};

export const WORKSPACE_SEVERITY_META: Record<
  CaseSeverity,
  {
    label: string;
    tone: string;
  }
> = {
  critical: {
    label: "Critica",
    tone: "border-red-200 bg-red-50 text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300",
  },
  high: {
    label: "Alta",
    tone: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300",
  },
  medium: {
    label: "Media",
    tone: "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300",
  },
  low: {
    label: "Bassa",
    tone: "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/70 dark:text-zinc-300",
  },
};

export const WORKSPACE_CASE_KIND_META: Record<
  CaseKind,
  {
    label: string;
    tone: string;
  }
> = {
  onboarding_readiness: {
    label: "Onboarding",
    tone: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300",
  },
  session_imminent: {
    label: "Sessione",
    tone: "bg-sky-100 text-sky-700 dark:bg-sky-950/30 dark:text-sky-300",
  },
  followup_post_session: {
    label: "Follow-up",
    tone: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-300",
  },
  todo_manual: {
    label: "Promemoria",
    tone: "bg-amber-100 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300",
  },
  plan_activation: {
    label: "Programma",
    tone: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300",
  },
  plan_review_due: {
    label: "Review",
    tone: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300",
  },
  plan_compliance_risk: {
    label: "Compliance",
    tone: "bg-violet-100 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300",
  },
  plan_cycle_closing: {
    label: "Fine ciclo",
    tone: "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-950/30 dark:text-fuchsia-300",
  },
  payment_overdue: {
    label: "Incasso",
    tone: "bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300",
  },
  payment_due_soon: {
    label: "Scadenza",
    tone: "bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300",
  },
  contract_renewal_due: {
    label: "Rinnovo",
    tone: "bg-orange-100 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300",
  },
  recurring_expense_due: {
    label: "Spesa",
    tone: "bg-orange-100 text-orange-700 dark:bg-orange-950/30 dark:text-orange-300",
  },
  client_reactivation: {
    label: "Riattivazione",
    tone: "bg-teal-100 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300",
  },
  ops_anomaly: {
    label: "Anomalia",
    tone: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300",
  },
  portal_questionnaire_pending: {
    label: "Portale",
    tone: "bg-lime-100 text-lime-700 dark:bg-lime-950/30 dark:text-lime-300",
  },
};

const DATE_FORMATTER = new Intl.DateTimeFormat("it-IT", {
  day: "numeric",
  month: "short",
});

const DATETIME_FORMATTER = new Intl.DateTimeFormat("it-IT", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatWorkspaceDate(value: string | null): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return DATE_FORMATTER.format(parsed);
}

export function formatWorkspaceDateTime(value: string | null): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return DATETIME_FORMATTER.format(parsed);
}

export function getCaseDueLabel(item: OperationalCase): string {
  if (item.bucket === "now") return "Richiede attenzione ora";
  if (item.days_to_due === null) {
    return item.due_date ? `Scadenza ${formatWorkspaceDate(item.due_date)}` : "Senza scadenza";
  }
  if (item.days_to_due < 0) {
    const absDays = Math.abs(item.days_to_due);
    return absDays === 1 ? "Scaduto ieri" : `Scaduto da ${absDays} giorni`;
  }
  if (item.days_to_due === 0) return "Scade oggi";
  if (item.days_to_due === 1) return "Scade domani";
  return `Scade tra ${item.days_to_due} giorni`;
}

export function getFinanceSummary(item: OperationalCase): string | null {
  if (!item.finance_context) return null;
  if (item.finance_context.visibility === "redacted") {
    return "Importi disponibili nel workspace Rinnovi & Incassi";
  }
  if (item.finance_context.visibility !== "full") return null;
  const due = item.finance_context.total_due_amount;
  const residual = item.finance_context.total_residual_amount;
  if (due === null && residual === null) return null;
  const pieces: string[] = [];
  if (due !== null) pieces.push(`Da incassare ${due.toFixed(2)} EUR`);
  if (residual !== null) pieces.push(`Residuo ${residual.toFixed(2)} EUR`);
  return pieces.join(" • ");
}

export function getCaseImpactLine(item: OperationalCase): string {
  switch (item.case_kind) {
    case "session_imminent":
      return "Se aspetti, rischi di arrivare al prossimo appuntamento senza contesto operativo.";
    case "onboarding_readiness":
      return "Se lo rimandi, l'avvio del cliente resta bloccato e la giornata si sporca dopo.";
    case "payment_overdue":
      return "Se lo lasci aperto, il contratto resta in area a rischio e perdi trazione economica.";
    case "contract_renewal_due":
      return "Se non lo muovi oggi, il rinnovo perde slancio commerciale.";
    case "client_reactivation":
      return "Se agisci oggi, la probabilita di riattivazione resta piu alta.";
    case "todo_manual":
      return "Chiuderlo ora libera attenzione per i casi piu pesanti.";
    default:
      return "Questo e il prossimo passo utile della giornata.";
  }
}
