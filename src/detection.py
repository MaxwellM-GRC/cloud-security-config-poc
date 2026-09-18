"""Full population evaluation for ITGC-SCM-001."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from .models import Finding


def _truth(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


def _matches(actual: str, expected: str, comparison: str) -> bool:
    if comparison == "equals":
        return actual.strip().lower() == expected.strip().lower()
    if comparison == "nonempty":
        return bool(actual.strip())
    if comparison == "not_equals":
        return actual.strip().lower() != expected.strip().lower()
    raise ValueError(f"unsupported comparison: {comparison}")


def _valid_exception(row: dict | None, as_of: date) -> bool:
    if not row:
        return False
    try:
        expires = date.fromisoformat(row["expires_on"])
    except (ValueError, KeyError):
        return False
    return bool(
        row.get("status") == "approved"
        and row.get("approved_by")
        and row.get("approved_by") != row.get("requested_by")
        and row.get("approved_at")
        and row.get("risk_assessment_id")
        and row.get("owner")
        and expires >= as_of
    )


def _finding(config: dict, rule_id: str, resource: dict, setting: str, detail: str,
             evidence_refs: list[str], exception_id: str = "", critical: bool = False) -> Finding:
    response = config["rule_responses"][rule_id]
    return Finding(
        control_id=config["control"]["id"], rule_id=rule_id,
        severity="critical" if critical else config["rules"][rule_id]["severity"],
        provider=resource["provider"], resource_id=resource["resource_id"],
        resource_name=resource["resource_name"], setting=setting, detail=detail,
        evidence_refs=tuple(reference for reference in evidence_refs if reference),
        exception_id=exception_id, escalation=response["escalation"],
        remediation=response["remediation"], mitigation=response["mitigation"],
        root_cause=response["root_cause"], closure_evidence=response["closure_evidence"],
    )


def evaluate(config: dict, evidence: dict) -> tuple[list[Finding], list[dict], list[dict]]:
    inventory = evidence["inventory"]
    baselines = evidence["baselines"]
    actual = evidence["actual_configurations"]
    exceptions = evidence["approved_exceptions"]
    changes = evidence["change_records"]
    as_of = date.fromisoformat(config["review_window"]["as_of"])

    requirements: dict[str, dict[str, dict]] = defaultdict(dict)
    baseline_meta: dict[str, dict] = {}
    for row in baselines:
        requirements[row["baseline_id"]][row["setting"]] = row
        baseline_meta[row["baseline_id"]] = row
    actual_by_resource: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in actual:
        actual_by_resource[row["resource_id"]][row["setting"]] = row
    exceptions_by_key = {
        (row["resource_id"], row["setting"]): row for row in exceptions
    }
    resource_by_id = {row["resource_id"]: row for row in inventory}

    findings: list[Finding] = []
    resource_evaluations: list[dict] = []

    for resource in inventory:
        baseline_id = resource["baseline_id"]
        meta = baseline_meta.get(baseline_id)
        assigned = bool(
            baseline_id and meta and meta["status"] == "approved"
            and meta["resource_type"] == resource["resource_type"]
        )
        assertions = {"SCM-01": assigned, "SCM-02": True, "SCM-03": True}
        settings: list[dict] = []
        if not assigned:
            findings.append(_finding(
                config, "SCM-01", resource, "baseline_assignment",
                "In scope resource has no applicable, approved baseline assignment.",
                [resource.get("inventory_source_ref", "")],
            ))
        else:
            for setting, requirement in requirements[baseline_id].items():
                observed = actual_by_resource[resource["resource_id"]].get(setting)
                conforming = bool(observed and _matches(
                    observed["actual_value"], requirement["expected_value"], requirement["comparison"]
                ))
                exception = exceptions_by_key.get((resource["resource_id"], setting))
                exception_valid = _valid_exception(exception, as_of)
                status = "conforming" if conforming else "approved_exception" if exception_valid else "exception"
                settings.append({
                    "setting": setting, "expected_value": requirement["expected_value"],
                    "actual_value": observed["actual_value"] if observed else None,
                    "comparison": requirement["comparison"], "status": status,
                    "exception_id": exception["exception_id"] if exception else "",
                    "source_ref": observed["source_ref"] if observed else "",
                })
                if conforming or exception_valid:
                    continue
                assertions["SCM-02"] = False
                assertions["SCM-03"] = False
                exception_id = exception["exception_id"] if exception else ""
                actual_value = observed["actual_value"] if observed else "<missing>"
                critical = setting in set(config["control_parameters"]["immediate_escalation_settings"])
                references = [resource.get("inventory_source_ref", ""), observed.get("source_ref", "") if observed else "", exception_id]
                findings.append(_finding(
                    config, "SCM-02", resource, setting,
                    f"Observed value {actual_value!r} does not meet approved baseline value {requirement['expected_value']!r}.",
                    references, exception_id, critical,
                ))
                findings.append(_finding(
                    config, "SCM-03", resource, setting,
                    "Baseline deviation lacks a current, risk assessed, formally approved exception.",
                    references, exception_id, critical,
                ))
        resource_evaluations.append({
            "resource_id": resource["resource_id"], "provider": resource["provider"],
            "resource_name": resource["resource_name"], "baseline_id": baseline_id,
            "assertions": assertions, "settings": settings,
            "result": "pass" if all(assertions.values()) else "exception",
        })

    change_evaluations: list[dict] = []
    for change in changes:
        resource = resource_by_id.get(change["resource_id"])
        in_scope = resource is not None
        traceable = bool(
            in_scope and _truth(change["approved"]) and change["change_ticket_id"]
            and change["approved_by"] and change["approved_at"]
            and change["approved_at"] <= change["changed_at"]
        )
        change_evaluations.append({
            "change_id": change["change_id"], "resource_id": change["resource_id"],
            "setting": change["setting"], "in_scope": in_scope,
            "approved_before_change": traceable, "change_ticket_id": change["change_ticket_id"],
            "result": "pass" if traceable else "exception",
        })
        if in_scope and not traceable:
            critical = change["setting"] in set(config["control_parameters"]["immediate_escalation_settings"])
            findings.append(_finding(
                config, "SCM-04", resource, change["setting"],
                f"Security setting change {change['change_id']} does not trace to approval completed before the change.",
                [change["change_id"], change["change_ticket_id"], change["source_ref"]], critical=critical,
            ))

    return findings, resource_evaluations, change_evaluations
