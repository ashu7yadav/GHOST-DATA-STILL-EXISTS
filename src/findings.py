from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def _to_dt(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = tuple(sorted((str(k), str(v)) for k, v in item.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def find_checks(case: dict[str, Any] | None, identifiers: Any, data: dict[str, Any] | None) -> list[dict[str, Any]]:
    case = dict(case or {})
    # Ensure no status-label leakage: never use input deletion_status to decide findings
    case.pop("deletion_status", None)

    if not isinstance(data, dict):
        data = {}

    request_type = str(case.get("request_type", "")).strip().upper()
    workflow_status = str(case.get("workflow_status", "")).strip().upper()
    deletion_requested = bool(case.get("deletion_requested", True))
    authorized = bool(case.get("authorized_for_deletion", True))

    if request_type in {"NO_DELETION", "NOT_APPLICABLE", "NOTAPPLICABLE"} or (
        not deletion_requested and not authorized
    ) or workflow_status in {"NOT_APPLICABLE", "NOTAPPLICABLE"}:
        return []

    case_id = str(case.get("case_id", "")).strip()
    audit_cutoff = _to_dt(case.get("audit_at"))
    evidence_files = data.get("evidence_files", []) or []
    system_activity = data.get("system_activity", []) or []
    rules = data.get("deletion_rules", []) or []

    # Get primary evidence ID for this case if available
    case_ev_id = next(
        (str(r.get("evidence_id")) for r in evidence_files if str(r.get("case_id", "")).strip() == case_id and r.get("evidence_id")),
        "",
    )

    findings: list[dict[str, Any]] = []

    # 1. Investigate real evidence files
    for record in evidence_files:
        if str(record.get("case_id", "")).strip() != case_id:
            continue
        ev_id = record.get("evidence_id", record.get("file_name", "")) or case_ev_id
        sys_id = record.get("system_id", "account_service")
        res_id = record.get("resource_id", f"account_{case.get('user_id', 1):03d}")

        # If parsed evidence dict is present
        parsed = record.get("parsed", {})
        content = parsed.get("content", {}) if isinstance(parsed, dict) else {}
        if isinstance(content, dict) and content:
            state = str(content.get("state") or record.get("state", "")).upper()
            ts = _to_dt(content.get("event_time") or record.get("event_time") or record.get("timestamp"))
            sys_id = content.get("system_id") or sys_id
            res_id = content.get("resource_id") or res_id
        else:
            state = str(record.get("state", "")).upper()
            ts = _to_dt(record.get("event_time") or record.get("timestamp"))

        # Check cutoff: evidence after audit cutoff cannot prove cutoff state
        if audit_cutoff is not None and ts is not None and ts > audit_cutoff:
            findings.append({
                "phase": "FINDING",
                "type": "remaining_record",
                "case_id": case_id,
                "system_id": sys_id,
                "resource_id": res_id,
                "operation": "REPORT_REMAINING_RECORD",
                "state": "PRESENT",
                "evidence_id": ev_id,
                "reason": "evidence timestamp is after audit cutoff",
            })
        elif state in {"PRESENT", "ACTIVE", "EXISTS"}:
            category = str(case.get("category", "")).lower()
            op = "REPORT_EXPOSED_PII" if "support_tickets" in category else "REPORT_REMAINING_RECORD"
            findings.append({
                "phase": "FINDING",
                "type": "remaining_record",
                "case_id": case_id,
                "system_id": sys_id,
                "resource_id": res_id,
                "operation": op,
                "state": "PRESENT",
                "evidence_id": ev_id,
                "reason": "record still exists at audit cutoff",
            })

    # 2. Investigate system activity
    for event in system_activity:
        if str(event.get("case_id", "")).strip() != case_id:
            continue
        event_name = str(event.get("event_name", "")).upper()
        if not event_name:
            continue
        ts = _to_dt(event.get("event_time") or event.get("timestamp"))
        if audit_cutoff is not None and ts is not None and ts > audit_cutoff:
            continue
        ev_id = event.get("event_id") or case_ev_id
        sys_id = event.get("system_id") or "sync_service"
        res_id = event.get("resource_id") or f"sync_{case.get('user_id', 1):03d}"

        outcome = str(event.get("outcome", "")).upper()
        if event_name == "SYNC_ACTIVE" or outcome == "ACTIVE" or (("SYNC" in event_name or "EXPORT" in event_name) and outcome == "ACTIVE"):
            if "RESTORE" not in event_name and "BACKUP" not in event_name:
                findings.append({
                    "phase": "FINDING",
                    "type": "active_data_flow",
                    "case_id": case_id,
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "REPORT_ACTIVE_DATA_FLOW",
                    "state": "ACTIVE",
                    "evidence_id": ev_id,
                    "reason": f"active data flow detected: {event_name}",
                })
        if ("RESTORE" in event_name or "BACKUP" in event_name or "RECOVERY" in event_name) and outcome in {"ACTIVE", "ENABLED", "RISK"}:
            findings.append({
                "phase": "FINDING",
                "type": "restore_risk",
                "case_id": case_id,
                "system_id": sys_id,
                "resource_id": res_id,
                "operation": "REPORT_RESTORE_RISK",
                "state": "ACTIVE",
                "evidence_id": ev_id,
                "reason": f"restore or backup path remains active: {event_name}",
            })

    # 3. Check retention policy rules
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        category = str(rule.get("category", "")).lower()
        action = str(rule.get("required_action", "")).upper()
        retention = str(rule.get("retention", "")).lower()
        case_cat = str(case.get("category", "")).lower()
        if category == case_cat and (
            category == "legal_hold" or action == "RETAIN" or ("required" in retention and "not required" not in retention)
        ):
            findings.append({
                "phase": "FINDING",
                "type": "retention_required",
                "case_id": case_id,
                "system_id": "policy_engine",
                "resource_id": case.get("resource_id", case.get("user_id", "unknown")),
                "operation": "REPORT_REMAINING_RECORD",
                "state": "RETAINED",
                "evidence_id": case_ev_id,
                "reason": f"retention rule requires {action} for {category}",
            })

    # 4. Check identity conflicts if identifiers passed
    if isinstance(identifiers, dict) and identifiers.get("status") == "conflict":
        findings.append({
            "phase": "FINDING",
            "type": "identity_conflict",
            "case_id": case_id,
            "system_id": "identity_service",
            "resource_id": f"user_{case.get('user_id', 1):03d}",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": case_ev_id,
            "reason": "conflicting identity match detected",
        })

    return _dedupe(findings)


__all__ = ["find_checks"]
