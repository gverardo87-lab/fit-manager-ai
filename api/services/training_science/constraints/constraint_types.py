"""Tipi minimi del constraint adapter SMART/KineScore."""

from typing import Literal

ConstraintSeverity = Literal["hard_fail", "soft_warning", "optimization_target"]
ConstraintScope = Literal["protocol", "weekly_plan", "session", "adjacent_sessions"]
ConstraintStatus = Literal["pass", "warn", "fail"]
