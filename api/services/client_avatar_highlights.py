# api/services/client_avatar_highlights.py
"""
Client Avatar Highlights — registry di regole per segnalazioni puntuali.

Ogni regola e' una funzione pura che riceve un AvatarContext e ritorna
un AvatarHighlight o None. Estendere = aggiungere 1 funzione + appendere
a HIGHLIGHT_RULES.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from api.schemas.client_avatar import AvatarHighlight


@dataclass
class AvatarContext:
    """Dati aggregati disponibili per le regole highlight."""
    client_id: int
    anamnesi_state: str  # missing | legacy | structured
    has_active_contract: bool
    credits_remaining: int
    credits_total: int
    overdue_rates_count: int
    days_to_expiry: Optional[int]
    renewal_count: int
    has_active_plan: bool
    compliance_30d: Optional[float]
    compliance_60d: Optional[float]
    days_since_last_session: Optional[int]
    has_measurements: bool
    measurement_freshness: str  # missing | ok | warning | critical
    seniority_days: int
    # Trajectory fields
    pt_attendance_trend: str = "unknown"  # up | stable | down | unknown
    momentum: str = "inactive"  # accelerating | steady | decelerating | inactive
    # PT temporal anchors
    days_since_last_pt: Optional[int] = None
    days_until_next_pt: Optional[int] = None
    pt_cancellation_rate_30d: Optional[float] = None


HighlightRule = Callable[[AvatarContext], Optional[AvatarHighlight]]


def _overdue_rates(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.overdue_rates_count > 0:
        n = ctx.overdue_rates_count
        text = f"{n} rata scaduta" if n == 1 else f"{n} rate scadute"
        return AvatarHighlight(
            code="overdue_rates",
            text=text,
            severity="critical",
            dimension="contract",
            cta_href=f"/contratti?cliente={ctx.client_id}",
        )
    return None


def _credits_exhausted(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.has_active_contract and ctx.credits_remaining <= 0 and ctx.credits_total > 0:
        return AvatarHighlight(
            code="credits_exhausted",
            text="Crediti esauriti",
            severity="critical",
            dimension="contract",
            cta_href=f"/clienti/{ctx.client_id}?tab=contratti",
        )
    return None


def _session_gap_14d(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.days_since_last_session is not None and ctx.days_since_last_session >= 14:
        return AvatarHighlight(
            code="session_gap_14d",
            text=f"{ctx.days_since_last_session} giorni senza allenamento",
            severity="warning",
            dimension="training",
            cta_href=f"/allenamenti?idCliente={ctx.client_id}",
        )
    return None


def _compliance_dropping(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if (
        ctx.compliance_30d is not None
        and ctx.compliance_60d is not None
        and ctx.compliance_30d < 0.5
        and ctx.compliance_60d > 0.7
    ):
        pct = int(ctx.compliance_30d * 100)
        return AvatarHighlight(
            code="compliance_dropping",
            text=f"Compliance in calo ({pct}% ultimi 30gg)",
            severity="warning",
            dimension="training",
            cta_href=f"/allenamenti?idCliente={ctx.client_id}",
        )
    return None


def _credits_low(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.has_active_contract and 1 <= ctx.credits_remaining <= 2:
        return AvatarHighlight(
            code="credits_low",
            text=f"{ctx.credits_remaining} crediti rimasti",
            severity="warning",
            dimension="contract",
            cta_href=f"/clienti/{ctx.client_id}?tab=contratti",
        )
    return None


def _measurements_stale(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.measurement_freshness == "critical":
        return AvatarHighlight(
            code="measurements_stale",
            text="Misurazioni da aggiornare",
            severity="critical",
            dimension="body_goals",
            cta_href=f"/clienti/{ctx.client_id}/misurazioni",
        )
    if ctx.measurement_freshness == "warning":
        return AvatarHighlight(
            code="measurements_stale",
            text="Misurazioni da aggiornare",
            severity="warning",
            dimension="body_goals",
            cta_href=f"/clienti/{ctx.client_id}/misurazioni",
        )
    return None


def _anamnesi_missing(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.anamnesi_state == "missing":
        return AvatarHighlight(
            code="anamnesi_missing",
            text="Anamnesi mancante",
            severity="warning",
            dimension="clinical",
            cta_href=f"/clienti/{ctx.client_id}/anamnesi?startWizard=1",
        )
    return None


def _anamnesi_v1(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.anamnesi_state == "legacy":
        return AvatarHighlight(
            code="anamnesi_v1",
            text="Anamnesi legacy da aggiornare",
            severity="info",
            dimension="clinical",
            cta_href=f"/clienti/{ctx.client_id}/anamnesi?startWizard=1",
        )
    return None


def _no_active_plan(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if not ctx.has_active_plan:
        return AvatarHighlight(
            code="no_active_plan",
            text="Nessuna scheda attiva",
            severity="warning",
            dimension="training",
            cta_href=f"/clienti/{ctx.client_id}?tab=schede&startScheda=1",
        )
    return None


def _pt_attendance_dropping(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.pt_attendance_trend == "down":
        return AvatarHighlight(
            code="pt_attendance_dropping",
            text="Frequenza PT in calo",
            severity="warning",
            dimension="training",
            cta_href=f"/clienti/{ctx.client_id}?tab=sessioni",
        )
    return None


def _pt_session_gap(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.days_since_last_pt is not None and ctx.days_since_last_pt >= 14:
        severity = "critical" if ctx.days_since_last_pt >= 21 else "warning"
        return AvatarHighlight(
            code="pt_session_gap",
            text=f"{ctx.days_since_last_pt}g dall'ultima seduta PT",
            severity=severity,
            dimension="training",
            cta_href=f"/agenda?from=clienti-{ctx.client_id}",
        )
    return None


def _no_next_pt_booked(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if (
        ctx.days_until_next_pt is None
        and ctx.has_active_contract
        and ctx.credits_remaining > 0
    ):
        return AvatarHighlight(
            code="no_next_pt_booked",
            text="Nessuna seduta PT programmata",
            severity="warning",
            dimension="training",
            cta_href=f"/agenda?from=clienti-{ctx.client_id}",
        )
    return None


def _pt_high_cancellation(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.pt_cancellation_rate_30d is not None and ctx.pt_cancellation_rate_30d >= 0.3:
        pct = int(ctx.pt_cancellation_rate_30d * 100)
        return AvatarHighlight(
            code="pt_high_cancellation",
            text=f"{pct}% sedute PT cancellate",
            severity="warning",
            dimension="training",
            cta_href=f"/clienti/{ctx.client_id}?tab=sessioni",
        )
    return None


def _momentum_decelerating(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if ctx.momentum == "decelerating":
        return AvatarHighlight(
            code="momentum_decelerating",
            text="Momentum in calo — da monitorare",
            severity="info",
            dimension="training",
            cta_href=f"/monitoraggio/{ctx.client_id}?from=clienti-{ctx.client_id}",
        )
    return None


def _loyal_no_renewal(ctx: AvatarContext) -> Optional[AvatarHighlight]:
    if (
        ctx.seniority_days >= 180
        and ctx.has_active_contract
        and ctx.days_to_expiry is not None
        and ctx.days_to_expiry <= 30
        and ctx.renewal_count == 0
    ):
        return AvatarHighlight(
            code="loyal_no_renewal",
            text="Cliente fedele, contratto in scadenza — proponi rinnovo",
            severity="info",
            dimension="contract",
            cta_href=f"/clienti/{ctx.client_id}?tab=contratti",
        )
    return None


# Ordine = priorita' (critical first, poi warning, poi info)
HIGHLIGHT_RULES: list[HighlightRule] = [
    _overdue_rates,
    _credits_exhausted,
    _pt_session_gap,
    _session_gap_14d,
    _compliance_dropping,
    _pt_attendance_dropping,
    _no_next_pt_booked,
    _pt_high_cancellation,
    _credits_low,
    _measurements_stale,
    _anamnesi_missing,
    _anamnesi_v1,
    _no_active_plan,
    _momentum_decelerating,
    _loyal_no_renewal,
]


def compute_highlights(ctx: AvatarContext) -> list[AvatarHighlight]:
    """Applica tutte le regole e ritorna le highlight attive."""
    highlights: list[AvatarHighlight] = []
    for rule in HIGHLIGHT_RULES:
        result = rule(ctx)
        if result is not None:
            highlights.append(result)
    return highlights
