from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DashboardProjectInput:
    project_name: str
    author_name: str
    region_focus: str
    system_type: str
    species: str
    number_of_units: int
    unit_volume_m3: float
    density_kg_m3: float
    survival_rate: float
    cycles_per_year: float
    sale_price_per_kg: float
    fingerling_price: float
    fingerling_weight_kg: float
    electricity_cost_cycle: float
    labor_cost_cycle: float
    other_costs_cycle: float
    capex_total: float
    initial_weight_g: float
    target_weight_g: float
    water_temperature_c: float
    base_daily_growth_g: float
    oxygen_demand_mg_per_kg_h: float
    aerator_hp_each: float
    oxygen_transfer_kg_o2_hp_h: float
    aeration_hours_per_day: float
    electricity_price_kwh: float
    cost_scaling_mode: str = "Fixos (não escalar)"
    cost_reference_units: int = 1
    economic_model_mode: str = "Simplificado"
    electricity_cost_fixed_cycle: float = 0.0
    electricity_cost_per_unit_cycle: float = 0.0
    labor_cost_fixed_cycle: float = 0.0
    labor_cost_per_unit_cycle: float = 0.0
    other_cost_fixed_cycle: float = 0.0
    other_cost_per_unit_cycle: float = 0.0
    capex_fixed_total: float = 0.0
    capex_per_unit: float = 0.0
    fingerling_rounding_mode: str = "Arredondar para cima"
    fingerling_rounding_base: int = 1000

    production_strategy: str = "Ciclos simultâneos"
    production_batch_mode: str = "Automático"
    manual_parallel_batches: int = 6
    harvest_interval_months: float = 1.0

    report_profile: str = "Produtor"
    aerator_quantity_mode: str = "Manual"
    manual_aerators: int = 1
    notes: str = ""

    phase1_min_g: float = 1.0
    phase1_max_g: float = 100.0
    phase1_feeding_rate_percent: float = 5.0
    phase1_meals_per_day: int = 4
    phase1_protein_percent: float = 40.0
    phase1_pellet_mm: float = 1.0
    phase1_feed_price_per_kg: float = 4.2
    phase1_fcr: float = 1.20

    phase2_min_g: float = 100.0
    phase2_max_g: float = 300.0
    phase2_feeding_rate_percent: float = 3.5
    phase2_meals_per_day: int = 4
    phase2_protein_percent: float = 36.0
    phase2_pellet_mm: float = 2.0
    phase2_feed_price_per_kg: float = 4.0
    phase2_fcr: float = 1.35

    phase3_min_g: float = 300.0
    phase3_max_g: float = 700.0
    phase3_feeding_rate_percent: float = 2.5
    phase3_meals_per_day: int = 3
    phase3_protein_percent: float = 32.0
    phase3_pellet_mm: float = 4.0
    phase3_feed_price_per_kg: float = 3.8
    phase3_fcr: float = 1.50

    phase4_min_g: float = 700.0
    phase4_max_g: float = 1000.0
    phase4_feeding_rate_percent: float = 1.8
    phase4_meals_per_day: int = 2
    phase4_protein_percent: float = 28.0
    phase4_pellet_mm: float = 6.0
    phase4_feed_price_per_kg: float = 3.5
    phase4_fcr: float = 1.70
