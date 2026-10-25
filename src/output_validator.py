from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


VALID_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}


def validate_output_csv(path: str | Path) -> dict:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing output file: {csv_path}")

    df = pd.read_csv(csv_path)
    expected_cols = ["case_id", "deletion_status", "steps_json"]
    if list(df.columns) != expected_cols:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")

    if len(df) != 518:
        raise ValueError(f"Expected 518 rows, found {len(df)}")

    if df["case_id"].duplicated().any():
        raise ValueError("Duplicate case IDs found")

    if df["case_id"].tolist() != sorted(df["case_id"].tolist()):
        raise ValueError("Case IDs are not sorted")

    invalid_status = set(df["deletion_status"]) - VALID_STATUSES
    if invalid_status:
        raise ValueError(f"Invalid statuses found: {sorted(invalid_status)}")

    # Validate per-row JSON and step structure for non-NOT_APPLICABLE rows.
    for index, row in df.iterrows():
        step_text = row["steps_json"]
        if pd.isna(step_text):
            raise ValueError(f"Missing steps_json for {row['case_id']}")
        try:
            steps = json.loads(step_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON for {row['case_id']}: {exc}") from exc

        if row["deletion_status"] == "NOT_APPLICABLE":
            if steps != []:
                raise ValueError(f"NOT_APPLICABLE case {row['case_id']} must have empty steps")
            continue

        if not isinstance(steps, list):
            raise ValueError(f"steps_json must decode to a list for {row['case_id']}")

        required_ops = {"phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError(f"Malformed step in {row['case_id']}")
            missing = required_ops - set(step)
            if missing:
                raise ValueError(f"Missing required fields in {row['case_id']}: {sorted(missing)}")

    return {"rows": int(len(df)), "statuses": df["deletion_status"].value_counts().to_dict()}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate the deletion audit output CSV.")
    parser.add_argument("path", nargs="?", default="output.csv")
    args = parser.parse_args()
    result = validate_output_csv(args.path)
    print(result)
