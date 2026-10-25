from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


def parse_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def parse_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_sqlite_snapshot(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"tables": {}}
    if not path.exists():
        return result
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
        for _, row in tables.iterrows():
            table = row["name"]
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 20;", conn)
                result["tables"][table] = df.to_dict("records")
            except Exception:
                result["tables"][table] = []
        conn.close()
    except Exception:
        return result
    return result


def parse_pdf_file(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""


def parse_evidence_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return {"type": "json", "content": parse_json_file(path)}
    if suffix in {".txt", ".log"}:
        return {"type": "text", "content": parse_text_file(path)}
    if suffix == ".csv":
        return {"type": "csv", "content": pd.read_csv(path).to_dict("records")}
    if suffix in {".db", ".sqlite", ".sqlite3"}:
        return {"type": "sqlite", "content": parse_sqlite_snapshot(path)}
    if suffix == ".pdf":
        return {"type": "pdf", "content": parse_pdf_file(path)}
    return {"type": "unknown", "content": ""}


def load_manifest(base_dir: Path) -> pd.DataFrame:
    manifest_path = base_dir / "dataset" / "evidence_files.csv"
    if not manifest_path.exists():
        return pd.DataFrame(columns=["evidence_id", "file_name", "file_path", "system_id", "resource_id", "case_id"])
    return pd.read_csv(manifest_path)


def collect_evidence_for_case(case_id: str, manifest: pd.DataFrame, evidence_dir: Path) -> list[dict[str, Any]]:
    relevant = []
    if manifest.empty:
        return relevant
    filtered = manifest[manifest["case_id"].astype(str).eq(str(case_id))] if "case_id" in manifest.columns else pd.DataFrame()
    for _, row in filtered.iterrows():
        file_path = evidence_dir / str(row.get("file_name", ""))
        parsed = parse_evidence_file(file_path)
        relevant.append({
            "evidence_id": row.get("evidence_id"),
            "system_id": row.get("system_id"),
            "resource_id": row.get("resource_id"),
            "file_name": row.get("file_name"),
            "file_path": str(file_path),
            "parsed": parsed,
        })
    return relevant
