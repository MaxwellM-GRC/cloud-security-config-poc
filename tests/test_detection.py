from pathlib import Path

from src.detection import evaluate
from src.loaders import load_config, load_evidence


ROOT = Path(__file__).parents[1]


def review():
    config = load_config(ROOT / "config.yaml")
    evidence = load_evidence(config, ROOT)
    return config, evidence, evaluate(config, evidence)


def test_all_four_catalog_rules_are_exercised():
    _, _, (findings, resources, changes) = review()

    assert {item.rule_id for item in findings} == {"SCM-01", "SCM-02", "SCM-03", "SCM-04"}
    assert len(resources) == 7
    assert len(changes) == 6
    assert len(findings) == 12


def test_valid_approved_exception_is_preserved_without_actionable_finding():
    _, _, (findings, resources, _) = review()

    azure = next(row for row in resources if row["resource_id"] == "az-st-001")
    public_setting = next(row for row in azure["settings"] if row["setting"] == "public_network_access")
    assert public_setting["status"] == "approved_exception"
    assert public_setting["exception_id"] == "EX-001"
    assert not any(item.resource_id == "az-st-001" for item in findings)


def test_expired_and_pending_exceptions_do_not_suppress_findings():
    _, _, (findings, _, _) = review()

    pairs = {(item.rule_id, item.resource_id, item.exception_id) for item in findings}
    assert ("SCM-03", "gcp-bq-001", "EX-002") in pairs
    assert ("SCM-03", "k8s-deploy-001", "EX-003") in pairs


def test_missing_baseline_and_unapproved_changes_are_reported():
    _, _, (findings, _, changes) = review()

    assert any(item.rule_id == "SCM-01" and item.resource_id == "aws-ec2-001" for item in findings)
    failed_changes = {row["change_id"] for row in changes if row["result"] == "exception"}
    assert failed_changes == {"CHG-101", "CHG-103", "CHG-105"}


def test_immediate_escalation_settings_become_critical():
    _, _, (findings, _, _) = review()

    assert all(
        item.severity == "critical"
        for item in findings
        if item.setting in {"public_access", "audit_logging", "ingress_cidr"}
    )


def test_finding_ids_are_stable_and_unique():
    _, _, (findings, _, _) = review()

    ids = [item.finding_id for item in findings]
    assert len(ids) == len(set(ids))
    assert ids == [item.finding_id for item in review()[2][0]]
