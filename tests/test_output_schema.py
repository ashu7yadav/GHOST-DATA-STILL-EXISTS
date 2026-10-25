import pandas as pd

from src.workflow import run_pipeline


def test_output_has_required_columns_and_case_count(tmp_path):
    result = run_pipeline(tmp_path)
    output = pd.read_csv(tmp_path / "output.csv")
    assert list(output.columns) == ["case_id", "deletion_status", "steps_json"]
    assert len(output) == 518
    assert result["total_cases"] == 518
