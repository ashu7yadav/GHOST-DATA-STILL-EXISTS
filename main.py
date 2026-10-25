from pathlib import Path

from src.workflow import run_pipeline


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    run_pipeline(project_root)
