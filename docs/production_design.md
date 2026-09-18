# Production design

This repository is an executable design, not a production collector. A
production implementation should replace static files with collectors that have read only access and use
versioned collectors while preserving the normalized evidence contract.

## Suggested collection paths

| Domain | Production sources |
|---|---|
| Scope | CMDB, cloud organization/account inventory, Kubernetes cluster registry, Terraform workspace inventory |
| AWS | AWS Config aggregators, Security Hub, CloudTrail Lake |
| Azure | Azure Resource Graph, Azure Policy, Activity Log |
| GCP | Cloud Asset Inventory, Security Command Center, Cloud Audit Logs |
| Kubernetes | API snapshots, admission policy reports, audit logs |
| Infrastructure as code | Terraform Cloud/Enterprise plans and state, approved pull requests, policy as code results |
| Governance | GRC baseline library, change tickets, exception and risk acceptance register |

Collectors should use dedicated identities with read only access, explicit organization
and account scope, timestamps recorded by source servers, immutable landing storage, and a
separately signed manifest. The inventory source remains authoritative;
scanner results alone must not define the population.

## Operating model

1. Freeze the inventory and review window.
2. Collect all provider, IaC, baseline, exception, and change sources.
3. Validate provenance before parsing or evaluation.
4. Reconcile missing observations and baseline assignments as control
   exceptions rather than silently dropping resources.
5. Publish immutable run evidence and route stable finding IDs.
6. Require human approval for remediation, exceptions, risk acceptance, and
   closure. Preserve configuration before and after the change and the exposure period lookback.

Use access controls and retention aligned to the audit evidence policy.
Secrets and raw sensitive configuration should be redacted or tokenized before
case routing. Changes to the evaluator, baselines, mappings, or severity rules
should follow the organization's approved change management process.
