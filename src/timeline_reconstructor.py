from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def to_datetime(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def reconstruct_timeline(case_row: dict[str, Any], activity: pd.DataFrame, audit_log: pd.DataFrame) -> list[dict[str, Any]]:
    requested_at = to_datetime(case_row.get("requested_at"))
    audit_at = to_datetime(case_row.get("audit_at"))
    timeline = []
    if not activity.empty:
        for _, row in activity.iterrows():
            timestamp = to_datetime(row.get("event_time") or row.get("event_at") or row.get("timestamp"))
            timeline.append({
                "event_name": row.get("event_name"),
                "system_id": row.get("system_id"),
                "resource_id": row.get("resource_id"),
                "timestamp": timestamp,
                "outcome": row.get("outcome"),
                "source": "system_activity",
            })
    if not audit_log.empty:
        for _, row in audit_log.iterrows():
            timestamp = to_datetime(row.get("audit_at") or row.get("event_time") or row.get("changed_at"))
            if timestamp is None:
                continue
            timeline.append({
                "event_name": row.get("event_name") or "identity_change",
                "system_id": row.get("system_id"),
                "resource_id": row.get("resource_id"),
                "timestamp": timestamp,
                "outcome": row.get("change_type"),
                "source": "user_audit_log",
            })
    timeline = [event for event in timeline if event["timestamp"] is not None]
    timeline.sort(key=lambda item: item["timestamp"])
    for event in timeline:
        event["before_request"] = requested_at is not None and event["timestamp"] < requested_at
        event["at_or_after_audit"] = audit_at is not None and event["timestamp"] >= audit_at
    return timeline
