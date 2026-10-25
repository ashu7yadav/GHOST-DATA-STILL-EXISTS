from __future__ import annotations

PHASE_ORDER = {"FINDING": 0, "REMEDIATION": 1, "VERIFICATION": 2}
OPERATION_ORDER = {
    "REPORT_REMAINING_RECORD": 0,
    "REPORT_EXPOSED_PII": 1,
    "REPORT_ACTIVE_DATA_FLOW": 2,
    "REPORT_RESTORE_RISK": 3,
    "DISABLE_DATA_FLOW": 4,
    "BLOCK_RESTORE": 5,
    "DELETE_RECORD": 6,
    "REDACT_RECORD": 7,
    "ANONYMIZE_RECORD": 8,
    "VERIFY_RECORD_ABSENT": 9,
    "VERIFY_RECORD_PRESENT": 10,
    "VERIFY_RECORD_REDACTED": 11,
    "VERIFY_RECORD_ANONYMIZED": 12,
    "VERIFY_DATA_FLOW_DISABLED": 13,
    "VERIFY_RESTORE_BLOCKED": 14,
}


def sort_steps(steps: list[dict]) -> list[dict]:
    def key(item: dict):
        phase = str(item.get("phase", "")).upper()
        op = str(item.get("operation", "")).upper()
        system_id = str(item.get("system_id", "")).lower()
        resource_id = str(item.get("resource_id", "")).lower()
        return (PHASE_ORDER.get(phase, 99), OPERATION_ORDER.get(op, 99), system_id, resource_id)

    return sorted(steps, key=key)


def assign_step_numbers(steps: list[dict]) -> list[dict]:
    numbered = []
    for idx, step in enumerate(sort_steps(steps), start=1):
        new_step = dict(step)
        new_step["step_no"] = idx
        numbered.append(new_step)
    return numbered
