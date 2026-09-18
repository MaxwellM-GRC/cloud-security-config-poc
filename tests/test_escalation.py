from datetime import datetime, timezone

from scripts.escalate_cases import (
    BREACH_LABEL,
    HUMAN_REVIEW_LABEL,
    OPEN_LABEL,
    is_overdue,
)


NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def test_actionable_case_beyond_sla_is_overdue():
    assert is_overdue("2026-09-10T11:59:00Z", {OPEN_LABEL}, 5, NOW)


def test_case_inside_sla_is_not_overdue():
    assert not is_overdue("2026-09-15T12:00:00Z", {OPEN_LABEL}, 5, NOW)


def test_human_review_or_existing_escalation_is_not_relabelled():
    assert not is_overdue("2026-09-01T00:00:00Z", {OPEN_LABEL, HUMAN_REVIEW_LABEL}, 5, NOW)
    assert not is_overdue("2026-09-01T00:00:00Z", {OPEN_LABEL, BREACH_LABEL}, 5, NOW)
