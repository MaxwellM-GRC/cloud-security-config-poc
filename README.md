# Cloud Security Configuration Baseline Management — Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cloud-security-config-poc/actions/workflows/ci.yml/badge.svg)

**A standalone, cloud native implementation of ITGC-SCM-001 that reconciles
the complete in scope inventory to approved baselines, observed configuration,
approved exceptions, and change records.**

> **Sanitized.** Every person, organization, account, resource, ticket, and
> source URI in this repository is fictional. No employer, client, or
> production data is present.

## What the control does

The proof of concept implements the portfolio control language without
changing its intent:

> Management periodically compares actual security configurations for
> in scope systems to approved baselines and ensures deviations are remediated
> or supported by current approved exceptions.

It evaluates the full fictional population across:

- AWS Config snapshots for S3, RDS, and EC2 inventory;
- Azure Policy state for a storage account;
- Google Cloud Security Command Center state for BigQuery;
- Kubernetes policy results for a production workload; and
- Terraform Cloud plan/state evidence for a network module.

The data intentionally demonstrates conforming resources, an approved and
unexpired Azure exception, expired and pending exceptions, an unassigned
baseline, unsafe drift, and cloud/IaC changes without timely approval.

## Rules implemented

| Rule | Test | Default severity |
|---|---|---|
| SCM-01 | Every in scope system has an applicable approved baseline. | High |
| SCM-02 | Actual settings conform to the assigned baseline. | High |
| SCM-03 | Deviations have a current, risk assessed, approved exception. | High |
| SCM-04 | Security setting changes trace to approval completed before the change. | High |

Internet exposure and disabled logging or encryption are raised to critical
under the documented parameter. A valid exception makes the deviation an
`approved_exception` in the setting evaluation and prevents an
actionable finding; it does not rewrite the observed technical state.

## How it works

```text
in scope inventory ────────┐
approved baselines ────────┤
AWS/Azure/GCP/K8s/IaC state├─> provenance gate ─> full population comparison
approved exceptions ───────┤                         │
cloud and IaC changes ─────┘                         ├─> RCM evidence JSON
                                                     ├─> findings CSV
                                                     └─> one case owned by a human for each finding
```

The provenance gate fails closed if any configured extract is missing,
altered, incomplete, duplicated, outside the configured review window, or
missing its source URI, query, collection timestamp, row count, or fingerprint.
The comparison does not run on invalid inputs, so a broken feed cannot produce
a misleading clean report.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.main
```

The run writes:

```text
output/
  control_evidence.json    Run metadata, provenance, population, evaluations, findings
  findings.csv             RCM ready exception register with one row for each finding
  cases/SCM-*.md           Individual response and closure case files
```

Exit codes are `0` for a valid completed review, `2` when
`--fail-on-findings` is requested and findings exist, and `3` when input
integrity or population reconciliation fails.

## Human decision boundary

Automation collects evidence, compares settings, detects exceptions,
recommends a response, and routes cases. It cannot mutate cloud
configuration, approve an exception, accept risk, or close a case. Each case
requires an accountable human to approve the response, complete the exposure
lookback, document root cause, attach closure evidence, and approve closure.

## Continuous monitoring

- `ci.yml` tests the evaluator and runs a reproducible sample review on every
  pull request and push.
- `control-monitor.yml` runs on weekdays or on demand, uploads the evidence,
  creates or updates a GitHub Issue per finding, labels findings that are no
  longer observed for human closure review, and then alerts with a failing job when the
  seeded sample contains findings.

The monitor never closes an Issue automatically. A missing finding can mean
remediation, a collection gap, or a scope change; human verification remains
required.

## Repository map

```text
config.yaml                 RCM control, rules, responses, sources, boundaries
data/                       Fictional evidence from multiple clouds and IaC
data/source_manifest.json   Query provenance, counts, windows, SHA-256 hashes
src/                        Integrity, comparison, evaluation, and reporting code
tests/                      Rule, integrity, reconciliation, and output tests
docs/                       Evidence contract, RCM narrative, production design
.github/workflows/          CI and scheduled control monitoring
```

See [the RCM narrative](docs/rcm_and_control_narrative.md),
[evidence contract](docs/evidence_contract.md), and
[production design](docs/production_design.md) for audit and implementation
detail.

MIT licensed.
