import pandas as pd

from src.workflow import run_pipeline


def test_sample_output_matches_generated_subset(tmp_path):
    run_pipeline(tmp_path)
    full = pd.read_csv(tmp_path / "output.csv")
    sample = pd.read_csv(tmp_path / "dataset" / "sample_output.csv")
    assert len(sample) <= len(full)
    assert set(sample["case_id"]).issubset(set(full["case_id"]))
