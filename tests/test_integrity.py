import json
import shutil
from pathlib import Path

from src.integrity import validate_sources
from src.loaders import load_config


ROOT = Path(__file__).parents[1]


def test_fixture_sources_have_valid_provenance():
    config = load_config(ROOT / "config.yaml")
    statuses = validate_sources(config, ROOT, ROOT / "data/source_manifest.json")

    assert len(statuses) == len(config["sources"])
    assert all(item.ok for item in statuses)
    assert all(item.actual_rows == item.expected_rows for item in statuses)


def test_missing_manifest_fails_every_source_closed(tmp_path):
    config = load_config(ROOT / "config.yaml")
    statuses = validate_sources(config, ROOT, tmp_path / "missing.json")

    assert statuses
    assert not any(item.ok for item in statuses)
    assert all("source manifest is missing" in item.errors for item in statuses)


def test_tampered_extract_fails_digest_and_count(tmp_path):
    shutil.copytree(ROOT / "data", tmp_path / "data")
    target = tmp_path / "data/inventory.csv"
    target.write_text(target.read_text(encoding="utf-8") + "extra,AWS,x,x,x,true,x,x,x\n", encoding="utf-8")
    config = load_config(ROOT / "config.yaml")
    statuses = validate_sources(config, tmp_path, tmp_path / "data/source_manifest.json")
    inventory = next(item for item in statuses if item.source_id == "in_scope_inventory")

    assert not inventory.ok
    assert "manifest row count does not match source" in inventory.errors
    assert "manifest SHA-256 does not match source" in inventory.errors


def test_unexpected_manifest_source_fails_closed(tmp_path):
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text(encoding="utf-8"))
    manifest["sources"].append({"source_id": "unconfigured_feed"})
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    config = load_config(ROOT / "config.yaml")
    statuses = validate_sources(config, ROOT, path)

    assert not all(item.ok for item in statuses)
    assert "unexpected manifest source" in statuses[0].errors[-1]
