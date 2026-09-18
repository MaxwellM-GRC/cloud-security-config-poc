"""Validate source provenance, completeness, and integrity and fail closed."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .models import SourceStatus


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sources(config: dict, root: Path, manifest_path: Path) -> list[SourceStatus]:
    """Validate each configured extract against an independently retained manifest."""
    if not manifest_path.exists():
        return [
            SourceStatus(source_id=s["id"], path=s["path"], errors=["source manifest is missing"])
            for s in config["sources"]
        ]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return [
            SourceStatus(source_id=s["id"], path=s["path"], errors=[f"manifest is unreadable: {error}"])
            for s in config["sources"]
        ]

    entries = {entry["source_id"]: entry for entry in manifest.get("sources", [])}
    configured_ids = {source["id"] for source in config["sources"]}
    unexpected = sorted(set(entries) - configured_ids)
    statuses: list[SourceStatus] = []

    for source in config["sources"]:
        entry = entries.get(source["id"], {})
        path = root / source["path"]
        status = SourceStatus(
            source_id=source["id"], path=source["path"],
            source_uri=entry.get("source_uri", ""), query=entry.get("query", ""),
            extracted_at=entry.get("extracted_at", ""),
            window_start=entry.get("window_start", ""),
            window_end=entry.get("window_end", ""),
            expected_rows=entry.get("row_count", 0),
            expected_sha256=entry.get("sha256", ""),
        )
        if not entry:
            status.errors.append("source is absent from manifest")
        if not path.exists():
            status.errors.append("source file is missing")
            statuses.append(status)
            continue

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            headers = set(reader.fieldnames or [])
        status.actual_rows = len(rows)
        status.actual_sha256 = file_sha256(path)
        status.missing_columns = sorted(set(source["required_columns"]) - headers)
        keys = [row.get(source["primary_key"], "").strip() for row in rows]
        status.duplicate_keys = sorted({key for key in keys if key and keys.count(key) > 1})
        if any(not key for key in keys):
            status.errors.append("blank primary key")
        if status.expected_rows != status.actual_rows:
            status.errors.append("manifest row count does not match source")
        if not status.expected_sha256 or status.expected_sha256 != status.actual_sha256:
            status.errors.append("manifest SHA-256 does not match source")
        for field in ("source_uri", "query", "extracted_at", "window_start", "window_end"):
            if not getattr(status, field):
                status.errors.append(f"manifest {field} is blank")
        if status.window_start != config["review_window"]["start"] or status.window_end != config["review_window"]["end"]:
            status.errors.append("manifest window does not equal configured review window")
        try:
            extracted = datetime.fromisoformat(status.extracted_at.replace("Z", "+00:00"))
            ended = datetime.fromisoformat(status.window_end.replace("Z", "+00:00"))
            if extracted < ended:
                status.errors.append("extract timestamp precedes review window end")
        except ValueError:
            status.errors.append("manifest timestamp is invalid")
        statuses.append(status)

    if unexpected and statuses:
        statuses[0].errors.append(f"unexpected manifest source(s): {unexpected}")
    return statuses
