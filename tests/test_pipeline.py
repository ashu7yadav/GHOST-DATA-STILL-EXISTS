from src.status_classifier import classify_case
from src.workflow import run_pipeline


def test_complete_classification():
    case = {"request_type": "DELETE", "workflow_status": "READY", "deletion_requested": True, "authorized_for_deletion": True}
    assert classify_case(case, []) == "COMPLETE"


def test_incomplete_classification():
    case = {"request_type": "DELETE", "workflow_status": "READY", "deletion_requested": True, "authorized_for_deletion": True}
    assert classify_case(case, [{"phase": "FINDING", "system_id": "s", "resource_id": "r", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "e1"}]) == "INCOMPLETE"


def test_not_applicable_classification():
    case = {"request_type": "NO_DELETION", "workflow_status": "NOT_APPLICABLE", "deletion_requested": False, "authorized_for_deletion": False}
    assert classify_case(case, []) == "NOT_APPLICABLE"


def test_real_run_generation(tmp_path):
    result = run_pipeline(tmp_path)
    assert result["total_cases"] == 518
    assert result["status_counts"]["COMPLETE"] > 0
    assert result["status_counts"]["INCOMPLETE"] > 0
    assert result["status_counts"]["NOT_APPLICABLE"] > 0
