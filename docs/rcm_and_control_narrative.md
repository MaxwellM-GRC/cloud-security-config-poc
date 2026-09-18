# RCM and control narrative

## RCM entry

| Attribute | Definition |
|---|---|
| Control ID | ITGC-SCM-001 |
| Name | Security Configuration Baseline Management |
| Risk category | `security_configuration` |
| Risk | Failure to establish, monitor, and remediate security configuration baselines could weaken safeguards over in scope systems and allow unauthorized access, alteration, or loss of financial data. |
| Control description | Management periodically compares actual security configurations for in scope systems to approved baselines and ensures deviations are remediated or supported by current approved exceptions. |
| Objective | Security configurations remain aligned to approved baselines or documented, approved exceptions. |
| Frequency | Continuous/daily scanning where available; periodic formal review per policy. |
| Population | All in scope cloud accounts, services, hosts, databases, applications, and their approved configuration baselines and exceptions. |
| Evidence | Source manifest, source extracts, resource and change evaluations, findings register, individual case files, and human closure evidence. |

## Control procedure

1. Obtain the authoritative in scope inventory and reconcile every resource to
   exactly one applicable, approved baseline.
2. Verify each source's origin, extraction query, review window, collection
   timestamp, record count, required schema, unique keys, and SHA-256 digest.
3. Compare every required setting in the assigned baseline to the latest
   observed value from the provider or infrastructure as code source.
4. For each deviation, require an approved status, risk assessment, owner,
   approver, approval timestamp, and unexpired end date. Preserve both the
   technical deviation and exception disposition in the evidence.
5. Reconcile security setting changes during the period to an approved ticket
   whose approval precedes implementation.
6. Route each finding to an individual case. A human decides on remediation or
   risk acceptance, performs the lookback, documents root cause and closure
   evidence, and approves closure.

## Linkage between rules and risks

- **SCM-01** addresses coverage risk: unassigned resources can evade policy.
- **SCM-02** addresses hardening risk: actual settings may weaken safeguards.
- **SCM-03** addresses governance risk: deviations may persist without
  accountable, time bound risk acceptance.
- **SCM-04** addresses change risk: manual cloud or IaC changes may bypass
  authorization and review.

## Precision notes

An approved exception is not treated as technical conformance. The setting
evaluation says `approved_exception`, links the exception, and produces no
actionable finding while approval remains valid. Expired, pending, incomplete,
or missing exception records do not suppress findings.

SCM-02 and SCM-03 intentionally produce separate findings for an uncovered
deviation. They represent distinct control failures: the setting is outside
baseline, and the deviation lacks valid governance. Stable finding IDs permit
independent assignment and closure.
