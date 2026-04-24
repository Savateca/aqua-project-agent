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
    water_depth_m: float = 1.2
    tank_length_m: float = 10.0
    tank_width_m: float = 10.0

    density_kg_m3: float = 30.0
    survival_rate: float = 0.90
    cycles_per_year: float = 2.0

    sale_price_per_kg: float = 10.0
    fingerling_price: float = 0.30
    fingerling_weight_kg: float = 0.001

    electricity_cost_cycle: float = 0.0
    labor_cost_cycle: float = 0.0
    other_costs_cycle: float = 0.0
    capex_total: float = 0.0
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

    initial_weight_g: float = 1.0
    target_weight_g: float = 1000.0
    water_temperature_c: float = 28.0
    base_daily_growth_g: float = 4.5
    oxygen_demand_mg_per_kg_h: float = 550.0
    growth_curve_adjustment_pct: float = 100.0

    production_strategy: str = "Ciclos simultâneos"
    scheduling_basis: str = "Intervalo entre despescas"
    harvest_interval_months: float = 1.0
    manual_parallel_batches: int = 9
    desired_units_per_batch: int = 1

    report_profile: str = "Produtor"
    notes: str = ""

    site_altitude_m: float = 0.0
    target_do_mg_l: float = 5.0
    field_efficiency_pct: float = 85.0
    aeration_safety_factor_pct: float = 20.0
    aeration_hours_per_day: float = 24.0
    electricity_price_kwh: float = 0.45

    aeration_mode: str = "Automático"
    automatic_aeration_technology: str = "Chafariz"
    blower_type: str = "Automático"
    diffusion_efficiency_pct: float = 12.0
    aeration_power_mode: str = "Potência modulada por fase"
    aeration_control_strategy: str = "Automático"
    blower_min_operational_pct: float = 35.0
    fountain_min_operational_pct: float = 50.0
    paddle_min_operational_pct: float = 50.0

    manual_use_fountain: bool = False
    manual_fountain_model: str = "B-501/B-503"
    manual_fountain_qty: int = 0

    manual_use_paddlewheel: bool = False
    manual_paddle_model: str = "B-209"
    manual_paddle_qty: int = 0

    manual_use_radial: bool = False
    manual_radial_model: str = "CRA-750 TS"
    manual_radial_qty: int = 0

    manual_use_lobular: bool = False
    manual_lobular_model: str = "Família SRT"
    manual_lobular_qty: int = 0

    phase1_min_g: float = 1.0
    phase1_max_g: float = 20.0
    phase1_feeding_rate_percent: float = 8.0
    phase1_meals_per_day: int = 4
    phase1_protein_percent: float = 45.0
    phase1_pellet_mm: float = 1.5
    phase1_feed_price_per_kg: float = 4.2
    phase1_fcr: float = 1.10

    phase2_min_g: float = 20.0
    phase2_max_g: float = 250.0
    phase2_feeding_rate_percent: float = 5.0
    phase2_meals_per_day: int = 4
    phase2_protein_percent: float = 40.0
    phase2_pellet_mm: float = 3.0
    phase2_feed_price_per_kg: float = 4.0
    phase2_fcr: float = 1.30

    phase3_min_g: float = 250.0
    phase3_max_g: float = 650.0
    phase3_feeding_rate_percent: float = 3.0
    phase3_meals_per_day: int = 3
    phase3_protein_percent: float = 36.0
    phase3_pellet_mm: float = 4.0
    phase3_feed_price_per_kg: float = 3.8
    phase3_fcr: float = 1.50

    phase4_min_g: float = 650.0
    phase4_max_g: float = 1000.0
    phase4_feeding_rate_percent: float = 2.2
    phase4_meals_per_day: int = 2
    phase4_protein_percent: float = 32.0
    phase4_pellet_mm: float = 6.0
    phase4_feed_price_per_kg: float = 3.5
    phase4_fcr: float = 1.60

    phase5_min_g: float = 1000.0
    phase5_max_g: float = 2000.0
    phase5_feeding_rate_percent: float = 1.5
    phase5_meals_per_day: int = 2
    phase5_protein_percent: float = 28.0
    phase5_pellet_mm: float = 8.0
    phase5_feed_price_per_kg: float = 3.4
    phase5_fcr: float = 1.70
