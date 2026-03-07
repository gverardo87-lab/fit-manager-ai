"""Validation harness SMART/KineScore — benchmark cases e contratti."""

from .validation_catalog import (
    CLIENT_FIXTURES,
    REQUEST_FIXTURES,
    VALIDATION_CATALOG_VERSION,
    VALIDATION_MATRIX,
    ClientFixture,
    RequestFixture,
    ScoreBand,
    ValidationCase,
    WarningPolicy,
    get_client_fixture,
    get_request_fixture,
    get_validation_case,
)
from .validation_contracts import (
    VALIDATION_CONTRACTS_VERSION,
    CheckResult,
    ValidationReport,
    run_full_matrix,
    run_validation_case,
)

__all__ = [
    "CLIENT_FIXTURES",
    "VALIDATION_CATALOG_VERSION",
    "VALIDATION_CONTRACTS_VERSION",
    "VALIDATION_MATRIX",
    "REQUEST_FIXTURES",
    "CheckResult",
    "ClientFixture",
    "RequestFixture",
    "ScoreBand",
    "ValidationCase",
    "ValidationReport",
    "WarningPolicy",
    "get_client_fixture",
    "get_request_fixture",
    "get_validation_case",
    "run_full_matrix",
    "run_validation_case",
]
