from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECTS_DIR = "projects"


def _slugify(text: str) -> str:
    text = (text or "projeto").strip().lower()
    text = re.sub(r"[^a-z0-9áàâãéèêíïóôõöúçñ_-]+", "_", text, flags=re.IGNORECASE)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "projeto"


def _base_dir(base_dir: str = PROJECTS_DIR) -> Path:
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _project_path(project_id: str, base_dir: str = PROJECTS_DIR) -> Path:
    return _base_dir(base_dir) / f"{project_id}.json"


def generate_project_id(project_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(project_name)
    return f"{ts}_{slug}"


def save_project(project_data: dict[str, Any], base_dir: str = PROJECTS_DIR) -> str:
    meta = project_data.setdefault("project_meta", {})
    project_name = meta.get("project_name", "projeto")

    project_id = meta.get("project_id")
    if not project_id:
        project_id = generate_project_id(project_name)
        meta["project_id"] = project_id

    if "created_at" not in meta:
        meta["created_at"] = datetime.now().isoformat()

    meta["updated_at"] = datetime.now().isoformat()

    path = _project_path(project_id, base_dir)
    path.write_text(
        json.dumps(project_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return project_id


def load_project(project_id: str, base_dir: str = PROJECTS_DIR) -> dict[str, Any]:
    path = _project_path(project_id, base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Projeto não encontrado: {project_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_projects(base_dir: str = PROJECTS_DIR) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []

    for path in sorted(_base_dir(base_dir).glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            meta = data.get("project_meta", {})
            projects.append(
                {
                    "project_id": meta.get("project_id", path.stem),
                    "project_name": meta.get("project_name", path.stem),
                    "report_profile": meta.get("report_profile", ""),
                    "updated_at": meta.get("updated_at", ""),
                    "created_at": meta.get("created_at", ""),
                    "path": str(path),
                }
            )
        except Exception:
            continue

    return projects


def delete_project(project_id: str, base_dir: str = PROJECTS_DIR) -> None:
    path = _project_path(project_id, base_dir)
    if path.exists():
        path.unlink()


def duplicate_project(
    project_id: str,
    new_name: str | None = None,
    base_dir: str = PROJECTS_DIR,
) -> str:
    original = load_project(project_id, base_dir)
    clone = deepcopy(original)

    old_meta = clone.setdefault("project_meta", {})
    clone["project_meta"] = {
        **old_meta,
        "project_id": generate_project_id(new_name or f"{old_meta.get('project_name', 'projeto')}_copia"),
        "project_name": new_name or f"{old_meta.get('project_name', 'Projeto')} - cópia",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    return save_project(clone, base_dir)


def build_project_payload(
    form_data: dict[str, Any],
    results: dict[str, Any],
    current_project_id: str | None = None,
) -> dict[str, Any]:
    report_profile = form_data.get("report_profile", "Produtor")
    project_name = form_data.get("project_name", "Projeto")

    meta = {
        "project_id": current_project_id,
        "project_name": project_name,
        "author_name": form_data.get("author_name", ""),
        "report_profile": report_profile,
    }

    return {
        "project_meta": meta,
        "inputs": form_data,
        "results": results,
    }
