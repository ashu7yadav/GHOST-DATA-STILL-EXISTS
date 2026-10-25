from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_identifier(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    text = text.replace(" ", "")
    return text


def _as_records(identifiers: Any) -> list[dict[str, Any]]:
    if identifiers is None:
        return []
    if isinstance(identifiers, pd.DataFrame):
        return identifiers.fillna("").to_dict("records")
    if isinstance(identifiers, list):
        return [dict(item) if isinstance(item, dict) else {} for item in identifiers]
    if isinstance(identifiers, tuple):
        return [dict(item) if isinstance(item, dict) else {} for item in identifiers]
    return [dict(identifiers)] if isinstance(identifiers, dict) else []


def _collect_email_values(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("current_email", "request_email", "email", "new_email", "old_email", "previous_email"):
        values.append(record.get(key, ""))
    historic = record.get("historical_emails", "")
    if isinstance(historic, str):
        values.extend(part.strip() for part in re.split(r"[;,\n]", historic) if part.strip())
    return [normalize_identifier(item) for item in values if item not in (None, "")]


def _collect_phone_values(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("phone", "mobile_phone", "phone_number"):
        value = record.get(key)
        if value not in (None, ""):
            values.append(normalize_identifier(value))
    return values


def resolve_identity(case_row: dict[str, Any], identifiers: Any, audit_log: Any) -> dict[str, Any]:
    case = case_row or {}
    records = _as_records(identifiers)
    audit_rows = _as_records(audit_log)

    case_user = case.get("user_id")
    case_email = normalize_identifier(case.get("current_email") or case.get("request_email") or case.get("email"))
    case_phone = normalize_identifier(case.get("phone") or case.get("mobile_phone") or case.get("phone_number"))

    exact_matches: list[dict[str, Any]] = []
    candidate_matches: list[dict[str, Any]] = []
    historical_matches: list[str] = []
    reasoning: list[str] = []
    seen_user_ids: set[Any] = set()

    for record in records:
        user_id = record.get("user_id")
        emails = _collect_email_values(record)
        phones = _collect_phone_values(record)
        if case_user is not None and user_id is not None and str(case_user) == str(user_id):
            exact_matches.append(record)
            seen_user_ids.add(str(user_id))
            reasoning.append(f"matched user_id {user_id} from identity table")
        if case_email and case_email in emails:
            candidate_matches.append(record)
            reasoning.append(f"matched email {case_email} to record user_id {user_id}")
        if case_phone and case_phone in phones:
            candidate_matches.append(record)
            reasoning.append(f"matched phone {case_phone} to record user_id {user_id}")
        for email in emails:
            if case_email and case_email == email:
                historical_matches.append(email)

    for row in audit_rows:
        match_user = row.get("user_id")
        row_old = normalize_identifier(row.get("old_email") or row.get("previous_email"))
        row_new = normalize_identifier(row.get("new_email") or row.get("email"))
        if case_user is not None and match_user is not None and str(case_user) == str(match_user):
            if row_old:
                historical_matches.append(row_old)
            if row_new:
                historical_matches.append(row_new)
            reasoning.append(f"identity history confirms user_id {match_user}")
        if case_email and row_old and row_old == case_email:
            candidate_matches.append({"user_id": match_user, "source": "audit_log", "match": row_old})
            reasoning.append(f"historical email {row_old} matches request email")

    unique_historical = []
    seen_hist = set()
    for value in historical_matches:
        clean_value = normalize_identifier(value)
        if clean_value and clean_value not in seen_hist:
            unique_historical.append(clean_value)
            seen_hist.add(clean_value)

    user_ids = {str(record.get("user_id")) for record in exact_matches + candidate_matches if record.get("user_id") is not None}
    if exact_matches and len(user_ids) == 1:
        status = "resolved"
    elif len(user_ids) > 1:
        status = "ambiguous"
    elif candidate_matches:
        status = "ambiguous"
    elif not records and not audit_rows:
        status = "unmatched"
    else:
        status = "unmatched"

    if case_user is not None and exact_matches and any(str(record.get("user_id")) != str(case_user) for record in exact_matches):
        status = "conflict"

    return {
        "user_id": case_user,
        "status": status,
        "case_email": case_email,
        "case_phone": case_phone,
        "exact_matches": exact_matches,
        "candidate_matches": candidate_matches,
        "historical_matches": unique_historical,
        "reasoning": reasoning,
        "evidence": [{"source": "identity_table", "record": rec} for rec in exact_matches]
        + [{"source": "audit_log", "record": row} for row in audit_rows if row.get("user_id") == case_user],
    }


__all__ = ["normalize_identifier", "resolve_identity"]
