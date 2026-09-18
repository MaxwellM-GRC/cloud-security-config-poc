from pathlib import Path

from src.loaders import load_config


ROOT = Path(__file__).parents[1]


def test_control_metadata_and_language_meet_release_contract():
    config = load_config(ROOT / "config.yaml")
    control = config["control"]
    required = {
        "id", "source_checklist", "risk_category", "risk",
        "control_description", "objective", "activity", "frequency", "owner",
    }

    assert required <= set(control)
    assert control["risk"].startswith("Failure to")
    assert " could " in control["risk"]
    assert control["control_description"].startswith("Management performs")


def test_every_rule_has_sources_and_full_response_guidance():
    config = load_config(ROOT / "config.yaml")
    source_ids = {source["id"] for source in config["sources"]}
    rule_ids = []
    response_fields = {
        "remediation", "mitigation", "lookback", "root_cause",
        "closure_evidence", "escalation", "recurrence",
    }

    for key, rule in config["rules"].items():
        rule_ids.append(rule["control_id"])
        assert rule["control_id"] == key
        assert rule["control_description"]
        assert rule["severity"]
        assert set(rule["source_ids"]) <= source_ids
        assert response_fields <= set(config["rule_responses"][key])
    assert len(rule_ids) == len(set(rule_ids))


def test_readme_uses_required_rule_table_headers_and_decision_boundary():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    config = load_config(ROOT / "config.yaml")

    assert "| Control ID | Control description | Severity |" in readme
    for rule in config["rules"].values():
        expected_row = (
            f"| {rule['control_id']} | {rule['control_description']} | "
            f"{rule['severity'].title()} |"
        )
        assert expected_row in readme
    assert "Automation detects and routes exceptions." in readme
    assert "Authorized people approve" in readme
