from __future__ import annotations

import math
from dataclasses import asdict

from .models import DashboardProjectInput


DEFAULT_FEEDING_CURVE = [
    {
        "phase_name": "Fase 1",
        "min_g": 1.0,
        "max_g": 100.0,
        "feeding_rate_percent": 5.0,
        "meals_per_day": 4,
        "protein_percent": 40.0,
        "pellet_mm": 1.0,
        "feed_price_per_kg": 4.2,
    },
    {
        "phase_name": "Fase 2",
        "min_g": 100.0,
        "max_g": 300.0,
        "feeding_rate_percent": 3.5,
        "meals_per_day": 4,
        "protein_percent": 36.0,
        "pellet_mm": 2.0,
        "feed_price_per_kg": 4.0,
    },
    {
        "phase_name": "Fase 3",
        "min_g": 300.0,
        "max_g": 700.0,
        "feeding_rate_percent": 2.5,
        "meals_per_day": 3,
        "protein_percent": 32.0,
        "pellet_mm": 4.0,
        "feed_price_per_kg": 3.8,
    },
    {
        "phase_name": "Fase 4",
        "min_g": 700.0,
        "max_g": 1000.0,
        "feeding_rate_percent": 1.8,
        "meals_per_day": 2,
        "protein_percent": 28.0,
        "pellet_mm": 6.0,
        "feed_price_per_kg": 3.5,
    },
]


def temperature_growth_factor(temp_c: float) -> float:
    if temp_c < 20:
        return 0.35
    if temp_c < 22:
        return 0.55
    if temp_c < 24:
        return 0.75
    if temp_c < 26:
        return 0.90
    if temp_c <= 30:
        return 1.00
    if temp_c <= 32:
        return 0.88
    if temp_c <= 34:
        return 0.70
    return 0.45


def protein_growth_factor(protein_percent: float) -> float:
    if protein_percent < 28:
        return 0.85
    if protein_percent < 32:
        return 1.00
    if protein_percent < 36:
        return 1.05
    return 1.08


def round_up_to_base(value: float, base: int) -> int:
    if base <= 1:
        return math.ceil(value)
    return int(math.ceil(value / base) * base)


def resolve_fingerling_purchase_quantity(inp: DashboardProjectInput, theoretical_quantity: float) -> int:
    rounding_mode = getattr(inp, "fingerling_rounding_mode", "Arredondar para cima")
    rounding_base = max(int(getattr(inp, "fingerling_rounding_base", 1000)), 1)
    if rounding_mode == "Arredondar para cima":
        return round_up_to_base(theoretical_quantity, rounding_base)
    return int(round(theoretical_quantity))


def adjusted_daily_growth_g(inp: DashboardProjectInput) -> float:
    proteins = [
        inp.phase1_protein_percent,
        inp.phase2_protein_percent,
        inp.phase3_protein_percent,
        inp.phase4_protein_percent,
    ]
    avg_factor = sum(protein_growth_factor(p) for p in proteins) / len(proteins)
    return max(
        inp.base_daily_growth_g * temperature_growth_factor(inp.water_temperature_c) * avg_factor,
        0.1,
    )


def phase_rows(inp: DashboardProjectInput) -> list[dict]:
    return [
        {
            "phase_name": "Fase 1",
            "min_g": inp.phase1_min_g,
            "max_g": inp.phase1_max_g,
            "feeding_rate_percent": inp.phase1_feeding_rate_percent,
            "meals_per_day": inp.phase1_meals_per_day,
            "protein_percent": inp.phase1_protein_percent,
            "pellet_mm": inp.phase1_pellet_mm,
            "feed_price_per_kg": inp.phase1_feed_price_per_kg,
            "phase_fcr": inp.phase1_fcr,
        },
        {
            "phase_name": "Fase 2",
            "min_g": inp.phase2_min_g,
            "max_g": inp.phase2_max_g,
            "feeding_rate_percent": inp.phase2_feeding_rate_percent,
            "meals_per_day": inp.phase2_meals_per_day,
            "protein_percent": inp.phase2_protein_percent,
            "pellet_mm": inp.phase2_pellet_mm,
            "feed_price_per_kg": inp.phase2_feed_price_per_kg,
            "phase_fcr": inp.phase2_fcr,
        },
        {
            "phase_name": "Fase 3",
            "min_g": inp.phase3_min_g,
            "max_g": inp.phase3_max_g,
            "feeding_rate_percent": inp.phase3_feeding_rate_percent,
            "meals_per_day": inp.phase3_meals_per_day,
            "protein_percent": inp.phase3_protein_percent,
            "pellet_mm": inp.phase3_pellet_mm,
            "feed_price_per_kg": inp.phase3_feed_price_per_kg,
            "phase_fcr": inp.phase3_fcr,
        },
        {
            "phase_name": "Fase 4",
            "min_g": inp.phase4_min_g,
            "max_g": inp.phase4_max_g,
            "feeding_rate_percent": inp.phase4_feeding_rate_percent,
            "meals_per_day": inp.phase4_meals_per_day,
            "protein_percent": inp.phase4_protein_percent,
            "pellet_mm": inp.phase4_pellet_mm,
            "feed_price_per_kg": inp.phase4_feed_price_per_kg,
            "phase_fcr": inp.phase4_fcr,
        },
    ]


