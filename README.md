# Cloud Security Configuration Baseline Management — Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cloud-security-config-poc/actions/workflows/ci.yml/badge.svg)

This cloud native control detects baseline drift by correlating the full in
scope inventory with AWS Config, Azure Policy, Google Cloud Security Command
Center, Kubernetes policy, Terraform Cloud, approved baseline, exception, and
change evidence.

> **Sanitized data.** All names, people, organizations, systems, accounts, and
> records in this repository are fictional. No employer, client, or production
> data is included.

## The problem it catches

A scanner can report individual settings without showing whether every in
scope system was scanned, whether its baseline was approved, or whether a
deviation has valid risk acceptance. That can leave an auditor with a clean
dashboard but no evidence that the population was complete.

The fictional data demonstrates issues that require different responses:

- an AWS RDS instance becomes publicly accessible through an unapproved
  change;
- Google Cloud audit logging is disabled after its exception expires;
- a Kubernetes workload runs as root while its exception remains pending;
- a Terraform module permits internet ingress without prior approval;
- an AWS EC2 instance enters scope without a baseline assignment; and
- an Azure storage deviation is correctly supported by a current, independently
  approved exception.

The control preserves an approved exception as `approved_exception`. It does
not rewrite the observed technical state or treat risk acceptance as baseline
conformance.

## What this control tests

| Rule ID | Control assertion | Severity |
|---|---|---|
| SCM-01 | Every in scope system has an applicable approved baseline. | High |
| SCM-02 | Actual configuration settings conform to the applicable baseline. | High |
| SCM-03 | Deviations have a current, risk assessed, approved exception or remediation plan. | High |
| SCM-04 | Security setting changes trace to approved change management evidence. | High |

Internet exposure and disabled logging or encryption are raised to critical
under the documented control parameter.

## How it works

```text
in scope inventory ────────┐
approved baselines ────────┤
AWS/Azure/GCP/K8s/IaC state├─> provenance gate ─> full population comparison
approved exceptions ───────┤                         │
cloud and IaC changes ─────┘                         ├─> RCM evidence JSON
                                                     ├─> findings CSV
                                                     └─> one exception case for each finding
```

1. The source provenance gate verifies every source URI, query, collection
   time, review window, row count, schema, primary key, and SHA-256 digest.
   The control fails closed and performs no comparison if an input is invalid.
2. Population reconciliation evaluates every inventory resource, including a
   resource that lacks a baseline or configuration observations.
3. Rule evaluation compares each observed value to an approved baseline,
   validates exception approval and expiration, and confirms that approval
   preceded each security setting change.
4. Reporting writes RCM ready evidence, a findings register, and one stable
   exception case for each failed rule.

Automation may collect evidence, compare settings, recommend a response, and
route cases. A human must approve remediation or risk acceptance, perform the
exposure lookback, document root cause, attach closure evidence, and approve
closure. Automation cannot mutate cloud configuration, approve an exception,
accept risk, or close a case.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.main
```

The command exits with `0` after a valid review, `2` when
`--fail-on-findings` is requested and findings exist, and `3` when input
integrity or population reconciliation fails.

## Sample output

```text
SECURITY CONFIGURATION BASELINE CONTROL
Input provenance valid: True
Resources evaluated: 7/7
Population reconciled: True
Findings: 12 ({'critical': 9, 'high': 3})
[CRITICAL] SCM-02 AWS aws-rds-001/public_access: Observed value 'true' does not meet approved baseline value 'false'.
[HIGH] SCM-01 AWS aws-ec2-001/baseline_assignment: In scope resource has no applicable, approved baseline assignment.
```

Each run generates:

```text
output/
  control_evidence.json    Provenance, population, evaluations, and findings
  findings.csv             RCM ready register with one row for each finding
  cases/SCM-*.md           Individual human approved response checklists
```

## Continuous monitoring

- `ci.yml` runs all tests and a reproducible sample review on each push and
  pull request.
- `control-monitor.yml` runs at 14:17 UTC each weekday or on demand, uploads
  the evidence package, and creates or updates a GitHub Issue for each stable
  finding ID.
- The monitor raises an alert when actionable findings exist. Its failing
  status is expected for the deliberately seeded sample exceptions.
- The response SLA is five days. Immediate escalation applies to internet
  exposure, disabled logging or encryption, and critical security deviations.
- A finding that is no longer observed receives the
  `human-closure-review` label. Automation never closes its Issue; the control
  owner must verify remediation and approve closure.

## Production design and limitations

This proof of concept uses static fictional extracts and does not connect to a
live cloud tenant. A production design should use collectors with read only,
least privilege access to the CMDB, cloud organization inventory, AWS Config,
Azure Policy, Google Cloud Security Command Center, Kubernetes policy and audit
data, Terraform Cloud, the GRC baseline library, change tickets, and the
approved exception register.

The authoritative inventory must define the full population; scanner results
must not define their own scope. Production collectors should preserve source
timestamps, land evidence in immutable storage, sign the source manifest,
protect sensitive configuration, and retain evidence under the audit policy.
Changes to collectors, baselines, mappings, or severity rules remain subject to
approved change management.

The implementation detects and routes exceptions. It does not prove that a
compensating control operated, decide that residual risk is acceptable, change
a production resource, or determine that an exception case is ready to close.
Those decisions remain human approved.

## Control mapping

| RCM attribute | Definition |
|---|---|
| Control ID | ITGC-SCM-001 |
| Control name | Security Configuration Baseline Management |
| Risk category | `security_configuration` |
| Risk | Failure to establish, monitor, and remediate security configuration baselines could weaken safeguards over in scope systems and allow unauthorized access, alteration, or loss of financial data. |
| Control description | Management performs periodic comparisons of actual security configurations for in scope systems to approved baselines and ensures deviations are remediated or supported by current approved exceptions. |
| Objective | Security configurations remain aligned to approved baselines or documented, approved exceptions. |
| Frequency | Continuous or daily scanning where available, with formal review at the frequency defined by policy. |
| Population | All in scope cloud accounts, services, hosts, databases, applications, and their approved configuration baselines and exceptions. |
| Portfolio framework | SOX ITGC security configuration; portfolio category `security_configuration`. |

The [evidence contract](docs/evidence_contract.md) defines the five required
source packages, provenance assertions, output fields, and conditions that fail
closed. The [RCM narrative](docs/rcm_and_control_narrative.md) documents the
test procedure and rule linkage. The [production design](docs/production_design.md)
describes collector and operating model requirements.

## Repository layout

```text
config.yaml                 RCM metadata, rules, responses, and boundaries
data/                       Fictional cloud, Kubernetes, and IaC evidence
data/source_manifest.json   Query provenance, counts, windows, and digests
src/                        Integrity, evaluation, and reporting code
tests/                      Rule, provenance, population, and output tests
docs/                       Evidence contract, RCM narrative, production design
.github/workflows/          CI and scheduled control monitoring
```

MIT licensed.
