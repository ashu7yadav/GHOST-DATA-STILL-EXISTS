# Ghost Data Still Exists — AI-Powered Deletion Audit Agent

This project implements a deterministic deletion-audit pipeline for the synthetic hackathon dataset. It resolves identity links, inspects supporting evidence, reconstructs the audit timeline, applies policy rules, and emits a validated CSV report for each case.

## Problem statement

The goal is to decide whether each deletion request is `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`, while verifying that no remaining records, stale backups, or active sync flows create residual privacy risk. The workflow respects the provided policy rules and evidence timestamps instead of guessing from incomplete data.

## Architecture

- `main.py`: entry point used to generate the final output.
- `src/workflow.py`: orchestrates loading, evidence analysis, status classification, and writing output files.
- `src/identity.py` and `src/identity_resolver.py`: normalize and classify identity matches using current and historical identifiers.
- `src/findings.py`: investigates evidence and raises findings when records, sync flows, restore paths, or retention obligations remain.
- `src/policy_engine.py`: applies the configured deletion policy and required action for each category.
- `src/remediation_planner.py` and `src/step_sorter.py`: generate and order the deterministic remediation steps.
- `src/evidence_parser.py` and `src/evidence_validator.py`: parse raw evidence and validate that each step is grounded in the dataset.
- `src/output_generator.py` and `src/output_validator.py`: serialize and validate the final output file.

## How evidence is investigated

Each case is checked against the records in `dataset/evidence_files.csv`, the matching JSON evidence files in `dataset/evidence/`, and `dataset/system_activity.csv`. The search considers:

- Records still present at the audit cutoff.
- Active data flows, sync jobs, or export pipelines.
- Restore or backup paths that can recreate deleted data.
- Retention obligations and tombstone requirements under the configured policy.
- Evidence timestamps relative to `audit_at` so future events are never treated as past proof.

## Identity resolution

The identity layer normalizes identifiers, compares email and phone values, and checks historical email changes from `user_audit_log.csv`. It distinguishes exact matches from ambiguous or conflicting matches, and it refuses to merge records based on weak name-only assumptions.

## Policy and status rules

The pipeline applies the required actions from `dataset/deletion_rules.csv` and classifies each case as one of:

- `COMPLETE`: required deletion and verification are supported by evidence.
- `INCOMPLETE`: material risks remain or verification is missing.
- `NOT_APPLICABLE`: the request or policy says no deletion action is required.

## Install and run

1. Create a virtual environment: `python -m venv .venv`
2. Install dependencies: `pip install -r requirements.txt`
3. Generate output: `python main.py`
4. Run tests: `python -m pytest -q`
5. Run evaluation: `python evaluation/evaluate.py`
6. Launch dashboard: `streamlit run app.py`

## Output validation

The generated CSV at `output.csv` is validated by `src/output_validator.py` before it is written. The validator checks column order, row count, sorting, duplicate handling, status values, and JSON validity.

## Known limitations

- The project uses the supplied synthetic dataset and deterministic rules; there is no official full ground-truth label set for all 518 cases.
- The evaluation report therefore reports actual counts and validation status, but does not claim precision or recall without reference labels.
- The workflow intentionally avoids inventing evidence or silently merging ambiguous identities.

## Submission contents

The final package should include:

- Source code under `src/`
- Generated `output.csv`
- Test suite under `tests/`
- Evaluation reports under `evaluation/`
- Supporting dataset files under `dataset/`
- Final archive `ghost-audit-final.zip`

## Environment notes

- No API keys or secrets are required for the default workflow.
- Status label leakage is strictly prevented: predictions are calculated purely from evidence files, timeline, identity resolution, cutoff, and deletion rules without reading any reference status labels.
- Verified completion: COMPLETE requests generate verified deletion operations (`VERIFY_RECORD_ABSENT`, `VERIFY_RECORD_REDACTED`, etc.) grounded in real evidence.
- An optional LLM integration is not required for this project and is not used in the current implementation.

