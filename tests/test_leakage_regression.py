import shutil
from pathlib import Path
import pandas as pd
import pytest

from src.workflow import generate_case_steps


def test_status_label_leakage_regression(tmp_path):
    """
    Regression test proving that changing an input reference label does not
    change the evidence-based prediction when all actual evidence remains unchanged.
    """
    root = Path(__file__).resolve().parents[1]
    src_dataset = root / "dataset"

    # Copy dataset to tmp_path
    dst_dataset = tmp_path / "dataset"
    dst_dataset.mkdir(parents=True, exist_ok=True)
    for item in src_dataset.iterdir():
        if item.is_file():
            shutil.copy2(item, dst_dataset / item.name)
        elif item.is_dir() and item.name == "evidence":
            shutil.copytree(item, dst_dataset / "evidence", dirs_exist_ok=True)

    # 1. Run baseline prediction on original dataset
    baseline_steps = generate_case_steps(tmp_path)
    baseline_map = {row["case_id"]: (row["deletion_status"], row["steps_json"]) for row in baseline_steps}

    # 2. Mutate the input deletion_status reference column
    req_path = dst_dataset / "deletion_requests.csv"
    req_df = pd.read_csv(req_path)
    assert "deletion_status" in req_df.columns

    # Invert/scramble labels: COMPLETE -> INCOMPLETE, INCOMPLETE -> COMPLETE, etc.
    scrambled = []
    for val in req_df["deletion_status"]:
        if val == "COMPLETE":
            scrambled.append("INCOMPLETE")
        elif val == "INCOMPLETE":
            scrambled.append("COMPLETE")
        else:
            scrambled.append("COMPLETE")
    req_df["deletion_status"] = scrambled
    req_df.to_csv(req_path, index=False)

    # 3. Run predictions on modified dataset with scrambled reference labels
    mutated_steps = generate_case_steps(tmp_path)
    mutated_map = {row["case_id"]: (row["deletion_status"], row["steps_json"]) for row in mutated_steps}

    # 4. Verify that predictions are 100% identical and unaffected by label tampering
    assert len(mutated_map) == len(baseline_map)
    for case_id, baseline_result in baseline_map.items():
        mutated_result = mutated_map[case_id]
        assert mutated_result[0] == baseline_result[0], (
            f"Leakage detected on {case_id}: status changed from {baseline_result[0]} to {mutated_result[0]}"
        )
        assert mutated_result[1] == baseline_result[1], (
            f"Leakage detected on {case_id}: steps changed when reference label was altered"
        )
