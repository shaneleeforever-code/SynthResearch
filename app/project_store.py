import json
import os
from typing import Any, List, Dict

import pandas as pd


PROJECTS_FILE = "config/projects_store.json"


def serialize_value(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return {
            "__type__": "dataframe",
            "data": value.to_dict(orient="records"),
        }
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    return value


def deserialize_value(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("__type__") == "dataframe":
            return pd.DataFrame(value.get("data", []))
        return {k: deserialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [deserialize_value(v) for v in value]
    return value


def save_projects(projects: List[Dict], path: str = PROJECTS_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serialize_value(projects), f, ensure_ascii=False, indent=2)


def load_projects(path: str = PROJECTS_FILE) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        projects = deserialize_value(data)
        return projects if isinstance(projects, list) else []
    except Exception:
        return []


def _has_rows(value: Any) -> bool:
    if isinstance(value, pd.DataFrame):
        return not value.empty
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def get_project_landing_page(project: Dict) -> int:
    if project.get("report") or project.get("quant_report_text"):
        return 6
    if _has_rows(project.get("interview_results")) or _has_rows(project.get("focus_group_history")) or _has_rows(project.get("quant_results")):
        return 5
    if _has_rows(project.get("personas")):
        return 4
    return 3
