# api/services/projection_engine.py
"""
Projection Engine — proiezione deterministica per obiettivi cliente.

3 layer indipendenti:
  Layer 1: Accumulo stimolo (volume training × compliance × tempo)
  Layer 2: Risposta corporea (OLS regression su misurazioni)
  Layer 3: Proiezione goal (ETA basata su trend + compliance factor)

Ogni layer funziona indipendentemente. Se mancano dati per un layer,
gli altri producono comunque output utile.

Regressione: OLS pura (stdlib, zero numpy). R² come indicatore di fiducia.
Nessuna finestra temporale fissa — tutti i punti disponibili,
i dati parlano da soli.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# Layer 2: Regressione lineare OLS (stdlib puro)
# ════════════════════════════════════════════════════════════


def linear_regression(
    points: list[tuple[float, float]],
) -> tuple[float, float, float] | None:
    """
    Regressione lineare OLS su coppie (x, y).

    Returns: (slope, intercept, r_squared) oppure None se < 2 punti
    o varianza x nulla.

    Formule:
      slope = Σ((xi - x̄)(yi - ȳ)) / Σ((xi - x̄)²)
      intercept = ȳ - slope × x̄
      R² = 1 - SS_res / SS_tot   (0 se SS_tot = 0)
    """
    n = len(points)
    if n < 2:
        return None

    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    mean_x = sum_x / n
    mean_y = sum_y / n

    ss_xx = sum((p[0] - mean_x) ** 2 for p in points)
    ss_xy = sum((p[0] - mean_x) * (p[1] - mean_y) for p in points)
    ss_yy = sum((p[1] - mean_y) ** 2 for p in points)

    if ss_xx < 1e-12:
        return None  # tutti i punti sulla stessa x

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    # R²
    ss_res = sum((p[1] - (slope * p[0] + intercept)) ** 2 for p in points)
    r_squared = 1.0 - (ss_res / ss_yy) if ss_yy > 1e-12 else 0.0
    r_squared = max(0.0, min(1.0, r_squared))

    return slope, intercept, r_squared


def compute_metric_trend(
    values: list[tuple[date, float]],
    reference_date: date | None = None,
) -> MetricTrend | None:
    """
    Calcola trend per una singola metrica usando regressione su TUTTI i punti.

    values: [(data_misurazione, valore), ...] cronologici
    reference_date: data di riferimento per x=0 (default: primo punto)

    Returns: MetricTrend o None se dati insufficienti.
    """
    if len(values) < 2:
        return None

    sorted_vals = sorted(values, key=lambda v: v[0])
    ref = reference_date or sorted_vals[0][0]

    # Converti date in giorni da riferimento
    points = [((v[0] - ref).days, v[1]) for v in sorted_vals]

    result = linear_regression(points)
    if result is None:
        return None

    slope_per_day, intercept, r_squared = result
    weekly_rate = slope_per_day * 7

    # Span temporale dei dati
    span_days = (sorted_vals[-1][0] - sorted_vals[0][0]).days

    current_value = sorted_vals[-1][1]
    current_date = sorted_vals[-1][0]

    # Classificazione fiducia
    n = len(sorted_vals)
    if n < 3 and span_days < 14:
        confidence = "insufficient"
    elif r_squared < 0.3 and n < 4:
        confidence = "insufficient"
    elif r_squared < 0.3:
        confidence = "unstable"
    elif r_squared < 0.6:
        confidence = "moderate"
    else:
        confidence = "good"

    return MetricTrend(
        weekly_rate=round(weekly_rate, 3),
        r_squared=round(r_squared, 3),
        n_points=n,
        span_days=span_days,
        current_value=round(current_value, 2),
        current_date=current_date,
        slope_per_day=slope_per_day,
        intercept=intercept,
        confidence=confidence,
    )


# ════════════════════════════════════════════════════════════
# Layer 3: Proiezione goal
# ════════════════════════════════════════════════════════════

_MAX_PROJECTION_WEEKS = 52  # cap a 12 mesi


def compute_goal_projection(
    trend: MetricTrend,
    target: float,
    direction: str,
    compliance_pct: int,
    goal_deadline: date | None = None,
) -> GoalProjection | None:
    """
    Proietta quando il goal sara' raggiunto basandosi sul trend osservato.

    direction: "diminuire" | "aumentare" | "mantenere"
    compliance_pct: compliance attuale (0-100), usata per scenario perfetto

    Returns: GoalProjection o None se non proiettabile.
    """
    if direction == "mantenere":
        return None

    if trend.confidence == "insufficient":
        return GoalProjection(
            status="insufficient_data",
            message="Servono piu' misurazioni per una proiezione affidabile",
        )

    rate = trend.weekly_rate
    current = trend.current_value
    remaining = target - current

    # Verifica direzione coerente
    if direction == "diminuire" and rate >= 0:
        return GoalProjection(
            status="wrong_direction",
            message="Il trend attuale va nella direzione opposta al goal",
            weekly_rate=rate,
            current_value=current,
            target_value=target,
        )
    if direction == "aumentare" and rate <= 0:
        return GoalProjection(
            status="wrong_direction",
            message="Il trend attuale va nella direzione opposta al goal",
            weekly_rate=rate,
            current_value=current,
            target_value=target,
        )

    # Plateau detection
    if abs(rate) < 0.01:
        return GoalProjection(
            status="plateau",
            message="Plateau rilevato — il valore non sta cambiando",
            weekly_rate=rate,
            current_value=current,
            target_value=target,
        )

    # ETA al ritmo attuale
    weeks_needed = remaining / rate
    if weeks_needed < 0 or weeks_needed > _MAX_PROJECTION_WEEKS:
        return GoalProjection(
            status="unreachable",
            message="Obiettivo oltre 12 mesi al ritmo attuale",
            weekly_rate=rate,
            current_value=current,
            target_value=target,
        )

    today = date.today()
    eta_current = today + timedelta(weeks=weeks_needed)

    # Scenario compliance perfetta
    eta_perfect: date | None = None
    days_saved: int | None = None

    if 0 < compliance_pct < 100:
        perfect_rate = rate * (100.0 / compliance_pct)
        weeks_perfect = remaining / perfect_rate
        if 0 < weeks_perfect <= _MAX_PROJECTION_WEEKS:
            eta_perfect = today + timedelta(weeks=weeks_perfect)
            days_saved = (eta_current - eta_perfect).days

    # Impatto per sessione saltata
    days_per_missed_session: float | None = None
    if eta_perfect and days_saved and days_saved > 0:
        # Stima sessioni perse nel periodo trend
        if compliance_pct < 100 and trend.span_days > 0:
            # Approssimazione: 3 sessioni/settimana di default
            total_expected = (trend.span_days / 7) * 3
            missed = total_expected * (1 - compliance_pct / 100)
            if missed > 0:
                days_per_missed_session = round(days_saved / missed, 1)

    # Deadline check
    on_track: bool | None = None
    if goal_deadline:
        on_track = eta_current <= goal_deadline

    return GoalProjection(
        status="projected",
        message=None,
        weekly_rate=rate,
        current_value=current,
        target_value=target,
        eta=eta_current,
        eta_perfect=eta_perfect,
        days_saved=days_saved,
        days_per_missed_session=days_per_missed_session,
        r_squared=trend.r_squared,
        confidence=trend.confidence,
        on_track=on_track,
        goal_deadline=goal_deadline,
    )


# ════════════════════════════════════════════════════════════
# Layer 1: Accumulo stimolo (volume cumulativo)
# ════════════════════════════════════════════════════════════


def compute_volume_accumulation(
    weekly_volume: float,
    compliance_pct: int,
    weeks_active: int,
) -> VolumeAccumulation:
    """
    Stima stimolo cumulativo nel periodo di attivita' del piano.

    weekly_volume: serie/settimana dal piano (da analyze_plan)
    compliance_pct: aderenza 0-100
    weeks_active: settimane di attivita' del piano
    """
    planned_total = round(weekly_volume * weeks_active, 1)
    effective_total = round(planned_total * (compliance_pct / 100.0), 1)
    missed_total = round(planned_total - effective_total, 1)

    return VolumeAccumulation(
        weekly_volume_planned=round(weekly_volume, 1),
        weekly_volume_effective=round(weekly_volume * compliance_pct / 100.0, 1),
        weeks_active=weeks_active,
        total_volume_planned=planned_total,
        total_volume_effective=effective_total,
        total_volume_missed=missed_total,
    )


# ════════════════════════════════════════════════════════════
# Generazione punti chart
# ════════════════════════════════════════════════════════════

_CHART_WEEKS_FUTURE = 16  # punti proiezione nel chart


def generate_projection_points(
    trend: MetricTrend,
    target: float | None,
    eta: date | None,
) -> list[ProjectionPoint]:
    """
    Genera punti per il chart predittivo.

    Produce punti settimanali dalla data corrente fino a ETA (o +16 settimane).
    """
    if trend.confidence == "insufficient":
        return []

    today = date.today()
    ref_date = trend.current_date

    # Calcola fine proiezione
    if eta and (eta - today).days <= _CHART_WEEKS_FUTURE * 7:
        end_date = eta + timedelta(weeks=2)  # un po' oltre ETA
    else:
        end_date = today + timedelta(weeks=_CHART_WEEKS_FUTURE)

    points: list[ProjectionPoint] = []
    current = today
    while current <= end_date:
        days_from_ref = (current - ref_date).days
        projected_value = trend.current_value + trend.slope_per_day * days_from_ref

        # Clamp: non proiettare oltre il target se lo supera
        if target is not None:
            if trend.weekly_rate < 0:  # diminuire
                projected_value = max(projected_value, target)
            else:  # aumentare
                projected_value = min(projected_value, target)

        points.append(
            ProjectionPoint(
                date=current,
                value=round(projected_value, 2),
                is_projection=current > ref_date,
            )
        )
        current += timedelta(weeks=1)

    return points


# ════════════════════════════════════════════════════════════
# Risk flags
# ════════════════════════════════════════════════════════════

# Soglie rate ACSM (per peso — >1% body weight/week = rischio catabolismo)
_RATE_THRESHOLDS = {
    1: {"warning": 0.7, "alert": 1.0, "unit": "kg/sett", "lower_better": True},   # peso
    3: {"warning": 0.5, "alert": 0.8, "unit": "%/sett", "lower_better": True},     # grasso %
}


def compute_risk_flags(
    trends: dict[int, MetricTrend],
    goals: list[dict],
) -> list[RiskFlag]:
    """
    Genera flag di rischio basati su trend e soglie ACSM.

    goals: [{id_metrica, direzione, valore_target}, ...]
    """
    flags: list[RiskFlag] = []

    # 1. Rate troppo veloce (ACSM)
    for metric_id, thresholds in _RATE_THRESHOLDS.items():
        trend = trends.get(metric_id)
        if not trend or trend.confidence == "insufficient":
            continue

        abs_rate = abs(trend.weekly_rate)
        if abs_rate >= thresholds["alert"]:
            flags.append(RiskFlag(
                severity="alert",
                code="rate_too_fast",
                message=(
                    f"Variazione troppo rapida: "
                    f"{trend.weekly_rate:+.1f} {thresholds['unit']}"
                ),
                metric_id=metric_id,
            ))
        elif abs_rate >= thresholds["warning"]:
            flags.append(RiskFlag(
                severity="warning",
                code="rate_elevated",
                message=(
                    f"Variazione elevata: "
                    f"{trend.weekly_rate:+.1f} {thresholds['unit']}"
                ),
                metric_id=metric_id,
            ))

    # 2. Trend contrario al goal
    for goal in goals:
        mid = goal.get("id_metrica")
        direction = goal.get("direzione")
        trend = trends.get(mid) if mid else None
        if not trend or trend.confidence == "insufficient":
            continue
        if direction == "diminuire" and trend.weekly_rate > 0.05:
            flags.append(RiskFlag(
                severity="alert",
                code="wrong_direction",
                message="Trend in aumento ma obiettivo e' diminuire",
                metric_id=mid,
            ))
        elif direction == "aumentare" and trend.weekly_rate < -0.05:
            flags.append(RiskFlag(
                severity="alert",
                code="wrong_direction",
                message="Trend in calo ma obiettivo e' aumentare",
                metric_id=mid,
            ))

    # 3. Plateau su goal attivi
    for goal in goals:
        mid = goal.get("id_metrica")
        trend = trends.get(mid) if mid else None
        if not trend or trend.confidence == "insufficient":
            continue
        if abs(trend.weekly_rate) < 0.01 and goal.get("valore_target") is not None:
            flags.append(RiskFlag(
                severity="warning",
                code="plateau",
                message="Plateau rilevato — nessun cambiamento significativo",
                metric_id=mid,
            ))

    return flags


# ════════════════════════════════════════════════════════════
# Data classes (plain, no Pydantic — usati internamente)
# ════════════════════════════════════════════════════════════


class MetricTrend:
    """Trend calcolato per una singola metrica."""

    __slots__ = (
        "weekly_rate", "r_squared", "n_points", "span_days",
        "current_value", "current_date", "slope_per_day",
        "intercept", "confidence",
    )

    def __init__(
        self,
        weekly_rate: float,
        r_squared: float,
        n_points: int,
        span_days: int,
        current_value: float,
        current_date: date,
        slope_per_day: float,
        intercept: float,
        confidence: str,
    ):
        self.weekly_rate = weekly_rate
        self.r_squared = r_squared
        self.n_points = n_points
        self.span_days = span_days
        self.current_value = current_value
        self.current_date = current_date
        self.slope_per_day = slope_per_day
        self.intercept = intercept
        self.confidence = confidence


class GoalProjection:
    """Proiezione per un singolo goal."""

    __slots__ = (
        "status", "message", "weekly_rate", "current_value",
        "target_value", "eta", "eta_perfect", "days_saved",
        "days_per_missed_session", "r_squared", "confidence",
        "on_track", "goal_deadline",
    )

    def __init__(
        self,
        status: str,
        message: str | None = None,
        weekly_rate: float | None = None,
        current_value: float | None = None,
        target_value: float | None = None,
        eta: date | None = None,
        eta_perfect: date | None = None,
        days_saved: int | None = None,
        days_per_missed_session: float | None = None,
        r_squared: float | None = None,
        confidence: str | None = None,
        on_track: bool | None = None,
        goal_deadline: date | None = None,
    ):
        self.status = status
        self.message = message
        self.weekly_rate = weekly_rate
        self.current_value = current_value
        self.target_value = target_value
        self.eta = eta
        self.eta_perfect = eta_perfect
        self.days_saved = days_saved
        self.days_per_missed_session = days_per_missed_session
        self.r_squared = r_squared
        self.confidence = confidence
        self.on_track = on_track
        self.goal_deadline = goal_deadline


class VolumeAccumulation:
    """Stimolo cumulativo nel periodo attivo."""

    __slots__ = (
        "weekly_volume_planned", "weekly_volume_effective",
        "weeks_active", "total_volume_planned",
        "total_volume_effective", "total_volume_missed",
    )

    def __init__(
        self,
        weekly_volume_planned: float,
        weekly_volume_effective: float,
        weeks_active: int,
        total_volume_planned: float,
        total_volume_effective: float,
        total_volume_missed: float,
    ):
        self.weekly_volume_planned = weekly_volume_planned
        self.weekly_volume_effective = weekly_volume_effective
        self.weeks_active = weeks_active
        self.total_volume_planned = total_volume_planned
        self.total_volume_effective = total_volume_effective
        self.total_volume_missed = total_volume_missed


class ProjectionPoint:
    """Singolo punto per il chart."""

    __slots__ = ("date", "value", "is_projection")

    def __init__(self, date: date, value: float, is_projection: bool):
        self.date = date
        self.value = value
        self.is_projection = is_projection


class RiskFlag:
    """Flag di rischio."""

    __slots__ = ("severity", "code", "message", "metric_id")

    def __init__(
        self,
        severity: str,
        code: str,
        message: str,
        metric_id: int | None = None,
    ):
        self.severity = severity
        self.code = code
        self.message = message
        self.metric_id = metric_id
