from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_rules(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["category", "rule", "required_action", "retention"])
    return pd.read_csv(path)


def required_action_for(category: str, rules: pd.DataFrame) -> str:
    if rules.empty:
        return "DELETE"
    subset = rules[rules["category"].astype(str).str.lower().eq(str(category).lower())]
    if subset.empty:
        return "DELETE"
    action = subset.iloc[0].get("required_action", "DELETE")
    return str(action).upper()


def decision_for_case(case_row: dict, rules: pd.DataFrame) -> dict:
    case_type = str(case_row.get("resource_type", "account")).lower()
    category = case_row.get("category") or case_type
    action = required_action_for(category, rules)
    retention_required = bool(case_row.get("retain_record"))
    return {
        "category": category,
        "required_action": action,
        "retention_required": retention_required,
        "policy_summary": f"{category} -> {action}",
    }
