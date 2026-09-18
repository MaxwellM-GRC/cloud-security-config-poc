# Evidence contract

## Required source package

| Source | Population purpose | Primary key |
|---|---|---|
| `inventory.csv` | Authoritative in scope resource population | `resource_id` |
| `baselines.csv` | Approved setting requirements by resource type | `requirement_id` |
| `actual_configurations.csv` | Latest provider/IaC observations | `observation_id` |
| `approved_exceptions.csv` | Risk assessed deviations and their lifecycle | `exception_id` |
| `change_records.csv` | Cloud and IaC security setting changes | `change_id` |

`source_manifest.json` is retained separately from the extracts and records,
for every source, its logical origin, extraction query, extraction time, review
window, row count, and SHA-256 digest. Runtime validation also checks required
columns, blank keys, and duplicate keys.

## Output contract

`control_evidence.json` contains:

- the unchanged control language, objective, frequency, and population;
- the run ID, UTC generation time, and review window;
- assertions for input validity and population reconciliation;
- provenance validation for each source;
- inventory and observation counts;
- resource, setting, exception, and change evaluations;
- finding counts and full RCM response fields; and
- the human/automation boundary in force for the run.

`findings.csv` contains stable finding IDs, control and rule IDs, severity,
provider and resource identifiers, affected setting, detail, evidence
references, related exception, escalation, remediation, mitigation/lookback,
root cause prompt, and required closure evidence.

One Markdown case is generated per finding. Case generation is deterministic
for a given control/rule/resource/setting combination, enabling an issue to be
updated across monitoring runs without being duplicated.

## Conditions that fail closed

No comparison is performed when source validation fails. Invalid provenance,
a missing file, an unexpected manifest entry, a schema problem, duplicate or
blank primary keys, row count mismatch, digest mismatch, review window
mismatch, or an extraction before the window ends makes the run invalid.
