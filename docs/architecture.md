# Architecture overview

The audit pipeline is intentionally modular and deterministic.

- `src/data_loader.py` initializes the dataset access layer.
- `src/identity_resolver.py` reconstructs current and historical identity links.
- `src/evidence_parser.py` parses evidence files and the manifest.
- `src/timeline_reconstructor.py` orders relevant events by timestamp.
- `src/policy_engine.py` applies the configured policy rules.
- `src/status_classifier.py` decides COMPLETE/INCOMPLETE/NOT_APPLICABLE.
- `src/remediation_planner.py` builds findings, remediation, and verification steps.
- `src/step_sorter.py` enforces the official phase and operation ordering.
- `src/evidence_validator.py` validates evidence-backed decisions.
- `src/output_generator.py` serializes the final output to CSV.
- `src/workflow.py` orchestrates the end-to-end run.