def build_feeding_plan(
    inp: DashboardProjectInput,
    fish_stocked: float,
) -> tuple[list[dict], list[dict], list[dict], float, float]:
    feeding_plan: list[dict] = []
    growth_curve: list[dict] = []
    cost_curve: list[dict] = []

    temp_factor = temperature_growth_factor(inp.water_temperature_c)

    total_days = 0.0
    total_feed_kg = 0.0
    cumulative_feed_cost = 0.0
    current_day = 0.0

    for phase in phase_rows(inp):
        start_g = max(inp.initial_weight_g, phase["min_g"])
        end_g = min(inp.target_weight_g, phase["max_g"])

        if end_g <= start_g:
            continue

        phase_growth_g_day = max(
            inp.base_daily_growth_g
            * temp_factor
            * protein_growth_factor(phase["protein_percent"]),
            0.1,
        )

        exact_phase_days = (end_g - start_g) / phase_growth_g_day
        phase_days = max(1, math.ceil(exact_phase_days))

        biomass_start = fish_stocked * (start_g / 1000.0)
        biomass_end = fish_stocked * (end_g / 1000.0)
        biomass_gain = max(biomass_end - biomass_start, 0.0)

        phase_fcr = phase["phase_fcr"]
        feed_phase = biomass_gain * phase_fcr
        cost_phase = feed_phase * phase["feed_price_per_kg"]

        total_feed_kg += feed_phase
        cumulative_feed_cost += cost_phase
        total_days += phase_days

        growth_curve.append(
            {
                "day": current_day,
                "weight_g": start_g,
                "biomass_kg": biomass_start,
            }
        )

        current_day += phase_days

        growth_curve.append(
            {
                "day": current_day,
                "weight_g": end_g,
                "biomass_kg": biomass_end,
            }
        )

        cost_curve.append(
            {
                "day": current_day,
                "cumulative_feed_cost": cumulative_feed_cost,
            }
        )

        feeding_plan.append(
            {
                "phase_name": phase["phase_name"],
                "weight_range": f"{start_g:.0f}-{end_g:.0f} g",
                "days_in_phase": phase_days,
                "feeding_rate_percent": phase["feeding_rate_percent"],
                "meals_per_day": phase["meals_per_day"],
                "protein_percent": phase["protein_percent"],
                "pellet_mm": phase["pellet_mm"],
                "feed_price_per_kg": phase["feed_price_per_kg"],
                "phase_fcr": phase_fcr,
                "biomass_gain_phase_kg": biomass_gain,
                "feed_phase_kg": feed_phase,
                "feed_phase_cost": cost_phase,
                "phase_daily_growth_g": phase_growth_g_day,
            }
        )

    return feeding_plan, growth_curve, cost_curve, total_days, total_feed_kg



