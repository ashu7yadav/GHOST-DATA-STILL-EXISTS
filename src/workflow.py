from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from typing import Any

from src.data_loader import load_dataset, write_json
from src.evidence_parser import collect_evidence_for_case, load_manifest
from src.evaluation import write_evaluation_report, write_usage_report
from src.findings import find_checks
from src.identity_resolver import resolve_identity
from src.output_generator import steps_to_json_string, write_output_csv
from src.output_validator import validate_output_csv
from src.policy_engine import decision_for_case, load_rules
from src.remediation_planner import build_steps
from src.status_classifier import classify_case
from src.step_sorter import assign_step_numbers
from src.timeline_reconstructor import reconstruct_timeline
from src.evidence_validator import validate_steps


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _to_dt(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None



def build_synthetic_dataset(base_dir: Path) -> None:
    dataset_dir = base_dir / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = dataset_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    case_rows = []
    identity_rows = []
    audit_rows = []
    activity_rows = []
    rule_rows = [
        {"category": "account", "rule": "remove direct identifiers", "required_action": "REDACT", "retention": "not required"},
        {"category": "profile", "rule": "delete personal profile", "required_action": "DELETE", "retention": "not required"},
        {"category": "analytics", "rule": "anonymize analytics", "required_action": "ANONYMIZE", "retention": "not required"},
        {"category": "support_tickets", "rule": "redact pii from tickets", "required_action": "REDACT", "retention": "ticket records remain"},
        {"category": "backup", "rule": "delete backup copies", "required_action": "DELETE", "retention": "not required"},
        {"category": "legal_hold", "rule": "retain legal records", "required_action": "RETAIN", "retention": "required"},
    ]

    for idx in range(1, 519):
        case_id = f"case_{idx:03d}"
        base_dt = datetime(2024, 1, 1) + timedelta(days=idx)
        requested_at = base_dt - timedelta(hours=4)
        reported_at = base_dt - timedelta(hours=2)
        audit_at = base_dt + timedelta(hours=1)

        if idx <= 18:
            status = "NOT_APPLICABLE"
            request_type = "NO_DELETION"
            deletion_requested = False
            authorized = False
            resource_type = "none"
        elif idx <= 168:
            status = "INCOMPLETE"
            request_type = "DELETE"
            deletion_requested = True
            authorized = True
            resource_type = "profile"
        else:
            status = "COMPLETE"
            request_type = "DELETE"
            deletion_requested = True
            authorized = True
            resource_type = "profile"

        case_rows.append({
            "case_id": case_id,
            "user_id": idx,
            "current_email": f"user{idx}@example.com",
            "request_email": f"user{idx}@example.com",
            "phone": f"+1-555-{1000 + idx % 9000}",
            "requested_at": _iso(requested_at),
            "reported_at": _iso(reported_at),
            "audit_at": _iso(audit_at),
            "workflow_status": "READY",
            "request_type": request_type,
            "deletion_requested": deletion_requested,
            "authorized_for_deletion": authorized,
            "resource_type": resource_type,
            "category": resource_type,
            "deletion_status": status,
        })

        identity_rows.append({
            "user_id": idx,
            "current_email": f"user{idx}@example.com",
            "historical_emails": f"old{idx}@example.com; prior{idx}@example.com",
            "phone": f"+1-555-{1000 + idx % 9000}",
            "email_hash": f"hash_{idx:04d}",
            "identity_source": "synthetic",
        })

        if idx % 7 == 0:
            audit_rows.append({
                "case_id": case_id,
                "user_id": idx,
                "old_email": f"old{idx}@example.com",
                "new_email": f"user{idx}@example.com",
                "audit_at": _iso(base_dt - timedelta(days=15)),
                "event_name": "EMAIL_CHANGED",
                "system_id": "identity_service",
                "resource_id": f"user_{idx}",
            })

        activity_rows.append({
            "case_id": case_id,
            "system_id": "account_service",
            "resource_id": f"account_{idx:03d}",
            "event_name": "DELETE_REQUESTED" if deletion_requested else "NO_REQUEST",
            "event_time": _iso(requested_at),
            "outcome": "REQUESTED",
        })
        activity_rows.append({
            "case_id": case_id,
            "system_id": "analytics_store",
            "resource_id": f"analytics_{idx:03d}",
            "event_name": "ANALYTICS_EXPORTED" if deletion_requested else "NO_ACTIVITY",
            "event_time": _iso(reported_at),
            "outcome": "REPORTED",
        })
        if status == "INCOMPLETE":
            activity_rows.append({
                "case_id": case_id,
                "system_id": "sync_service",
                "resource_id": f"sync_{idx:03d}",
                "event_name": "SYNC_ACTIVE",
                "event_time": _iso(audit_at - timedelta(hours=1)),
                "outcome": "ACTIVE",
            })

    pd.DataFrame(case_rows).to_csv(dataset_dir / "deletion_requests.csv", index=False)
    pd.DataFrame(identity_rows).to_csv(dataset_dir / "user_identities.csv", index=False)
    pd.DataFrame(audit_rows).to_csv(dataset_dir / "user_audit_log.csv", index=False)
    pd.DataFrame(activity_rows).to_csv(dataset_dir / "system_activity.csv", index=False)
    pd.DataFrame(rule_rows).to_csv(dataset_dir / "deletion_rules.csv", index=False)

    evidence_rows = []
    for idx in range(1, 519):
        case_id = f"case_{idx:03d}"
        evidence_id = f"evidence_{idx:03d}"
        file_name = f"{evidence_id}.json"
        evidence_rows.append({
            "evidence_id": evidence_id,
            "case_id": case_id,
            "file_name": file_name,
            "file_path": f"evidence/{file_name}",
            "system_id": "account_service",
            "resource_id": f"account_{idx:03d}",
        })
        payload = {
            "case_id": case_id,
            "system_id": "account_service",
            "resource_id": f"account_{idx:03d}",
            "state": "PRESENT" if idx <= 168 else "ABSENT",
            "event_time": _iso(datetime(2024, 1, 1) + timedelta(days=idx)),
        }
        (evidence_dir / file_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(evidence_rows).to_csv(dataset_dir / "evidence_files.csv", index=False)

    sample_rows = case_rows[:25]
    pd.DataFrame(sample_rows).to_csv(dataset_dir / "sample_deletion_requests.csv", index=False)

    output_df = pd.DataFrame(columns=["case_id", "deletion_status", "steps_json"])
    output_df.to_csv(dataset_dir / "output.csv", index=False)


def generate_case_steps(base_dir: Path) -> list[dict]:
    requests = pd.read_csv(base_dir / "dataset" / "deletion_requests.csv")
    identities = pd.read_csv(base_dir / "dataset" / "user_identities.csv")
    audit = pd.read_csv(base_dir / "dataset" / "user_audit_log.csv")
    activity = pd.read_csv(base_dir / "dataset" / "system_activity.csv")
    rules = load_rules(base_dir / "dataset" / "deletion_rules.csv")
    manifest = load_manifest(base_dir)
    evidence_dir = base_dir / "dataset" / "evidence"

    rows = []
    manifest_by_case = {case_id: manifest[manifest["case_id"].astype(str).eq(str(case_id))] for case_id in requests["case_id"].astype(str).unique()}
    audit_by_case = {case_id: audit[audit["case_id"].astype(str).eq(str(case_id))] if "case_id" in audit.columns else audit.iloc[0:0] for case_id in requests["case_id"].astype(str).unique()}
    activity_by_case = {case_id: activity[activity["case_id"].astype(str).eq(str(case_id))] if "case_id" in activity.columns else activity.iloc[0:0] for case_id in requests["case_id"].astype(str).unique()}

    for _, request in requests.iterrows():
        case = request.to_dict()
        case_id = str(case["case_id"])
        # CRITICAL: Strip any input deletion_status to prevent label leakage.
        # Decisions are made SOLELY from evidence, identity, timeline, cutoff, and policy.
        case.pop("deletion_status", None)

        user_id_val = case.get("user_id")
        case_identities = identities[identities["user_id"].astype(str).eq(str(user_id_val))] if "user_id" in identities.columns else pd.DataFrame()
        case_audit = audit_by_case.get(case_id, pd.DataFrame())
        case_activity = activity_by_case.get(case_id, pd.DataFrame())
        case_manifest = manifest_by_case.get(case_id, pd.DataFrame())

        case_identity = resolve_identity(case, case_identities, case_audit)
        timeline = reconstruct_timeline(case, case_activity, case_audit)
        decision = decision_for_case(case, rules)
        evidence = collect_evidence_for_case(case_id, case_manifest, evidence_dir)

        # Check applicability
        request_type = str(case.get("request_type", "")).strip().upper()
        workflow_status = str(case.get("workflow_status", "")).strip().upper()
        deletion_requested = bool(case.get("deletion_requested", True))
        authorized = bool(case.get("authorized_for_deletion", True))

        if request_type in {"NO_DELETION", "NOT_APPLICABLE", "NOTAPPLICABLE"} or workflow_status in {"NOT_APPLICABLE", "NOTAPPLICABLE"} or (not deletion_requested and not authorized):
            status = "NOT_APPLICABLE"
            steps = []
            valid, issues = validate_steps(status, steps, case_manifest.to_dict("records"))
            rows.append({
                "case_id": case_id,
                "deletion_status": status,
                "steps_json": json.dumps(steps),
                "valid": valid,
                "issues": issues,
                "identity": case_identity,
                "timeline": timeline,
                "decision": decision,
            })
            continue

        # Prepare evidence list for find_checks
        evidence_records = []
        for ev in evidence:
            parsed = ev.get("parsed", {})
            content = parsed.get("content", {}) if isinstance(parsed, dict) else {}
            rec = {
                "case_id": case_id,
                "evidence_id": ev.get("evidence_id"),
                "system_id": ev.get("system_id"),
                "resource_id": ev.get("resource_id"),
                "parsed": parsed,
            }
            if isinstance(content, dict):
                rec["state"] = content.get("state")
                rec["event_time"] = content.get("event_time") or content.get("timestamp")
                rec["system_id"] = content.get("system_id") or rec["system_id"]
                rec["resource_id"] = content.get("resource_id") or rec["resource_id"]
            evidence_records.append(rec)

        # Perform findings investigation grounded in real evidence, system activity, rules, and identity
        findings = find_checks(
            case,
            case_identity,
            {
                "evidence_files": evidence_records,
                "system_activity": case_activity.to_dict("records") if not case_activity.empty else [],
                "deletion_rules": rules.to_dict("records") if not rules.empty else [],
            },
        )

        status = classify_case(case, findings)

        if status == "COMPLETE":
            # For complete cases, verify that the record is absent (or redacted/anonymized)
            # as supported by the real evidence. Never verify present for a complete deletion!
            steps = []
            for ev in evidence:
                ev_id = ev.get("evidence_id", "")
                parsed = ev.get("parsed", {})
                content = parsed.get("content", {}) if isinstance(parsed, dict) else {}
                if isinstance(content, dict) and content:
                    ev_state = str(content.get("state", "ABSENT")).upper()
                    ev_system = content.get("system_id") or ev.get("system_id", "account_service")
                    ev_resource = content.get("resource_id") or ev.get("resource_id", f"account_{int(user_id_val or 1):03d}")
                else:
                    ev_state = "ABSENT"
                    ev_system = ev.get("system_id", "account_service")
                    ev_resource = ev.get("resource_id", f"account_{int(user_id_val or 1):03d}")

                req_action = str(decision.get("required_action", "DELETE")).upper()
                if ev_state == "REDACTED" or req_action == "REDACT":
                    op = "VERIFY_RECORD_REDACTED"
                    st_val = "REDACTED"
                elif ev_state == "ANONYMIZED" or req_action == "ANONYMIZE":
                    op = "VERIFY_RECORD_ANONYMIZED"
                    st_val = "ANONYMIZED"
                else:
                    op = "VERIFY_RECORD_ABSENT"
                    st_val = "ABSENT"

                steps.append({
                    "phase": "VERIFICATION",
                    "system_id": ev_system,
                    "resource_id": ev_resource,
                    "operation": op,
                    "state": st_val,
                    "evidence_id": ev_id,
                })
            if not steps:
                primary_ev_id = str(case_manifest.iloc[0]["evidence_id"]) if not case_manifest.empty else f"evidence_{int(user_id_val or 1):03d}"
                steps = [{
                    "phase": "VERIFICATION",
                    "system_id": "account_service",
                    "resource_id": f"account_{int(user_id_val or 1):03d}",
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": primary_ev_id,
                }]

        elif status == "INCOMPLETE":
            # Build findings, remediation, and verification steps in official ordering
            remediation = []
            verification = []
            primary_ev_id = str(case_manifest.iloc[0]["evidence_id"]) if not case_manifest.empty else f"evidence_{int(user_id_val or 1):03d}"

            clean_findings = []
            for item in findings:
                ev_id = item.get("evidence_id") or primary_ev_id
                clean_findings.append({
                    "phase": "FINDING",
                    "system_id": item["system_id"],
                    "resource_id": item["resource_id"],
                    "operation": item.get("operation", "REPORT_REMAINING_RECORD"),
                    "state": item.get("state", "PRESENT"),
                    "evidence_id": ev_id,
                })

            for item in clean_findings:
                op = item["operation"]
                sys_id = item["system_id"]
                res_id = item["resource_id"]
                ev_id = item["evidence_id"]

                if op == "REPORT_REMAINING_RECORD":
                    remediation.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "DELETE_RECORD",
                        "state": "ABSENT",
                        "evidence_id": "",
                    })
                    verification.append({
                        "phase": "VERIFICATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": ev_id,
                    })
                elif op == "REPORT_EXPOSED_PII":
                    remediation.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REDACT_RECORD",
                        "state": "REDACTED",
                        "evidence_id": "",
                    })
                    verification.append({
                        "phase": "VERIFICATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "VERIFY_RECORD_REDACTED",
                        "state": "REDACTED",
                        "evidence_id": ev_id,
                    })
                elif op == "REPORT_ACTIVE_DATA_FLOW":
                    remediation.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "DISABLE_DATA_FLOW",
                        "state": "DISABLED",
                        "evidence_id": "",
                    })
                    verification.append({
                        "phase": "VERIFICATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "VERIFY_DATA_FLOW_DISABLED",
                        "state": "DISABLED",
                        "evidence_id": ev_id,
                    })
                elif op == "REPORT_RESTORE_RISK":
                    remediation.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "BLOCK_RESTORE",
                        "state": "BLOCKED",
                        "evidence_id": "",
                    })
                    verification.append({
                        "phase": "VERIFICATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "VERIFY_RESTORE_BLOCKED",
                        "state": "BLOCKED",
                        "evidence_id": ev_id,
                    })

            def _dedupe(step_list):
                seen = set()
                out = []
                for s in step_list:
                    k = (s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"])
                    if k not in seen:
                        seen.add(k)
                        out.append(s)
                return out

            steps = _dedupe(clean_findings) + _dedupe(remediation) + _dedupe(verification)
        else:
            steps = []

        steps = assign_step_numbers(steps)
        valid, issues = validate_steps(status, steps, case_manifest.to_dict("records"))
        rows.append({
            "case_id": case_id,
            "deletion_status": status,
            "steps_json": json.dumps(steps),
            "valid": valid,
            "issues": issues,
            "identity": case_identity,
            "timeline": timeline,
            "decision": decision,
        })
    return rows


def run_pipeline(base_dir: Path) -> dict:
    dataset_dir = base_dir / "dataset"
    if not (dataset_dir / "deletion_requests.csv").exists():
        build_synthetic_dataset(base_dir)

    requests = pd.read_csv(dataset_dir / "deletion_requests.csv")
    case_steps = generate_case_steps(base_dir)
    final_rows = []
    for item in case_steps:
        final_rows.append({
            "case_id": item["case_id"],
            "deletion_status": item["deletion_status"],
            "steps_json": steps_to_json_string(item["steps_json"] if isinstance(item["steps_json"], list) else json.loads(item["steps_json"])),
        })

    final_rows = sorted(final_rows, key=lambda row: row["case_id"])
    output_path = base_dir / "output.csv"
    write_output_csv(output_path, final_rows)
    write_output_csv(dataset_dir / "output.csv", final_rows)

    sample_set = pd.read_csv(dataset_dir / "sample_deletion_requests.csv")
    sample_rows = [row for row in final_rows if row["case_id"] in set(sample_set["case_id"].astype(str))]
    sample_path = dataset_dir / "sample_output.csv"
    write_output_csv(sample_path, sample_rows)

    output_df = pd.DataFrame(final_rows)
    sample_df = pd.read_csv(sample_path) if sample_path.exists() else None
    validation = validate_output_csv(output_path)
    write_evaluation_report(base_dir, output_df, sample_df)
    write_usage_report(base_dir)

    return {
        "total_cases": len(requests),
        "generated_output": str(output_path),
        "status_counts": output_df["deletion_status"].value_counts().to_dict(),
        "validation": validation,
    }
