from __future__ import annotations

from typing import Any


def classify_case(case_row: dict[str, Any], findings: list[dict[str, Any]] | None = None) -> str:
    findings = findings or []
    request_type = str(case_row.get("request_type", "")).upper()
    workflow = str(case_row.get("workflow_status", "")).upper()
    deletion_requested = bool(case_row.get("deletion_requested", True))
    authorized = bool(case_row.get("authorized_for_deletion", True))

    if request_type in {"NOT_APPLICABLE", "NOTAPPLICABLE", "NO_DELETION"} or (not deletion_requested and not authorized):
        return "NOT_APPLICABLE"
    if workflow == "NOT_APPLICABLE":
        return "NOT_APPLICABLE"
    if findings:
        return "INCOMPLETE"
    return "COMPLETE"
