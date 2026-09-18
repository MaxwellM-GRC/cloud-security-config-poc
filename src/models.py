"""Normalized, deterministic control result structures."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256


@dataclass
class SourceStatus:
    source_id: str
    path: str
    source_uri: str = ""
    query: str = ""
    extracted_at: str = ""
    window_start: str = ""
    window_end: str = ""
    expected_rows: int = 0
    actual_rows: int = 0
    expected_sha256: str = ""
    actual_sha256: str = ""
    missing_columns: list[str] = field(default_factory=list)
    duplicate_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_columns and not self.duplicate_keys and not self.errors

    def as_dict(self) -> dict:
        value = asdict(self)
        value["ok"] = self.ok
        return value


@dataclass(frozen=True)
class Finding:
    control_id: str
    rule_id: str
    severity: str
    provider: str
    resource_id: str
    resource_name: str
    setting: str
    detail: str
    evidence_refs: tuple[str, ...]
    exception_id: str
    case_owner: str
    response_sla_days: int
    escalation: str
    remediation: str
    mitigation: str
    lookback: str
    root_cause: str
    closure_evidence: str
    recurrence: str
    human_closure_required: bool

    @property
    def finding_id(self) -> str:
        seed = "|".join(
            (self.control_id, self.rule_id, self.provider, self.resource_id, self.setting)
        )
        return f"SCM-{sha256(seed.encode()).hexdigest()[:16]}"

    def as_dict(self) -> dict:
        value = asdict(self)
        value["finding_id"] = self.finding_id
        value["evidence_refs"] = list(self.evidence_refs)
        return value


@dataclass
class ReviewResult:
    run_id: str
    findings: list[Finding]
    resource_evaluations: list[dict]
    change_evaluations: list[dict]
    source_status: list[SourceStatus]
    inventory_count: int
    evaluated_resource_count: int
    configuration_count: int

    @property
    def input_valid(self) -> bool:
        return bool(self.source_status) and all(source.ok for source in self.source_status)

    @property
    def population_reconciled(self) -> bool:
        evaluated = {row["resource_id"] for row in self.resource_evaluations}
        return self.input_valid and len(evaluated) == self.inventory_count == self.evaluated_resource_count
