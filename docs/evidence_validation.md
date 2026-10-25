# Evidence validation

The validator verifies that every output step is grounded in actual evidence, that the produced operation/state pair is consistent with the case findings, and that the final classification is not stronger than the available evidence supports.

## Validation steps

1. Confirm that a step is assigned to a valid phase and operation within the official ordering.
2. Confirm that the `evidence_id` is present when required.
3. Confirm that the evidence record exists in `dataset/evidence_files.csv`.
4. Confirm that the evidence resource matches the `system_id` and `resource_id` described by the step.
5. Confirm that the event time does not contradict the audit-time cutoff.
6. For proposed remediation steps, require an empty evidence ID and tie each step back to a supported finding or policy requirement.
7. For complete cases, require verification evidence for each required condition.

## Rule set

- `NOT_APPLICABLE` must emit `[]` in `steps_json`.
- `COMPLETE` may include only verification steps.
- `INCOMPLETE` includes findings, remediation, and verification steps.
- Evidence after `audit_at` cannot prove the state as of the audit cutoff.
- No fabricated identifiers are permitted.

## Implementation note

The check is deterministic and is enforced in `src/evidence_validator.py` before writing the final `output.csv`.
