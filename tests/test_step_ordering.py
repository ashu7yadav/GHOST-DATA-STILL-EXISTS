from src.step_sorter import assign_step_numbers, sort_steps


def test_operation_sorting():
    steps = [
        {"phase": "VERIFICATION", "system_id": "b", "resource_id": "r2", "operation": "VERIFY_RECORD_PRESENT", "state": "PRESENT", "evidence_id": "e1"},
        {"phase": "FINDING", "system_id": "a", "resource_id": "r1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "e2"},
        {"phase": "REMEDIATION", "system_id": "a", "resource_id": "r1", "operation": "DISABLE_DATA_FLOW", "state": "DISABLED", "evidence_id": ""},
    ]
    ordered = sort_steps(steps)
    assert ordered[0]["operation"] == "REPORT_REMAINING_RECORD"
    assert ordered[1]["operation"] == "DISABLE_DATA_FLOW"
    assert ordered[2]["operation"] == "VERIFY_RECORD_PRESENT"


def test_step_numbers_are_consecutive():
    steps = [
        {"phase": "FINDING", "system_id": "a", "resource_id": "r1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "e1"},
        {"phase": "FINDING", "system_id": "a", "resource_id": "r2", "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": "e2"},
    ]
    numbered = assign_step_numbers(steps)
    assert [step["step_no"] for step in numbered] == [1, 2]
