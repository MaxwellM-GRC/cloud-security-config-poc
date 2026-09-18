"""Create/update stable GitHub Issues without automatically closing resolved cases."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


CONTROL_LABEL = "control:ITGC-SCM-001"
OPEN_LABEL = "control-exception"
HUMAN_REVIEW_LABEL = "human-closure-review"


def gh(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        ["gh", *args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return completed.stdout if capture else ""


def ensure_labels() -> None:
    labels = (
        (CONTROL_LABEL, "5319E7", "ITGC-SCM-001 control finding"),
        (OPEN_LABEL, "B60205", "Open automated control finding"),
        (HUMAN_REVIEW_LABEL, "FBCA04", "No longer observed; human closure validation required"),
    )
    for name, color, description in labels:
        gh("label", "create", name, "--color", color, "--description", description, "--force")


def main(findings_path: Path, cases_dir: Path) -> None:
    ensure_labels()
    with findings_path.open(newline="", encoding="utf-8") as handle:
        findings = list(csv.DictReader(handle))
    open_issues = json.loads(gh(
        "issue", "list", "--state", "open", "--label", CONTROL_LABEL,
        "--limit", "500", "--json", "number,title,labels", capture=True,
    ))
    issue_by_finding = {
        finding_id: issue
        for issue in open_issues
        for finding_id in [next((token for token in issue["title"].split() if token.startswith("SCM-")), "")]
        if finding_id
    }
    observed: set[str] = set()
    for row in findings:
        finding_id = row["finding_id"]
        observed.add(finding_id)
        body_path = cases_dir / f"{finding_id}.md"
        title = f"[{row['severity'].upper()}] {finding_id} {row['rule_id']} — {row['resource_name']} / {row['setting']}"
        issue = issue_by_finding.get(finding_id)
        if issue:
            gh("issue", "edit", str(issue["number"]), "--title", title, "--body-file", str(body_path),
               "--add-label", OPEN_LABEL, "--remove-label", HUMAN_REVIEW_LABEL)
        else:
            gh("issue", "create", "--title", title, "--body-file", str(body_path),
               "--label", CONTROL_LABEL, "--label", OPEN_LABEL)

    for finding_id, issue in issue_by_finding.items():
        if finding_id not in observed:
            gh("issue", "edit", str(issue["number"]), "--add-label", HUMAN_REVIEW_LABEL,
               "--remove-label", OPEN_LABEL)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: sync_findings.py FINDINGS.csv CASES_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
