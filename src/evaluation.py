from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def summarize_output(output_path: Path, sample_path: Path | None = None) -> dict:
    df = pd.read_csv(output_path)
    result = {
        "total_requests": len(df),
        "complete": int((df["deletion_status"] == "COMPLETE").sum()),
        "incomplete": int((df["deletion_status"] == "INCOMPLETE").sum()),
        "not_applicable": int((df["deletion_status"] == "NOT_APPLICABLE").sum()),
    }
    if sample_path and sample_path.exists():
        sample = pd.read_csv(sample_path)
        overlap = pd.merge(df, sample, on=["case_id", "deletion_status"], how="outer")
        result["sample_overlap_cases"] = int(overlap["case_id"].nunique())
    return result


def write_evaluation_report(base_dir: Path, output_df: pd.DataFrame, sample_df: pd.DataFrame | None) -> None:
    summary = summarize_output(base_dir / "output.csv", base_dir / "dataset" / "sample_output.csv")
    report = {
        "dataset_summary": summary,
        "sample_reference": {
            "available": sample_df is not None,
            "cases": len(sample_df) if sample_df is not None else 0,
        },
        "status_counts": output_df["deletion_status"].value_counts().to_dict(),
    }
    report_path = base_dir / "evaluation" / "evaluation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Evaluation report\n\n"
        + "## Dataset summary\n\n"
        + f"- Total requests: {summary['total_requests']}\n"
        + f"- COMPLETE: {summary['complete']}\n"
        + f"- INCOMPLETE: {summary['incomplete']}\n"
        + f"- NOT_APPLICABLE: {summary['not_applicable']}\n\n"
        + "## Notes\n\n"
        + json.dumps(report, indent=2),
        encoding="utf-8",
    )


def write_usage_report(base_dir: Path) -> None:
    usage_path = base_dir / "evaluation" / "usage_report.md"
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(
        "# Token usage and cost report\n\n"
        "This run uses deterministic Python processing only, so the model usage is zero.\n\n"
        "- Model provider: none\n"
        "- Exact model name: none\n"
        "- Number of model calls: 0\n"
        "- Input tokens: 0\n"
        "- Output tokens: 0\n"
        "- Total tokens: 0\n"
        "- Average tokens per request: 0\n"
        "- Estimated total cost: $0.00\n"
        "- Estimated cost per request: $0.00\n"
        "- Measurement method: deterministic local processing with no LLM calls\n",
        encoding="utf-8",
    )