def build_production_schedule(
    inp: DashboardProjectInput,
    cycle_days: float,
    production_per_cycle_kg: float,
    production_per_year_kg: float,
    feed_consumption_cycle_kg: float,
    feed_consumption_year_kg: float,
    fish_stocked_per_cycle: float,
    revenue_cycle: float,
    revenue_year: float,
    fingerling_cost_cycle: float,
    fingerling_cost_year: float,
    fingerlings_purchase_cycle: int,
) -> dict:
    strategy = getattr(inp, "production_strategy", "Ciclos simultâneos")
    batch_mode = getattr(inp, "production_batch_mode", "Automático")
    harvest_interval_months = max(getattr(inp, "harvest_interval_months", 1.0), 0.25)
    harvest_interval_days = harvest_interval_months * 30.0

    annual_stocking = fish_stocked_per_cycle * inp.cycles_per_year
    annual_fingerling_purchase = fingerlings_purchase_cycle * inp.cycles_per_year
    automatic_parallel_batches = max(1, math.ceil(cycle_days / harvest_interval_days)) if harvest_interval_days > 0 else 1

    if strategy == "Escalonada":
        if batch_mode == "Personalizado":
            batches_in_parallel = max(1, int(getattr(inp, "manual_parallel_batches", automatic_parallel_batches)))
        else:
            batches_in_parallel = automatic_parallel_batches

        harvests_per_year = max(1.0, 12.0 / harvest_interval_months)
        units_per_batch_exact = inp.number_of_units / batches_in_parallel

        low_units = math.floor(units_per_batch_exact)
        high_units = math.ceil(units_per_batch_exact)

        if abs(units_per_batch_exact - round(units_per_batch_exact)) < 1e-9:
            batch_distribution_note = f"{int(round(units_per_batch_exact))} tanque(s) por lote."
        else:
            high_group_count = inp.number_of_units - (low_units * batches_in_parallel)
            low_group_count = batches_in_parallel - high_group_count
            parts = []
            if high_group_count > 0:
                parts.append(f"{int(high_group_count)} lote(s) com {int(high_units)} tanque(s)")
            if low_group_count > 0:
                parts.append(f"{int(low_group_count)} lote(s) com {int(low_units)} tanque(s)")
            batch_distribution_note = "; ".join(parts) + "."

        production_per_harvest_kg = production_per_year_kg / harvests_per_year
        feed_per_harvest_kg = feed_consumption_year_kg / harvests_per_year
        revenue_per_harvest = revenue_year / harvests_per_year
        fingerling_cost_per_harvest = fingerling_cost_year / harvests_per_year
    else:
        batches_in_parallel = 1
        harvests_per_year = inp.cycles_per_year
        units_per_batch_exact = float(inp.number_of_units)
        batch_distribution_note = f"{int(inp.number_of_units)} tanque(s) em um único lote por ciclo."
        production_per_harvest_kg = production_per_cycle_kg
        feed_per_harvest_kg = feed_consumption_cycle_kg
        revenue_per_harvest = revenue_cycle
        fingerling_cost_per_harvest = fingerling_cost_cycle

    return {
        "production_strategy": strategy,
        "production_batch_mode": batch_mode,
        "automatic_parallel_batches": automatic_parallel_batches,
        "harvest_interval_months": harvest_interval_months,
        "harvest_interval_days": harvest_interval_days,
        "harvests_per_year": harvests_per_year,
        "batches_in_parallel": batches_in_parallel,
        "units_per_batch_exact": units_per_batch_exact,
        "batch_volume_m3": units_per_batch_exact * inp.unit_volume_m3,
        "production_per_harvest_kg": production_per_harvest_kg,
        "feed_per_harvest_kg": feed_per_harvest_kg,
        "revenue_per_harvest": revenue_per_harvest,
        "fingerling_cost_per_harvest": fingerling_cost_per_harvest,
        "fish_stocked_per_harvest": annual_stocking / harvests_per_year if harvests_per_year > 0 else 0.0,
        "fingerlings_purchase_per_harvest": round_up_to_base(annual_fingerling_purchase / harvests_per_year, max(int(getattr(inp, "fingerling_rounding_base", 1000)), 1)) if getattr(inp, "fingerling_rounding_mode", "Arredondar para cima") == "Arredondar para cima" and harvests_per_year > 0 else int(round(annual_fingerling_purchase / harvests_per_year)) if harvests_per_year > 0 else 0,
        "first_harvest_after_days": cycle_days,
        "first_harvest_after_months": cycle_days / 30.0 if cycle_days else 0.0,
        "batch_distribution_note": batch_distribution_note,
    }



