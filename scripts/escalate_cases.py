"""Label open exception cases that exceed the configured response SLA."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


CONTROL_LABEL = "control:ITGC-SCM-001"
OPEN_LABEL = "control-exception"
HUMAN_REVIEW_LABEL = "human-closure-review"
BREACH_LABEL = "sla-breached"


def gh(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        ["gh", *args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return completed.stdout if capture else ""


def is_overdue(created_at: str, labels: set[str], sla_days: int,
               now: datetime | None = None) -> bool:
    """Return whether an actionable open case has exceeded its response SLA."""
    current = now or datetime.now(timezone.utc)
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return bool(
        OPEN_LABEL in labels
        and HUMAN_REVIEW_LABEL not in labels
        and BREACH_LABEL not in labels
        and current > created + timedelta(days=sla_days)
    )


def main(sla_days: int) -> None:
    gh(
        "label", "create", BREACH_LABEL, "--color", "B60205",
        "--description", "ITGC-SCM-001 response SLA exceeded", "--force",
    )
    issues = json.loads(gh(
        "issue", "list", "--state", "open", "--label", CONTROL_LABEL,
        "--limit", "500", "--json", "number,createdAt,labels,title,url",
        capture=True,
    ))
    for issue in issues:
        labels = {label["name"] for label in issue["labels"]}
        if is_overdue(issue["createdAt"], labels, sla_days):
            gh("issue", "edit", str(issue["number"]), "--add-label", BREACH_LABEL)
            print(f"Escalated issue #{issue['number']}: {issue['title']}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("usage: escalate_cases.py SLA_DAYS")
    main(int(sys.argv[1]))
