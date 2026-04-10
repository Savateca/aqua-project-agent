from __future__ import annotations

from typing import Any

from aqua_project_agent_gui_dashboard_v1.calculator import calculate_dashboard_project
from aqua_project_agent_gui_dashboard_v1.models import DashboardProjectInput


def normalize_form_data(form_data: dict[str, Any]) -> dict[str, Any]:
    data = dict(form_data)

    # No app, o peso do alevino é informado em gramas.
    if "fingerling_weight_kg" in data and data["fingerling_weight_kg"] is not None:
        value = float(data["fingerling_weight_kg"])
        if value >= 1:
            data["fingerling_weight_kg"] = value / 1000.0

    int_fields = [
        "number_of_units",
        "manual_aerators",
        "manual_parallel_batches",
        "cost_reference_units",
        "fingerling_rounding_base",
        "phase1_meals_per_day",
        "phase2_meals_per_day",
        "phase3_meals_per_day",
        "phase4_meals_per_day",
    ]

    for field in int_fields:
        if field in data and data[field] is not None:
            data[field] = int(data[field])

    return data



def run_project_calculation(form_data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_form_data(form_data)
    project_input = DashboardProjectInput(**normalized)
    return calculate_dashboard_project(project_input)
