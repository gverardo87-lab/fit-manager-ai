"""Primo constraint adapter read-only per il planner legacy SMART."""

from api.schemas.training_science import (
    TSCanonicalPlan,
    TSConstraintEvaluationReport,
    TSConstraintEvaluationSummary,
    TSConstraintFinding,
)
from api.services.training_science import AnalisiPiano, TipoSplit
from api.services.training_science.registry import ProtocolSelectionResult

CONSTRAINT_ENGINE_VERSION = "smart-constraint-v1"


def _expected_split(protocol_split_family: str) -> TipoSplit | None:
    mapping = {
        "full_body": TipoSplit.FULL_BODY,
        "upper_lower": TipoSplit.UPPER_LOWER,
        "push_pull_legs": TipoSplit.PUSH_PULL_LEGS,
    }
    return mapping.get(protocol_split_family)


def _build_summary(findings: list[TSConstraintFinding]) -> TSConstraintEvaluationSummary:
    hard_fail_count = sum(1 for finding in findings if finding.severity == "hard_fail")
    soft_warning_count = sum(1 for finding in findings if finding.severity == "soft_warning")
    optimization_target_count = sum(
        1 for finding in findings if finding.severity == "optimization_target"
    )
    if hard_fail_count > 0:
        overall_status = "fail"
    elif soft_warning_count > 0 or optimization_target_count > 0:
        overall_status = "warn"
    else:
        overall_status = "pass"
    return TSConstraintEvaluationSummary(
        overall_status=overall_status,
        hard_fail_count=hard_fail_count,
        soft_warning_count=soft_warning_count,
        optimization_target_count=optimization_target_count,
    )


def evaluate_protocol_constraints(
    *,
    protocol_selection: ProtocolSelectionResult,
    canonical_plan: TSCanonicalPlan,
    analyzer: AnalisiPiano,
    requested_frequenza: int,
) -> TSConstraintEvaluationReport:
    """Valuta il piano legacy rispetto al protocollo selezionato, senza enforcement."""
    findings: list[TSConstraintFinding] = []
    protocol = protocol_selection.protocol

    if protocol.status == "unsupported_by_policy":
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_status_declared",
                severity="hard_fail",
                scope="protocol",
                status="fail",
                message=(
                    f"Protocollo selezionato '{protocol.protocol_id}' con stato "
                    f"dichiarato '{protocol.status}'."
                ),
            )
        )
    elif protocol.status != "supported":
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_status_declared",
                severity="soft_warning",
                scope="protocol",
                status="warn",
                message=(
                    f"Protocollo selezionato '{protocol.protocol_id}' con stato "
                    f"dichiarato '{protocol.status}'."
                ),
            )
        )
    else:
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_status_declared",
                severity="optimization_target",
                scope="protocol",
                status="pass",
                message=f"Protocollo '{protocol.protocol_id}' supportato dal registry.",
            )
        )

    if not protocol_selection.exact_match:
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_exact_match",
                severity="soft_warning",
                scope="protocol",
                status="warn",
                message=(
                    "Il contesto runtime non ha prodotto un match esatto nel protocol registry; "
                    "il planner legacy sta lavorando in modalita' adapter."
                ),
            )
        )

    if not (protocol.frequenza_min <= requested_frequenza <= protocol.frequenza_max):
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_frequency_range",
                severity="soft_warning",
                scope="protocol",
                status="warn",
                message=(
                    f"Frequenza richiesta {requested_frequenza}x fuori dal range dichiarato "
                    f"del protocollo ({protocol.frequenza_min}-{protocol.frequenza_max}x)."
                ),
            )
        )
    else:
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_frequency_range",
                severity="optimization_target",
                scope="protocol",
                status="pass",
                message=f"Frequenza {requested_frequenza}x compatibile col protocollo selezionato.",
            )
        )

    expected_split = _expected_split(protocol.split_family)
    if expected_split is not None and canonical_plan.tipo_split != expected_split:
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_split_family",
                severity="soft_warning",
                scope="weekly_plan",
                status="warn",
                message=(
                    f"Lo split canonico '{canonical_plan.tipo_split.value}' non coincide con la "
                    f"famiglia dichiarata dal protocollo '{protocol.split_family}'."
                ),
            )
        )
    elif expected_split is not None:
        findings.append(
            TSConstraintFinding(
                rule_id="protocol_split_family",
                severity="optimization_target",
                scope="weekly_plan",
                status="pass",
                message=f"Lo split canonico rispetta la famiglia '{protocol.split_family}'.",
            )
        )

    for muscle in analyzer.volume.muscoli_sotto_mev:
        findings.append(
            TSConstraintFinding(
                rule_id=f"volume_mev_floor:{muscle}",
                severity="optimization_target",
                scope="weekly_plan",
                status="warn",
                message=f"Il muscolo '{muscle}' resta sotto MEV nel piano legacy adattato.",
            )
        )

    for index, imbalance in enumerate(analyzer.balance.squilibri, start=1):
        findings.append(
            TSConstraintFinding(
                rule_id=f"balance_ratio_target:{index}",
                severity="optimization_target",
                scope="weekly_plan",
                status="warn",
                message=imbalance,
            )
        )

    for warning in analyzer.warnings:
        if warning.startswith("Recupero:"):
            findings.append(
                TSConstraintFinding(
                    rule_id="recovery_overlap",
                    severity="soft_warning",
                    scope="adjacent_sessions",
                    status="warn",
                    message=warning,
                )
            )

    return TSConstraintEvaluationReport(
        protocol_id=protocol.protocol_id,
        constraint_profile_id=protocol.constraint_profile_id,
        analyzer_score=analyzer.score,
        findings=findings,
        summary=_build_summary(findings),
    )
