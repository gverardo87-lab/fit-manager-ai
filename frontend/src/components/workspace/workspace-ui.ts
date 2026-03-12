import type { CaseBucket, CaseKind, CaseSeverity, OperationalCase } from "@/types/api";

export const WORKSPACE_BUCKET_META: Record<
  CaseBucket,
  {
    label: string;
    shortLabel: string;
  }
> = {
  now: {
    label: "Adesso",
    shortLabel: "Ora",
  },
  today: {
    label: "Oggi",
    shortLabel: "Oggi",
  },
  upcoming_3d: {
    label: "Entro 3 giorni",
    shortLabel: "3g",
  },
  upcoming_7d: {
    label: "Entro 7 giorni",
    shortLabel: "7g",
  },
  waiting: {
    label: "In attesa",
    shortLabel: "Attesa",
  },
};

export const WORKSPACE_SEVERITY_META: Record<
  CaseSeverity,
  {
    label: string;
  }
> = {
  critical: {
    label: "Critica",
  },
  high: {
    label: "Alta",
  },
  medium: {
    label: "Media",
  },
  low: {
    label: "Bassa",
  },
};

export const WORKSPACE_CASE_KIND_META: Record<
  CaseKind,
  {
    label: string;
  }
> = {
  onboarding_readiness: {
    label: "Onboarding",
  },
  session_imminent: {
    label: "Sessione",
  },
  followup_post_session: {
    label: "Follow-up",
  },
  todo_manual: {
    label: "Promemoria",
  },
  plan_activation: {
    label: "Programma",
  },
  plan_review_due: {
    label: "Review",
  },
  plan_compliance_risk: {
    label: "Compliance",
  },
  plan_cycle_closing: {
    label: "Fine ciclo",
  },
  payment_overdue: {
    label: "Incasso",
  },
  payment_due_soon: {
    label: "Incasso",
  },
  contract_renewal_due: {
    label: "Rinnovo",
  },
  recurring_expense_due: {
    label: "Spesa",
  },
  client_reactivation: {
    label: "Riattivazione",
  },
  ops_anomaly: {
    label: "Anomalia",
  },
  portal_questionnaire_pending: {
    label: "Portale",
  },
};

const FINANCE_CASE_KIND_LABELS: Partial<Record<CaseKind, string>> = {
  payment_due_soon: "In arrivo",
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

const EUR_FORMATTER = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
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

export function formatFinanceAmount(value: number | null | undefined): string | null {
  if (value === null || value === undefined) return null;
  return EUR_FORMATTER.format(value);
}

export function getWorkspaceSeverityLabel(severity: CaseSeverity): string {
  return WORKSPACE_SEVERITY_META[severity].label;
}

export function getWorkspaceCaseKindLabel(
  caseKind: CaseKind,
  variant: "default" | "finance" = "default",
): string {
  if (variant === "finance" && FINANCE_CASE_KIND_LABELS[caseKind]) {
    return FINANCE_CASE_KIND_LABELS[caseKind]!;
  }
  return WORKSPACE_CASE_KIND_META[caseKind].label;
}

export function getFinanceAmountLabel(caseKind: CaseKind): string {
  if (caseKind === "recurring_expense_due") return "Uscita";
  if (caseKind === "payment_due_soon") return "In arrivo";
  if (caseKind === "contract_renewal_due") return "Residuo";
  return "Da incassare";
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
  if (due !== null) {
    if (item.case_kind === "recurring_expense_due") {
      pieces.push(`Importo ${due.toFixed(2)} EUR`);
    } else if (item.case_kind === "payment_due_soon") {
      pieces.push(`In arrivo ${due.toFixed(2)} EUR`);
    } else {
      pieces.push(`Da incassare ${due.toFixed(2)} EUR`);
    }
  }
  if (residual !== null) pieces.push(`Residuo ${residual.toFixed(2)} EUR`);
  return pieces.join(" | ");
}

export function getCaseImpactLine(item: OperationalCase): string {
  switch (item.case_kind) {
    case "session_imminent":
      return "Se aspetti, rischi di arrivare al prossimo appuntamento senza contesto operativo.";
    case "onboarding_readiness":
      return "Se lo rimandi, l'avvio del cliente resta bloccato e la giornata si sporca dopo.";
    case "payment_overdue":
      return "Se lo lasci aperto, il contratto resta in area a rischio e perdi trazione economica.";
    case "payment_due_soon":
      return "Se lo prepari adesso, eviti che una scadenza vicina diventi arretrato.";
    case "contract_renewal_due":
      return "Se non lo muovi oggi, il rinnovo perde slancio commerciale.";
    case "recurring_expense_due":
      return "Se la confermi nel contesto corretto, la previsione di cassa resta pulita e auditabile.";
    case "client_reactivation":
      return "Se agisci oggi, la probabilita di riattivazione resta piu alta.";
    case "todo_manual":
      return "Chiuderlo ora libera attenzione per i casi piu pesanti.";
    default:
      return "Questo e il prossimo passo utile della giornata.";
  }
}
