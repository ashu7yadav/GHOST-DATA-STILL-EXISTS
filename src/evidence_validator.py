from __future__ import annotations

from typing import Any


def validate_steps(status: str, steps: list[dict[str, Any]], manifest: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    notes: list[str] = []
    if status == "NOT_APPLICABLE":
        return (len(steps) == 0, notes)

    if status == "COMPLETE":
        if not steps:
            return False, ["COMPLETE cases require verification steps."]
        for step in steps:
            if step.get("phase") != "VERIFICATION":
                return False, ["COMPLETE cases must only contain verification steps."]
            if not step.get("evidence_id"):
                return False, ["Verification steps require evidence IDs."]

    if status == "INCOMPLETE":
        seen_finding = any(step.get("phase") == "FINDING" for step in steps)
        if not seen_finding:
            return False, ["INCOMPLETE cases require at least one finding."]

    manifest_ids = {str(item.get("evidence_id", "")) for item in manifest}
    for step in steps:
        evidence_id = str(step.get("evidence_id", ""))
        phase = step.get("phase")
        if phase in {"FINDING", "VERIFICATION"} and status != "NOT_APPLICABLE":
            if not evidence_id:
                return False, [f"Missing evidence ID for step {step}."]
            if evidence_id not in manifest_ids:
                return False, [f"Unknown evidence ID: {evidence_id}."]

    return True, notes
