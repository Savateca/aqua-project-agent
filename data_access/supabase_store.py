from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests

from auth.supabase_auth import _base_url, service_headers


def _now_iso() -> str:
    return datetime.now().isoformat()


def _rest_url(table: str, params: dict[str, str] | None = None) -> str:
    base = f"{_base_url()}/rest/v1/{table}"
    if not params:
        return base
    return f"{base}?{urlencode(params)}"


def _raise_for_error(response: requests.Response) -> None:
    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Erro Supabase: {detail}")


def list_projects_remote(user_id: str) -> list[dict[str, Any]]:
    params = {
        "select": "id,project_name,report_profile,created_at,updated_at",
        "user_id": f"eq.{user_id}",
        "order": "updated_at.desc",
    }
    response = requests.get(_rest_url("projects", params), headers=service_headers(), timeout=30)
    _raise_for_error(response)
    rows = response.json() or []
    return [
        {
            "project_id": row["id"],
            "project_name": row.get("project_name", row["id"]),
            "report_profile": row.get("report_profile", ""),
            "updated_at": row.get("updated_at", ""),
            "created_at": row.get("created_at", ""),
        }
        for row in rows
    ]


def load_project_remote(project_id: str, user_id: str) -> dict[str, Any]:
    project_params = {
        "select": "*",
        "id": f"eq.{project_id}",
        "user_id": f"eq.{user_id}",
        "limit": "1",
    }
    response = requests.get(_rest_url("projects", project_params), headers=service_headers(), timeout=30)
    _raise_for_error(response)
    project_rows = response.json() or []
    project_row = project_rows[0] if project_rows else {}

    inputs_params = {
        "select": "version_no,payload_json,created_at",
        "project_id": f"eq.{project_id}",
        "order": "version_no.desc",
        "limit": "1",
    }
    response = requests.get(_rest_url("project_inputs", inputs_params), headers=service_headers(), timeout=30)
    _raise_for_error(response)
    input_rows = response.json() or []
    input_row = input_rows[0] if input_rows else {}

    results_params = {
        "select": "input_version,results_json,created_at",
        "project_id": f"eq.{project_id}",
        "order": "input_version.desc",
        "limit": "1",
    }
    response = requests.get(_rest_url("project_results", results_params), headers=service_headers(), timeout=30)
    _raise_for_error(response)
    result_rows = response.json() or []
    latest_result = result_rows[0] if result_rows else {}

    return {
        "project_meta": {
            "project_id": project_row.get("id"),
            "project_name": project_row.get("project_name"),
            "author_name": "",
            "report_profile": project_row.get("report_profile", "Produtor"),
            "created_at": project_row.get("created_at"),
            "updated_at": project_row.get("updated_at"),
        },
        "inputs": input_row.get("payload_json", {}),
        "results": latest_result.get("results_json", {}),
    }


def save_project_remote(project_data: dict[str, Any], user_id: str, current_project_id: str | None = None) -> str:
    meta = deepcopy(project_data.get("project_meta", {}))
    inputs = deepcopy(project_data.get("inputs", {}))
    results = deepcopy(project_data.get("results", {}))

    project_name = meta.get("project_name") or inputs.get("project_name") or "Projeto"
    species = inputs.get("species")
    system_type = inputs.get("system_type")
    report_profile = meta.get("report_profile") or inputs.get("report_profile") or "Produtor"

    if current_project_id:
        project_id = current_project_id
        params = {"id": f"eq.{project_id}", "user_id": f"eq.{user_id}"}
        payload = {
            "project_name": project_name,
            "species": species,
            "system_type": system_type,
            "report_profile": report_profile,
            "updated_at": _now_iso(),
        }
        response = requests.patch(
            _rest_url("projects", params),
            headers=service_headers(prefer="return=representation"),
            json=payload,
            timeout=30,
        )
        _raise_for_error(response)
    else:
        payload = {
            "user_id": user_id,
            "project_name": project_name,
            "species": species,
            "system_type": system_type,
            "report_profile": report_profile,
        }
        response = requests.post(
            _rest_url("projects"),
            headers=service_headers(prefer="return=representation"),
            json=payload,
            timeout=30,
        )
        _raise_for_error(response)
        rows = response.json() or []
        if not rows:
            raise RuntimeError("Supabase não retornou o projeto criado.")
        project_id = rows[0]["id"]

    version_params = {
        "select": "version_no",
        "project_id": f"eq.{project_id}",
        "order": "version_no.desc",
        "limit": "1",
    }
    response = requests.get(_rest_url("project_inputs", version_params), headers=service_headers(), timeout=30)
    _raise_for_error(response)
    version_rows = response.json() or []
    last_version = int(version_rows[0]["version_no"]) if version_rows else 0
    next_version = last_version + 1

    response = requests.post(
        _rest_url("project_inputs"),
        headers=service_headers(prefer="return=representation"),
        json={
            "project_id": project_id,
            "version_no": next_version,
            "payload_json": inputs,
        },
        timeout=30,
    )
    _raise_for_error(response)

    response = requests.post(
        _rest_url("project_results"),
        headers=service_headers(prefer="return=representation"),
        json={
            "project_id": project_id,
            "input_version": next_version,
            "results_json": results,
        },
        timeout=30,
    )
    _raise_for_error(response)

    return project_id


def delete_project_remote(project_id: str, user_id: str) -> None:
    params = {"id": f"eq.{project_id}", "user_id": f"eq.{user_id}"}
    response = requests.delete(_rest_url("projects", params), headers=service_headers(), timeout=30)
    _raise_for_error(response)


def duplicate_project_remote(project_id: str, user_id: str, new_name: str | None = None) -> str:
    loaded = load_project_remote(project_id, user_id)
    loaded.setdefault("project_meta", {})["project_id"] = None
    current_name = loaded.get("project_meta", {}).get("project_name") or "Projeto"
    loaded["project_meta"]["project_name"] = new_name or f"{current_name} - cópia"
    if "project_name" in loaded.get("inputs", {}):
        loaded["inputs"]["project_name"] = loaded["project_meta"]["project_name"]
    return save_project_remote(loaded, user_id, current_project_id=None)
