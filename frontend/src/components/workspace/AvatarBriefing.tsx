// src/components/workspace/AvatarBriefing.tsx
/**
 * AvatarBriefing — genera 2-3 righe di prosa italiana dall'avatar.
 *
 * Template deterministico, zero AI. Produce un briefing narrativo
 * che sintetizza lo stato del cliente prima della seduta.
 *
 * Es: "Maria, 34 anni, da 8 mesi. Compliance buona (78%). 5 crediti, misurazioni fresche."
 */

import { surfaceRoleClassName } from "@/components/ui/surface-role";
import type { ClientAvatar } from "@/types/api";

// ── Template engine ──────────────────────────────────────────────

function formatSeniority(days: number): string {
  if (days < 30) return "cliente da pochi giorni";
  if (days < 90) return "cliente recente";
  const months = Math.floor(days / 30);
  if (months < 12) return `da ${months} ${months === 1 ? "mese" : "mesi"}`;
  const y = Math.floor(months / 12);
  const r = months % 12;
  return r === 0 ? `da ${y} ${y === 1 ? "anno" : "anni"}` : `da ${y}a ${r}m`;
}

function buildBriefingParts(avatar: ClientAvatar): string[] {
  const { identity, clinical, contract, training, body_goals } = avatar;
  const parts: string[] = [];

  // ── Frase 1: identita + seniority ──
  const nameParts: string[] = [identity.nome];
  if (identity.age !== null) nameParts.push(`${identity.age} anni`);
  nameParts.push(formatSeniority(identity.seniority_days));
  parts.push(nameParts.join(", ") + ".");

  // ── Frase 2: stato operativo (il piu' importante) ──
  const opParts: string[] = [];

  // Compliance
  if (training.compliance_30d !== null) {
    const c = Math.round(training.compliance_30d);
    if (c >= 80) opParts.push(`compliance buona (${c}%)`);
    else if (c >= 50) opParts.push(`compliance in calo (${c}%)`);
    else opParts.push(`compliance bassa (${c}%)`);
  }

  // Crediti
  if (contract.has_active_contract) {
    const rem = contract.credits_remaining;
    if (rem <= 0) opParts.push("crediti esauriti");
    else if (rem <= 2) opParts.push(`${rem} ${rem === 1 ? "credito rimasto" : "crediti rimasti"}`);
    else opParts.push(`${rem} crediti`);
  } else {
    opParts.push("nessun contratto attivo");
  }

  // Rate scadute
  if (contract.overdue_rates_count > 0) {
    opParts.push(`${contract.overdue_rates_count} ${contract.overdue_rates_count === 1 ? "rata scaduta" : "rate scadute"}`);
  }

  if (opParts.length > 0) {
    parts.push(capitalize(opParts.join(", ")) + ".");
  }

  // ── Frase 3: contesto clinico/corpo (solo se rilevante) ──
  const ctxParts: string[] = [];

  // Anamnesi
  if (clinical.anamnesi_state === "missing") ctxParts.push("anamnesi da compilare");
  else if (clinical.anamnesi_state === "legacy") ctxParts.push("anamnesi da aggiornare");

  // Condizioni
  if (clinical.condition_count > 0 && clinical.condition_names.length > 0) {
    const names = clinical.condition_names.slice(0, 2).join(", ");
    ctxParts.push(clinical.condition_count <= 2 ? names : `${names} (+${clinical.condition_count - 2})`);
  }

  // Misurazioni
  if (body_goals.measurement_freshness === "stale") ctxParts.push("misurazioni da aggiornare");
  else if (body_goals.measurement_freshness === "missing") ctxParts.push("nessuna misurazione");
  else if (body_goals.measurement_freshness === "fresh") ctxParts.push("misurazioni recenti");

  // Scheda
  if (!training.has_active_plan) ctxParts.push("nessuna scheda attiva");

  // Gap sessioni
  if (training.days_since_last_session !== null && training.days_since_last_session >= 14) {
    ctxParts.push(`${training.days_since_last_session}g senza allenamento`);
  }

  if (ctxParts.length > 0) {
    parts.push(capitalize(ctxParts.join(", ")) + ".");
  }

  return parts;
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── Component ────────────────────────────────────────────────────

interface AvatarBriefingProps {
  avatar: ClientAvatar;
}

export function AvatarBriefing({ avatar }: AvatarBriefingProps) {
  const sentences = buildBriefingParts(avatar);

  return (
    <div className={surfaceRoleClassName({ role: "context", tone: "neutral" }, "px-3.5 py-3")}>
      <p className="text-[12px] leading-[1.6] text-foreground/80">
        {sentences.join(" ")}
      </p>
    </div>
  );
}
