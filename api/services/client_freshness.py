"""Shared freshness policy for measurements and workout plans."""

from datetime import date, datetime, timedelta

from api.schemas.clinical import ClinicalFreshnessSignal

MEASUREMENT_WARNING_DAYS = 25
MEASUREMENT_CRITICAL_DAYS = 35
WORKOUT_WARNING_DAYS = 21
WORKOUT_CRITICAL_DAYS = 35


def parse_reference_date(value: str | date | datetime | None) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    normalized = value.strip()
    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized[:10])
    except ValueError:
        return None


def _timeline_status(days_to_due: int | None) -> str:
    if days_to_due is None:
        return "none"
    if days_to_due < 0:
        return "overdue"
    if days_to_due == 0:
        return "today"
    if days_to_due <= 7:
        return "upcoming_7d"
    if days_to_due <= 14:
        return "upcoming_14d"
    return "future"


def _days_since(reference_date: date, last_recorded_date: date | None) -> int | None:
    if last_recorded_date is None:
        return None
    return (reference_date - last_recorded_date).days


def _format_weeks_label(days_since_last: int) -> str:
    weeks = max(1, days_since_last // 7)
    return f"{weeks} settiman{'a' if weeks == 1 else 'e'}"


def _build_missing_signal(
    *,
    domain: str,
    reason_code: str,
    label: str,
    cta_label: str,
    cta_href: str,
    reference_date: date,
) -> ClinicalFreshnessSignal:
    return ClinicalFreshnessSignal(
        domain=domain,
        status="missing",
        label=label,
        cta_label=cta_label,
        cta_href=cta_href,
        timeline_status="today",
        reason_code=reason_code,
        due_date=reference_date,
        last_recorded_date=None,
        days_to_due=0,
        days_since_last=None,
    )


def build_measurement_freshness(
    *,
    client_id: int,
    latest_measurement_date: date | None,
    reference_date: date,
) -> ClinicalFreshnessSignal:
    cta_href = f"/clienti/{client_id}/misurazioni"
    if latest_measurement_date is None:
        return _build_missing_signal(
            domain="measurements",
            reason_code="measurement_missing",
            label="Nessuna misurazione registrata",
            cta_label="Registra baseline",
            cta_href=cta_href,
            reference_date=reference_date,
        )

    due_date = latest_measurement_date + timedelta(days=MEASUREMENT_WARNING_DAYS)
    days_to_due = (due_date - reference_date).days
    days_since_last = _days_since(reference_date, latest_measurement_date)
    assert days_since_last is not None

    if days_since_last >= MEASUREMENT_CRITICAL_DAYS:
        status = "critical"
        label = f"Misurazioni da riprendere ({days_since_last} giorni)"
        reason_code = "measurement_stale"
    elif days_since_last >= MEASUREMENT_WARNING_DAYS:
        status = "warning"
        label = f"Ultima misurazione {days_since_last} giorni fa"
        reason_code = "measurement_review"
    else:
        status = "ok"
        if days_to_due == 0:
            label = "Review misurazioni oggi"
        elif days_to_due == 1:
            label = "Review misurazioni domani"
        else:
            label = f"Review misurazioni tra {days_to_due} giorni"
        reason_code = "measurement_review"

    return ClinicalFreshnessSignal(
        domain="measurements",
        status=status,
        label=label,
        cta_label="Nuova misurazione",
        cta_href=cta_href,
        timeline_status=_timeline_status(days_to_due),
        reason_code=reason_code,
        due_date=due_date,
        last_recorded_date=latest_measurement_date,
        days_to_due=days_to_due,
        days_since_last=days_since_last,
    )


def build_workout_freshness(
    *,
    client_id: int,
    latest_workout_reference: str | date | datetime | None,
    reference_date: date,
) -> ClinicalFreshnessSignal:
    cta_href = f"/clienti/{client_id}?tab=schede&startScheda=1"
    latest_workout_date = parse_reference_date(latest_workout_reference)
    if latest_workout_date is None:
        return _build_missing_signal(
            domain="workout",
            reason_code="workout_missing",
            label="Nessuna scheda assegnata",
            cta_label="Assegna scheda",
            cta_href=cta_href,
            reference_date=reference_date,
        )

    due_date = latest_workout_date + timedelta(days=WORKOUT_WARNING_DAYS)
    days_to_due = (due_date - reference_date).days
    days_since_last = _days_since(reference_date, latest_workout_date)
    assert days_since_last is not None

    if days_since_last >= WORKOUT_CRITICAL_DAYS:
        status = "critical"
        label = f"Scheda da aggiornare ({_format_weeks_label(days_since_last)})"
        reason_code = "workout_stale"
    elif days_since_last >= WORKOUT_WARNING_DAYS:
        status = "warning"
        label = f"Scheda creata {_format_weeks_label(days_since_last)} fa"
        reason_code = "workout_review"
    else:
        status = "ok"
        if days_to_due == 0:
            label = "Review scheda oggi"
        elif days_to_due == 1:
            label = "Review scheda domani"
        else:
            label = f"Review scheda tra {days_to_due} giorni"
        reason_code = "workout_review"

    return ClinicalFreshnessSignal(
        domain="workout",
        status=status,
        label=label,
        cta_label="Rivedi scheda",
        cta_href=cta_href,
        timeline_status=_timeline_status(days_to_due),
        reason_code=reason_code,
        due_date=due_date,
        last_recorded_date=latest_workout_date,
        days_to_due=days_to_due,
        days_since_last=days_since_last,
    )
