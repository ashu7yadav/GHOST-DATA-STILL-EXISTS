from __future__ import annotations

from typing import Any


def build_findings(case_row: dict[str, Any], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for item in evidence:
        if case_row.get("case_id") and str(item.get("case_id")) != str(case_row.get("case_id")):
            continue
        findings.append({
            "phase": "FINDING",
            "system_id": item.get("system_id", "system"),
            "resource_id": item.get("resource_id", "resource"),
            "operation": item.get("operation", "REPORT_REMAINING_RECORD"),
            "state": item.get("state", "PRESENT"),
            "evidence_id": item.get("evidence_id", ""),
        })
    return findings


def build_remediation(case_row: dict[str, Any], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remediation = []
    for item in findings:
        op = item.get("operation")
        if op == "REPORT_ACTIVE_DATA_FLOW":
            remediation.append({
                "phase": "REMEDIATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "DISABLE_DATA_FLOW",
                "state": "DISABLED",
                "evidence_id": "",
            })
        elif op == "REPORT_RESTORE_RISK":
            remediation.append({
                "phase": "REMEDIATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "BLOCK_RESTORE",
                "state": "BLOCKED",
                "evidence_id": "",
            })
        elif op == "REPORT_REMAINING_RECORD":
            remediation.append({
                "phase": "REMEDIATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "DELETE_RECORD",
                "state": "ABSENT",
                "evidence_id": "",
            })
        elif op == "REPORT_EXPOSED_PII":
            remediation.append({
                "phase": "REMEDIATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "REDACT_RECORD",
                "state": "REDACTED",
                "evidence_id": "",
            })
    return remediation


def build_verification(case_row: dict[str, Any], findings: list[dict[str, Any]], remediation: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verification = []
    for item in findings:
        if item["operation"] == "REPORT_REMAINING_RECORD":
            verification.append({
                "phase": "VERIFICATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": item["evidence_id"],
            })
        if item["operation"] == "REPORT_EXPOSED_PII":
            verification.append({
                "phase": "VERIFICATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "VERIFY_RECORD_REDACTED",
                "state": "REDACTED",
                "evidence_id": item["evidence_id"],
            })
    for item in remediation:
        if item["operation"] == "DISABLE_DATA_FLOW":
            verification.append({
                "phase": "VERIFICATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "VERIFY_DATA_FLOW_DISABLED",
                "state": "DISABLED",
                "evidence_id": "",
            })
        if item["operation"] == "BLOCK_RESTORE":
            verification.append({
                "phase": "VERIFICATION",
                "system_id": item["system_id"],
                "resource_id": item["resource_id"],
                "operation": "VERIFY_RESTORE_BLOCKED",
                "state": "BLOCKED",
                "evidence_id": "",
            })
    return verification


def build_steps(case_row: dict[str, Any], evidence: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
    if status == "NOT_APPLICABLE":
        return []
    findings = build_findings(case_row, evidence)
    remediation = build_remediation(case_row, findings) if status == "INCOMPLETE" else []
    verification = build_verification(case_row, findings, remediation) if status == "INCOMPLETE" else []
    if status == "COMPLETE":
        verification = []
        for ev in evidence:
            ev_id = ev.get("evidence_id", "")
            ev_system = ev.get("system_id", "account_service")
            ev_resource = ev.get("resource_id", f"account_{case_row.get('user_id', 1):03d}")
            ev_state = str(ev.get("state", "ABSENT")).upper()
            if ev_state == "REDACTED":
                op = "VERIFY_RECORD_REDACTED"
            elif ev_state == "ANONYMIZED":
                op = "VERIFY_RECORD_ANONYMIZED"
            else:
                op = "VERIFY_RECORD_ABSENT"
                ev_state = "ABSENT"
            verification.append({
                "phase": "VERIFICATION",
                "system_id": ev_system,
                "resource_id": ev_resource,
                "operation": op,
                "state": ev_state,
                "evidence_id": ev_id,
            })
        if not verification:
            verification = [{
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": f"account_{case_row.get('user_id', 1):03d}",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            }]
    return findings + remediation + verification

