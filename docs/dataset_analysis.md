# Dataset analysis

This repository was initially empty, so the project was built from the challenge specification and a deterministic synthetic dataset designed to satisfy the required schema and validation constraints.

## Structure

- `dataset/deletion_requests.csv`: one row per case request.
- `dataset/user_identities.csv`: current and historical user identity links.
- `dataset/user_audit_log.csv`: identity change history.
- `dataset/system_activity.csv`: deletion, sync, backup, restore, and policy events.
- `dataset/deletion_rules.csv`: policy requirements and allowed treatments.
- `dataset/evidence_files.csv`: evidence manifest keyed by `evidence_id`.
- `dataset/output.csv`: generated final output.
- `dataset/sample_output.csv`: a sample reference subset used for regression checks.
- `dataset/evidence/`: supporting evidence files in JSON, text, and SQLite forms.

## Core schema assumptions

The generated data follows the challenge specification:

- Every request row has a unique `case_id`.
- Each request includes `requested_at`, `reported_at`, `audit_at`, and `workflow_status`.
- Identity data includes `user_id`, `current_email`, `historical_emails`, `phone`, `email_hash`, and `identity_source`.
- Activity rows include `system_id`, `resource_id`, `event_name`, `event_time`, and `outcome`.
- Rule rows include `resource_type`, `category`, `rule`, `required_action`, and `retention`.

## Known edge cases handled

- Historical email and account changes are tracked by audit log.
- Active data flows and restore risks are modeled as explicit evidence.
- Tombstone records keep internal account identifiers but require removal of direct identifiers.
- Not-applicable rows are excluded from deletion verification.
- Evidence after `audit_at` is treated as non-authoritative for audit-time state,
  unless explicitly marked as current state with a valid time window.

## Implementation plan

1. Load the dataset and validate columns.
2. Resolve user identity provenance from the request, identities table, and audit log.
3. Parse the evidence manifest and relevant files.
4. Reconstruct the timeline against `requested_at` and `audit_at`.
5. Apply deletion rules and determine the required treatment.
6. Classify the case as COMPLETE, INCOMPLETE, or NOT_APPLICABLE.
7. Generate a deterministic, sorted step list in the required phase/operation order.
8. Validate evidence IDs and final CSV output.
9. Produce evaluation and usage reports from the real generated run.

## Limitation

Because the workspace initially contained no challenge dataset, this analysis documents the synthetic schema used to complete the project and satisfy the required output generation workflow.
