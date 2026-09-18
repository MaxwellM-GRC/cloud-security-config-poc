"""Command line runner for the ITGC-SCM-001 proof of concept."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .detection import evaluate
from .integrity import validate_sources
from .loaders import load_config, load_evidence
from .models import ReviewResult
from .reporting import print_summary, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--manifest", type=Path, default=Path("data/source_manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--run-id", default="")
    parser.add_argument("--fail-on-findings", action="store_true")
    return parser.parse_args()


def run(config_path: Path, manifest_path: Path, output: Path, run_id: str = "") -> ReviewResult:
    root = config_path.resolve().parent
    config = load_config(config_path)
    source_status = validate_sources(config, root, manifest_path.resolve())
    if not source_status or not all(item.ok for item in source_status):
        result = ReviewResult(
            run_id=run_id or datetime.now(timezone.utc).strftime("SCM-%Y%m%dT%H%M%SZ"),
            findings=[], resource_evaluations=[], change_evaluations=[],
            source_status=source_status, inventory_count=0,
            evaluated_resource_count=0, configuration_count=0,
        )
        write_outputs(result, config, output)
        return result
    evidence = load_evidence(config, root)
    findings, resources, changes = evaluate(config, evidence)
    result = ReviewResult(
        run_id=run_id or datetime.now(timezone.utc).strftime("SCM-%Y%m%dT%H%M%SZ"),
        findings=findings, resource_evaluations=resources, change_evaluations=changes,
        source_status=source_status, inventory_count=len(evidence["inventory"]),
        evaluated_resource_count=len(resources),
        configuration_count=len(evidence["actual_configurations"]),
    )
    write_outputs(result, config, output)
    return result


def main() -> int:
    args = parse_args()
    result = run(args.config, args.manifest, args.output, args.run_id)
    print_summary(result)
    if not result.input_valid or not result.population_reconciled:
        return 3
    if args.fail_on_findings and result.findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
