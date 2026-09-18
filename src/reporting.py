"""Write reproducible, RCM ready evidence and one case per finding."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .models import ReviewResult


FINDING_COLUMNS = [
    "run_id", "finding_id", "control_id", "rule_id", "severity", "provider",
    "resource_id", "resource_name", "setting", "detail", "evidence_refs",
    "exception_id", "escalation", "remediation", "mitigation", "root_cause",
    "closure_evidence",
]


def build_payload(result: ReviewResult, config: dict) -> dict:
    severity_counts = Counter(item.severity for item in result.findings)
    rule_counts = Counter(item.rule_id for item in result.findings)
    return {
        "schema_version": "1.0",
        "run_id": result.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "control": config["control"], "review_window": config["review_window"],
        "input_valid": result.input_valid,
        "population_reconciled": result.population_reconciled,
        "automation_boundary": config["automation_boundary"],
        "population": {
            "inventory_resources": result.inventory_count,
            "resources_evaluated": result.evaluated_resource_count,
            "configuration_observations": result.configuration_count,
            "changes_evaluated": len(result.change_evaluations),
        },
        "source_provenance": [source.as_dict() for source in result.source_status],
        "finding_counts": {
            "total": len(result.findings),
            "by_severity": dict(sorted(severity_counts.items())),
            "by_rule": dict(sorted(rule_counts.items())),
        },
        "resource_evaluations": result.resource_evaluations,
        "change_evaluations": result.change_evaluations,
        "findings": [finding.as_dict() for finding in result.findings],
    }


def write_outputs(result: ReviewResult, config: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "control_evidence.json").write_text(
        json.dumps(build_payload(result, config), indent=2) + "\n", encoding="utf-8"
    )
    with (output / "findings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINDING_COLUMNS)
        writer.writeheader()
        for finding in result.findings:
            row = {"run_id": result.run_id, **finding.as_dict()}
            row["evidence_refs"] = " | ".join(row["evidence_refs"])
            writer.writerow(row)
    cases = output / "cases"
    cases.mkdir(exist_ok=True)
    for stale_case in cases.glob("SCM-*.md"):
        stale_case.unlink()
    for finding in result.findings:
        case = f"""# Security configuration exception {finding.finding_id}

- **Run ID:** `{result.run_id}`
- **Control / rule:** `{finding.control_id}` / `{finding.rule_id}`
- **Severity:** {finding.severity}
- **Provider / resource:** {finding.provider} / `{finding.resource_id}` ({finding.resource_name})
- **Setting:** `{finding.setting}`
- **Related approved exception record:** `{finding.exception_id or 'none'}`
- **Status:** Open — human decision required

## Detection

{finding.detail}

Evidence references: {', '.join(f'`{item}`' for item in finding.evidence_refs) or 'none'}

## Human approved response checklist

- [ ] Authorized owner approves a remediation or time bound exception decision.
- [ ] Remediation: {finding.remediation}
- [ ] Mitigation / lookback: {finding.mitigation}
- [ ] Root cause: {finding.root_cause}
- [ ] Closure evidence: {finding.closure_evidence}
- [ ] Escalation evaluated: {finding.escalation}
- [ ] Control owner `{config['control']['owner']}` approves closure.

Automation may detect, route, and recommend. It must not change production,
approve an exception, accept risk, or close this case.
"""
        (cases / f"{finding.finding_id}.md").write_text(case, encoding="utf-8")


def print_summary(result: ReviewResult) -> None:
    counts = Counter(item.severity for item in result.findings)
    print("SECURITY CONFIGURATION BASELINE CONTROL")
    print(f"Run ID: {result.run_id}")
    print(f"Input provenance valid: {result.input_valid}")
    print(f"Resources evaluated: {result.evaluated_resource_count}/{result.inventory_count}")
    print(f"Population reconciled: {result.population_reconciled}")
    print(f"Findings: {len(result.findings)} ({dict(sorted(counts.items()))})")
    for item in result.findings:
        print(f"[{item.severity.upper()}] {item.rule_id} {item.provider} {item.resource_id}/{item.setting}: {item.detail}")
