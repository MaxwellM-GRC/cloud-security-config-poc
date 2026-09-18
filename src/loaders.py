"""Load the control definition and normalized fictional source extracts."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_evidence(config: dict, root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        source["kind"]: load_csv(root / source["path"])
        for source in config["sources"]
    }
