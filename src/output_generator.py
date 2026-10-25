from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_output_csv(path: Path, rows: list[dict]) -> None:
    df = pd.DataFrame(rows, columns=["case_id", "deletion_status", "steps_json"])
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.sort_values("case_id", kind="mergesort").reset_index(drop=True)
    df.to_csv(path, index=False)


def steps_to_json_string(steps: list[dict]) -> str:
    return json.dumps(steps, separators=(",", ":"))
