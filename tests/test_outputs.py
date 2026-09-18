import csv
import json
from pathlib import Path

from src.main import run


ROOT = Path(__file__).parents[1]


def test_evidence_is_rcm_ready_and_population_reconciles(tmp_path):
    result = run(
        ROOT / "config.yaml", ROOT / "data/source_manifest.json", tmp_path,
        run_id="TEST-SCM-001",
    )
    payload = json.loads((tmp_path / "control_evidence.json").read_text(encoding="utf-8"))

    assert result.input_valid
    assert result.population_reconciled
    assert payload["control"]["risk"].startswith("Failure to")
    assert payload["control"]["control_description"].startswith("Management performs")
    assert payload["population"]["inventory_resources"] == 7
    assert payload["population"]["resources_evaluated"] == 7
    assert payload["finding_counts"]["by_rule"] == {
        "SCM-01": 1, "SCM-02": 4, "SCM-03": 4, "SCM-04": 3
    }
    assert payload["automation_boundary"]["mode"] == "human_approval_required"
    assert "mutate_cloud_configuration" in payload["automation_boundary"]["prohibited_actions"]


def test_one_case_and_one_csv_row_exist_per_finding(tmp_path):
    result = run(
        ROOT / "config.yaml", ROOT / "data/source_manifest.json", tmp_path,
        run_id="TEST-SCM-002",
    )
    cases = list((tmp_path / "cases").glob("SCM-*.md"))
    with (tmp_path / "findings.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(cases) == len(rows) == len(result.findings) == 12
    assert {path.stem for path in cases} == {row["finding_id"] for row in rows}
    assert all(
        row["case_owner"] and row["response_sla_days"] and row["remediation"]
        and row["mitigation"] and row["lookback"] and row["root_cause"]
        and row["closure_evidence"] and row["recurrence"]
        and row["human_closure_required"] == "True"
        for row in rows
    )
    assert all("Automation may detect" in path.read_text(encoding="utf-8") for path in cases)


def test_invalid_input_writes_failure_evidence_without_comparison(tmp_path):
    result = run(
        ROOT / "config.yaml", tmp_path / "missing.json", tmp_path / "output",
        run_id="TEST-SCM-003",
    )
    payload = json.loads((tmp_path / "output/control_evidence.json").read_text(encoding="utf-8"))

    assert not result.input_valid
    assert not payload["input_valid"]
    assert not payload["population_reconciled"]
    assert payload["population"]["resources_evaluated"] == 0
    assert payload["findings"] == []


def test_default_run_identifier_is_deterministic_for_same_inputs(tmp_path):
    first = run(
        ROOT / "config.yaml", ROOT / "data/source_manifest.json", tmp_path / "first"
    )
    second = run(
        ROOT / "config.yaml", ROOT / "data/source_manifest.json", tmp_path / "second"
    )

    assert first.run_id == second.run_id
    assert first.run_id.startswith("SCM-")
