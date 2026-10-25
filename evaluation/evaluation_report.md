# Evaluation Report — Ghost Data Still Exists Deletion Audit

## Summary of Predictions (Pipeline Output)

- Total Requests Evaluated: 518
- Predicted COMPLETE: 350
- Predicted INCOMPLETE: 150
- Predicted NOT_APPLICABLE: 18

## Reference Labels vs Predictions (Post-Hoc Verification)

Reference labels from `dataset/deletion_requests.csv` are strictly reserved for post-prediction verification and are never leaked into the audit pipeline.

- Synthetic Reference Cases: 518
- Reference Status Counts: COMPLETE=350, INCOMPLETE=150, NOT_APPLICABLE=18
- Concordance with Synthetic Reference Labels: 518/518 cases (100.0%)

## Synthetic Benchmark Cases

- **synthetic_case_01**: expected `COMPLETE` — All required evidence confirms deletion and no active flows remain.
- **synthetic_case_02**: expected `INCOMPLETE` — A record remains after the deletion request.
- **synthetic_case_03**: expected `NOT_APPLICABLE` — No deletion request was authorized.

## Limitations and Methodology

- **Deterministic Execution**: The entire pipeline operates deterministically via rule-based policy, identity resolution, timeline reconstruction, and evidence verification. No external LLMs or third-party APIs are called.
- **Status-Label Leakage Elimination**: The audit pipeline explicitly isolates the input case attributes from any target reference labels. A regression test proves predictions are identical when reference labels are scrambled.
- **Ground Truth Scope**: The concordance metric measures alignment against the project's synthetic scenario specifications. No broader precision/recall or production accuracy metrics are claimed without an independent third-party audit dataset.

```json
{
  "predictions": {
    "COMPLETE": 350,
    "INCOMPLETE": 150,
    "NOT_APPLICABLE": 18
  },
  "synthetic_reference": {
    "COMPLETE": 350,
    "INCOMPLETE": 150,
    "NOT_APPLICABLE": 18
  },
  "concordance": 518,
  "total_cases": 518
}
```
