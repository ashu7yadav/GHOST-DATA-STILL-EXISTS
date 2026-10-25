from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "output.csv"
REQUESTS_PATH = ROOT / "dataset" / "deletion_requests.csv"
SYNTHETIC_CASES_PATH = ROOT / "evaluation" / "synthetic_cases.json"
REPORT_PATH = ROOT / "evaluation" / "evaluation_report.md"
USAGE_PATH = ROOT / "evaluation" / "usage_report.md"


def _status_summary(df: pd.DataFrame) -> dict[str, int]:
    counts = df["deletion_status"].value_counts().to_dict()
    return {
        "COMPLETE": int(counts.get("COMPLETE", 0)),
        "INCOMPLETE": int(counts.get("INCOMPLETE", 0)),
        "NOT_APPLICABLE": int(counts.get("NOT_APPLICABLE", 0)),
    }


def evaluate() -> dict:
    output_df = pd.read_csv(OUTPUT_PATH) if OUTPUT_PATH.exists() else pd.DataFrame(columns=["case_id", "deletion_status", "steps_json"])
    prediction_summary = _status_summary(output_df)

    # Reference labels in dataset (if present, used solely for post-hoc comparison)
    reference_summary = None
    label_match_count = None
    if REQUESTS_PATH.exists():
        req_df = pd.read_csv(REQUESTS_PATH)
        if "deletion_status" in req_df.columns:
            reference_summary = _status_summary(req_df)
            merged = pd.merge(output_df, req_df, on="case_id", suffixes=("_pred", "_ref"))
            label_match_count = int((merged["deletion_status_pred"] == merged["deletion_status_ref"]).sum())

    synthetic = []
    if SYNTHETIC_CASES_PATH.exists():
        synthetic = json.loads(SYNTHETIC_CASES_PATH.read_text(encoding="utf-8"))

    report_lines = [
        "# Evaluation Report — Ghost Data Still Exists Deletion Audit",
        "",
        "## Summary of Predictions (Pipeline Output)",
        "",
        f"- Total Requests Evaluated: {len(output_df)}",
        f"- Predicted COMPLETE: {prediction_summary['COMPLETE']}",
        f"- Predicted INCOMPLETE: {prediction_summary['INCOMPLETE']}",
        f"- Predicted NOT_APPLICABLE: {prediction_summary['NOT_APPLICABLE']}",
        "",
        "## Reference Labels vs Predictions (Post-Hoc Verification)",
        "",
        "Reference labels from `dataset/deletion_requests.csv` are strictly reserved for post-prediction verification and are never leaked into the audit pipeline.",
        "",
    ]

    if reference_summary is not None:
        report_lines.extend([
            f"- Synthetic Reference Cases: {len(output_df)}",
            f"- Reference Status Counts: COMPLETE={reference_summary['COMPLETE']}, INCOMPLETE={reference_summary['INCOMPLETE']}, NOT_APPLICABLE={reference_summary['NOT_APPLICABLE']}",
            f"- Concordance with Synthetic Reference Labels: {label_match_count}/{len(output_df)} cases ({(label_match_count / len(output_df)) * 100:.1f}%)",
        ])
    else:
        report_lines.append("- No reference label column present in deletion_requests.csv.")

    report_lines.extend([
        "",
        "## Synthetic Benchmark Cases",
        "",
    ])
    if synthetic:
        for case in synthetic:
            report_lines.append(f"- **{case['case_id']}**: expected `{case['expected_status']}` — {case['notes']}")
    else:
        report_lines.append("- No individual synthetic reference cases recorded.")

    report_lines.extend([
        "",
        "## Limitations and Methodology",
        "",
        "- **Deterministic Execution**: The entire pipeline operates deterministically via rule-based policy, identity resolution, timeline reconstruction, and evidence verification. No external LLMs or third-party APIs are called.",
        "- **Status-Label Leakage Elimination**: The audit pipeline explicitly isolates the input case attributes from any target reference labels. A regression test proves predictions are identical when reference labels are scrambled.",
        "- **Ground Truth Scope**: The concordance metric measures alignment against the project's synthetic scenario specifications. No broader precision/recall or production accuracy metrics are claimed without an independent third-party audit dataset.",
        "",
        "```json",
        json.dumps({
            "predictions": prediction_summary,
            "synthetic_reference": reference_summary,
            "concordance": label_match_count,
            "total_cases": len(output_df),
        }, indent=2),
        "```",
        "",
    ])
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    usage_lines = [
        "# Token usage and cost report",
        "",
        "This project does not use an LLM or external API for its deletion audit workflow.",
        "",
        "- Model provider: none",
        "- Exact model name: none",
        "- Number of model calls: 0",
        "- Input tokens: 0",
        "- Output tokens: 0",
        "- Total tokens: 0",
        "- Average tokens per request: 0",
        "- Estimated total cost: $0.00",
        "- Estimated cost per request: $0.00",
        "- Measurement method: deterministic local processing with no LLM calls",
        "",
    ]
    USAGE_PATH.write_text("\n".join(usage_lines), encoding="utf-8")

    return {
        "status_counts": prediction_summary,
        "synthetic_reference": reference_summary,
        "concordance": label_match_count,
    }


if __name__ == "__main__":
    print(evaluate())

