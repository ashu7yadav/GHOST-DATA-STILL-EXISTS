from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_dataset(base_dir: Path) -> dict[str, pd.DataFrame]:
    files = {
        "deletion_requests": base_dir / "dataset" / "deletion_requests.csv",
        "sample_deletion_requests": base_dir / "dataset" / "sample_deletion_requests.csv",
        "sample_output": base_dir / "dataset" / "sample_output.csv",
        "user_identities": base_dir / "dataset" / "user_identities.csv",
        "user_audit_log": base_dir / "dataset" / "user_audit_log.csv",
        "system_activity": base_dir / "dataset" / "system_activity.csv",
        "deletion_rules": base_dir / "dataset" / "deletion_rules.csv",
        "evidence_files": base_dir / "dataset" / "evidence_files.csv",
        "output": base_dir / "dataset" / "output.csv",
    }
    return {name: read_csv(path) for name, path in files.items()}


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