def resolve_economic_costs(inp: DashboardProjectInput) -> dict:
    economic_model_mode = getattr(inp, "economic_model_mode", "Simplificado")

    if economic_model_mode == "Fixo + por tanque":
        electricity_fixed = getattr(inp, "electricity_cost_fixed_cycle", 0.0)
        electricity_variable = getattr(inp, "electricity_cost_per_unit_cycle", 0.0) * inp.number_of_units
        labor_fixed = getattr(inp, "labor_cost_fixed_cycle", 0.0)
        labor_variable = getattr(inp, "labor_cost_per_unit_cycle", 0.0) * inp.number_of_units
        other_fixed = getattr(inp, "other_cost_fixed_cycle", 0.0)
        other_variable = getattr(inp, "other_cost_per_unit_cycle", 0.0) * inp.number_of_units
        capex_fixed = getattr(inp, "capex_fixed_total", 0.0)
        capex_variable = getattr(inp, "capex_per_unit", 0.0) * inp.number_of_units

        return {
            "economic_model_mode": economic_model_mode,
            "cost_scaling_mode": getattr(inp, "cost_scaling_mode", "Fixos (não escalar)"),
            "cost_reference_units": max(getattr(inp, "cost_reference_units", max(inp.number_of_units, 1)), 1),
            "cost_scale_factor": 1.0,
            "electricity_cost_cycle_effective": electricity_fixed + electricity_variable,
            "labor_cost_cycle_effective": labor_fixed + labor_variable,
            "other_costs_cycle_effective": other_fixed + other_variable,
            "capex_total_effective": capex_fixed + capex_variable,
            "electricity_cost_fixed_cycle_effective": electricity_fixed,
            "electricity_cost_variable_cycle_effective": electricity_variable,
            "labor_cost_fixed_cycle_effective": labor_fixed,
            "labor_cost_variable_cycle_effective": labor_variable,
            "other_cost_fixed_cycle_effective": other_fixed,
            "other_cost_variable_cycle_effective": other_variable,
            "capex_fixed_total_effective": capex_fixed,
            "capex_variable_total_effective": capex_variable,
        }

    cost_reference_units = max(getattr(inp, "cost_reference_units", max(inp.number_of_units, 1)), 1)
    if getattr(inp, "cost_scaling_mode", "Fixos (não escalar)") == "Escalonar pelo nº de tanques":
        cost_scale_factor = inp.number_of_units / cost_reference_units
    else:
        cost_scale_factor = 1.0

    electricity_cost_cycle_effective = inp.electricity_cost_cycle * cost_scale_factor
    labor_cost_cycle_effective = inp.labor_cost_cycle * cost_scale_factor
    other_costs_cycle_effective = inp.other_costs_cycle * cost_scale_factor
    capex_total_effective = inp.capex_total * cost_scale_factor

    return {
        "economic_model_mode": economic_model_mode,
        "cost_scaling_mode": getattr(inp, "cost_scaling_mode", "Fixos (não escalar)"),
        "cost_reference_units": cost_reference_units,
        "cost_scale_factor": cost_scale_factor,
        "electricity_cost_cycle_effective": electricity_cost_cycle_effective,
        "labor_cost_cycle_effective": labor_cost_cycle_effective,
        "other_costs_cycle_effective": other_costs_cycle_effective,
        "capex_total_effective": capex_total_effective,
        "electricity_cost_fixed_cycle_effective": electricity_cost_cycle_effective,
        "electricity_cost_variable_cycle_effective": 0.0,
        "labor_cost_fixed_cycle_effective": labor_cost_cycle_effective,
        "labor_cost_variable_cycle_effective": 0.0,
        "other_cost_fixed_cycle_effective": other_costs_cycle_effective,
        "other_cost_variable_cycle_effective": 0.0,
        "capex_fixed_total_effective": capex_total_effective,
        "capex_variable_total_effective": 0.0,
    }



def calculate_dashboard_project(inp: DashboardProjectInput) -> dict:
    total_volume_m3 = inp.number_of_units * inp.unit_volume_m3
    final_biomass_total_kg = total_volume_m3 * inp.density_kg_m3

    target_weight_kg = inp.target_weight_g / 1000.0
    fish_harvested = final_biomass_total_kg / target_weight_kg if target_weight_kg > 0 else 0.0
    fish_stocked_theoretical = fish_harvested / inp.survival_rate if inp.survival_rate > 0 else 0.0
    fingerlings_purchase_cycle = resolve_fingerling_purchase_quantity(inp, fish_stocked_theoretical)
    fish_stocked = fish_stocked_theoretical

    feeding_plan, growth_curve, cost_curve, cycle_days, feed_consumption_cycle_kg = build_feeding_plan(
        inp,
        fish_stocked,
    )

    revenue_cycle = final_biomass_total_kg * inp.sale_price_per_kg

    oxygen_demand_kg_h = final_biomass_total_kg * (inp.oxygen_demand_mg_per_kg_h / 1_000_000.0)

    aerator_capacity_each = inp.aerator_hp_each * inp.oxygen_transfer_kg_o2_hp_h

    auto_required_aerators = (
        math.ceil(oxygen_demand_kg_h / aerator_capacity_each)
        if aerator_capacity_each > 0
        else 0
    )

    if inp.aerator_quantity_mode == "Manual":
        required_aerators = max(1, int(inp.manual_aerators))
    else:
        required_aerators = auto_required_aerators

    fingerling_cost_cycle = fingerlings_purchase_cycle * inp.fingerling_price

    aeration_energy_cost_cycle = (
        required_aerators
        * inp.aerator_hp_each
        * 0.746
        * inp.aeration_hours_per_day
        * cycle_days
        * inp.electricity_price_kwh
    )

    economic_costs = resolve_economic_costs(inp)

    cost_reference_units = economic_costs["cost_reference_units"]
    cost_scale_factor = economic_costs["cost_scale_factor"]
    electricity_cost_cycle_effective = economic_costs["electricity_cost_cycle_effective"]
    labor_cost_cycle_effective = economic_costs["labor_cost_cycle_effective"]
    other_costs_cycle_effective = economic_costs["other_costs_cycle_effective"]
    capex_total_effective = economic_costs["capex_total_effective"]

    feed_cost_cycle = sum(item["feed_phase_cost"] for item in feeding_plan)

    opex_cycle = (
        feed_cost_cycle
        + fingerling_cost_cycle
        + electricity_cost_cycle_effective
        + labor_cost_cycle_effective
        + other_costs_cycle_effective
        + aeration_energy_cost_cycle
    )

    gross_margin_cycle = revenue_cycle - opex_cycle

    biomass_initial = fish_stocked * (inp.initial_weight_g / 1000.0)
    biomass_gain = max(final_biomass_total_kg - biomass_initial, 0.0)

    implied_fcr = (
        feed_consumption_cycle_kg / biomass_gain
        if biomass_gain > 0
        else None
    )

    production_per_year_kg = final_biomass_total_kg * inp.cycles_per_year
    feed_consumption_year_kg = feed_consumption_cycle_kg * inp.cycles_per_year
    feed_cost_year = feed_cost_cycle * inp.cycles_per_year
    revenue_year = revenue_cycle * inp.cycles_per_year
    gross_margin_year = gross_margin_cycle * inp.cycles_per_year
    opex_year = opex_cycle * inp.cycles_per_year
    fingerling_cost_year = fingerling_cost_cycle * inp.cycles_per_year
    aeration_energy_cost_year = aeration_energy_cost_cycle * inp.cycles_per_year
    electricity_cost_year = electricity_cost_cycle_effective * inp.cycles_per_year
    labor_cost_year = labor_cost_cycle_effective * inp.cycles_per_year
    other_costs_year = other_costs_cycle_effective * inp.cycles_per_year

    production_schedule = build_production_schedule(
        inp=inp,
        cycle_days=cycle_days,
        production_per_cycle_kg=final_biomass_total_kg,
        production_per_year_kg=production_per_year_kg,
        feed_consumption_cycle_kg=feed_consumption_cycle_kg,
        feed_consumption_year_kg=feed_consumption_year_kg,
        fish_stocked_per_cycle=fish_stocked,
        revenue_cycle=revenue_cycle,
        revenue_year=revenue_year,
        fingerling_cost_cycle=fingerling_cost_cycle,
        fingerling_cost_year=fingerling_cost_year,
        fingerlings_purchase_cycle=fingerlings_purchase_cycle,
    )

    base = {
        "scenario": "Base",
        "input": asdict(inp),

        "total_volume_m3": total_volume_m3,
        "final_biomass_total_kg": final_biomass_total_kg,
        "fish_harvested": fish_harvested,
        "fish_stocked": fish_stocked,
        "fish_stocked_theoretical": fish_stocked_theoretical,
        "fingerlings_purchase_cycle": fingerlings_purchase_cycle,
        "fingerlings_purchase_year": fingerlings_purchase_cycle * inp.cycles_per_year,
        "fingerling_rounding_mode": getattr(inp, "fingerling_rounding_mode", "Arredondar para cima"),
        "fingerling_rounding_base": max(int(getattr(inp, "fingerling_rounding_base", 1000)), 1),
        "biomass_gain_kg": biomass_gain,

        "production_per_cycle_kg": final_biomass_total_kg,
        "production_per_year_kg": production_per_year_kg,

        "feed_consumption_kg": feed_consumption_cycle_kg,
        "feed_consumption_cycle_kg": feed_consumption_cycle_kg,
        "feed_consumption_year_kg": feed_consumption_year_kg,
        "feed_cost_cycle": feed_cost_cycle,
        "feed_cost_year": feed_cost_year,
        "implied_fcr": implied_fcr,
        "economic_model_mode": economic_costs["economic_model_mode"],
        "cost_scaling_mode": economic_costs["cost_scaling_mode"],
        "cost_reference_units": cost_reference_units,
        "cost_scale_factor": cost_scale_factor,
        "electricity_cost_cycle_effective": electricity_cost_cycle_effective,
        "electricity_cost_fixed_cycle_effective": economic_costs["electricity_cost_fixed_cycle_effective"],
        "electricity_cost_variable_cycle_effective": economic_costs["electricity_cost_variable_cycle_effective"],
        "electricity_cost_year": electricity_cost_year,
        "labor_cost_cycle_effective": labor_cost_cycle_effective,
        "labor_cost_fixed_cycle_effective": economic_costs["labor_cost_fixed_cycle_effective"],
        "labor_cost_variable_cycle_effective": economic_costs["labor_cost_variable_cycle_effective"],
        "labor_cost_year": labor_cost_year,
        "other_costs_cycle_effective": other_costs_cycle_effective,
        "other_cost_fixed_cycle_effective": economic_costs["other_cost_fixed_cycle_effective"],
        "other_cost_variable_cycle_effective": economic_costs["other_cost_variable_cycle_effective"],
        "other_costs_year": other_costs_year,
        "capex_total_effective": capex_total_effective,
        "capex_fixed_total_effective": economic_costs["capex_fixed_total_effective"],
        "capex_variable_total_effective": economic_costs["capex_variable_total_effective"],

        "revenue_cycle": revenue_cycle,
        "revenue_year": revenue_year,
        "gross_margin_cycle": gross_margin_cycle,
        "gross_margin_year": gross_margin_year,
        "opex_cycle": opex_cycle,
        "opex_year": opex_year,

        "fingerling_cost_cycle": fingerling_cost_cycle,
        "fingerling_cost_year": fingerling_cost_year,
        "aeration_energy_cost_cycle": aeration_energy_cost_cycle,
        "aeration_energy_cost_year": aeration_energy_cost_year,

        "oxygen_demand_kg_h": oxygen_demand_kg_h,
        "required_aerators": required_aerators,
        "auto_required_aerators": auto_required_aerators,
        "aerator_quantity_mode": inp.aerator_quantity_mode,
        "installed_oxygen_supply_kg_h": required_aerators * aerator_capacity_each,

        "estimated_cycle_days": cycle_days,
        "adjusted_daily_growth_g": adjusted_daily_growth_g(inp),

        "feeding_plan": feeding_plan,
        "growth_curve": growth_curve,
        "cost_curve": cost_curve,
        "production_schedule": production_schedule,

        "cost_per_kg": (
            opex_cycle / final_biomass_total_kg
            if final_biomass_total_kg > 0
            else 0.0
        ),
        "payback_years": (
            capex_total_effective / gross_margin_year
            if gross_margin_year > 0
            else None
        ),
    }

    return {"base": base}