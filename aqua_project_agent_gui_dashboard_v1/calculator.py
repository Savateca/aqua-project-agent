from __future__ import annotations

import math
from dataclasses import asdict

from .models import DashboardProjectInput


def altitude_transfer_factor(altitude_m: float) -> float:
    """
    Fator de correção por altitude para transferência de oxigênio.

    Usa a razão aproximada de pressão atmosférica da atmosfera padrão:
        P/P0 = (1 - 2,25577e-5 * altitude_m) ** 5,25588

    Interpretação operacional: quanto menor a pressão atmosférica, menor a
    capacidade efetiva de incorporação de O₂ do mesmo equipamento.

    Valores aproximados:
        0 m     -> 1,00
        1.000 m -> 0,89
        2.000 m -> 0,78
        3.000 m -> 0,69
        5.000 m -> 0,53
        10.000 m -> 0,26
    """
    try:
        alt = max(0.0, float(altitude_m))
    except (TypeError, ValueError):
        alt = 0.0

    # Limite operacional para evitar valores matemáticos negativos fora da faixa usual.
    alt = min(alt, 10000.0)
    factor = (1.0 - 2.25577e-5 * alt) ** 5.25588
    return max(0.10, min(1.0, round(factor, 3)))


def surface_aeration_base_factor(temp_c: float) -> float:
    if 25 <= temp_c <= 30:
        return 0.50
    if 23 <= temp_c < 25 or 30 < temp_c <= 32:
        return 0.46
    if 20 <= temp_c < 23 or 32 < temp_c <= 34:
        return 0.42
    return 0.38

DEFAULT_FEEDING_CURVE = [
    {
        "phase_name": "Fase 1",
        "min_g": 1.0,
        "max_g": 20.0,
        "feeding_rate_percent": 8.0,
        "meals_per_day": 4,
        "protein_percent": 45.0,
        "pellet_mm": 1.0,
        "feed_price_per_kg": 4.2,
        "phase_fcr": 1.15,
    },
    {
        "phase_name": "Fase 2",
        "min_g": 20.0,
        "max_g": 250.0,
        "feeding_rate_percent": 5.0,
        "meals_per_day": 4,
        "protein_percent": 40.0,
        "pellet_mm": 3.0,
        "feed_price_per_kg": 4.0,
        "phase_fcr": 1.30,
    },
    {
        "phase_name": "Fase 3",
        "min_g": 250.0,
        "max_g": 650.0,
        "feeding_rate_percent": 3.0,
        "meals_per_day": 3,
        "protein_percent": 36.0,
        "pellet_mm": 4.0,
        "feed_price_per_kg": 3.8,
        "phase_fcr": 1.50,
    },
    {
        "phase_name": "Fase 4",
        "min_g": 650.0,
        "max_g": 1000.0,
        "feeding_rate_percent": 2.2,
        "meals_per_day": 2,
        "protein_percent": 32.0,
        "pellet_mm": 6.0,
        "feed_price_per_kg": 3.5,
        "phase_fcr": 1.60,
    },
    {
        "phase_name": "Fase 5",
        "min_g": 1000.0,
        "max_g": 2000.0,
        "feeding_rate_percent": 1.5,
        "meals_per_day": 2,
        "protein_percent": 28.0,
        "pellet_mm": 8.0,
        "feed_price_per_kg": 3.4,
        "phase_fcr": 1.70,
    },
]

FOUNTAIN_LIBRARY = [
    {"model": "B-401/B-403", "power_cv": 0.75, "consumption_kwh": 0.63, "sort_kg_h": 1.11, "sae": 1.76, "launch_diameter_m": 3.20},
    {"model": "B-501/B-503", "power_cv": 1.00, "consumption_kwh": 0.80, "sort_kg_h": 1.87, "sae": 2.33, "launch_diameter_m": 3.70},
    {"model": "B-601/B-603", "power_cv": 1.50, "consumption_kwh": 1.11, "sort_kg_h": 3.15, "sae": 2.83, "launch_diameter_m": 5.50},
    {"model": "B-701/B-703", "power_cv": 3.00, "consumption_kwh": 2.81, "sort_kg_h": 6.17, "sae": 2.19, "launch_diameter_m": 6.20},
]

PADDLEWHEEL_LIBRARY = [
    {"model": "B-105", "power_cv": 1.00, "consumption_kwh": 0.77, "sort_kg_h": 1.35, "sae": 1.75},
    {"model": "B-209", "power_cv": 2.00, "consumption_kwh": 1.46, "sort_kg_h": 3.60, "sae": 2.46},
    {"model": "B-309", "power_cv": 3.00, "consumption_kwh": 2.29, "sort_kg_h": 5.20, "sae": 2.27},
]

RADIAL_BLOWER_LIBRARY = [
    {"model": "CRA-370 TS", "power_kw": 1.50, "airflow_m3_h": 150.0, "pressure_mbar": 290.0, "source": "biblioteca preliminar"},
    {"model": "CRA-550 TS", "power_kw": 1.75, "airflow_m3_h": 240.0, "pressure_mbar": 290.0, "source": "biblioteca preliminar"},
    {"model": "CRA-750 TS", "power_kw": 2.00, "airflow_m3_h": 340.0, "pressure_mbar": 320.0, "source": "biblioteca preliminar"},
    {"model": "CRB-700 TS HE", "power_kw": 4.40, "airflow_m3_h": 360.0, "pressure_mbar": 330.0, "source": "Asten"},
]

LOBULAR_BLOWER_LIBRARY = [
    {"model": "Família SRT", "power_kw": 3.00, "airflow_m3_h": 1200.0, "pressure_mbar": 350.0},
]

DIFFUSER_LIBRARY = [
    {
        "name": "Mangueira porosa nano tube BERAQUA",
        "category": "mangueira_porosa_microbolhas",
        "airflow_m3_h_m": 0.20,
        "transfer_efficiency_pct_default": 12.0,
        "otr_kg_o2_h_m_conservative": 0.015,
        "otr_kg_o2_h_m_standard": 0.025,
        "otr_kg_o2_h_m_optimistic": 0.040,
        "otr_kg_o2_h_m_high_efficiency": 0.060,
        "spacing_m": 0.8,
        "note": "Material do fornecedor informa microbolhas e baixa resistência, mas sem SOTR/SAE certificado; usar como estimativa preliminar editável. Para projeto preliminar, utilizar 0,025 kg O₂/h/m como referência padrão em 1,20 m de profundidade.",
    },
    {
        "name": "Mangueira porosa genérica para ar",
        "category": "mangueira_porosa_ar",
        "airflow_m3_h_m": 0.15,
        "transfer_efficiency_pct_default": 8.0,
        "otr_kg_o2_h_m_conservative": 0.012,
        "otr_kg_o2_h_m_standard": 0.018,
        "otr_kg_o2_h_m_optimistic": 0.030,
        "otr_kg_o2_h_m_high_efficiency": 0.040,
        "spacing_m": 0.8,
        "note": "Referência preliminar para mangueiras porosas sem SOTR/SAE certificado. Ajustar com ficha técnica e teste de campo.",
    },
    {
        "name": "Difusor fino/microbolhas",
        "category": "microbolhas_ar",
        "airflow_m3_h_m": 0.25,
        "transfer_efficiency_pct_default": 15.0,
        "otr_kg_o2_h_m_conservative": 0.020,
        "otr_kg_o2_h_m_standard": 0.035,
        "otr_kg_o2_h_m_optimistic": 0.050,
        "otr_kg_o2_h_m_high_efficiency": 0.070,
        "spacing_m": 0.7,
        "note": "Referência preliminar para difusão de bolhas finas; exige controle de colmatação, filtragem de ar e manutenção.",
    },
    {
        "name": "Mangueira técnica de oxigenação tipo SOLVOX",
        "category": "oxigenio_puro",
        "airflow_m3_h_m": 0.10,
        "transfer_efficiency_pct_default": 80.0,
        "otr_kg_o2_h_m_conservative": 0.050,
        "otr_kg_o2_h_m_standard": 0.080,
        "otr_kg_o2_h_m_optimistic": 0.120,
        "otr_kg_o2_h_m_high_efficiency": 0.180,
        "spacing_m": 0.8,
        "note": "Uso com oxigênio, não ar. Dimensionar por vazão de O₂, pressão, profundidade e curva do fabricante.",
    },
]

GROWTH_SUBRANGES_V2 = [
    {"label": "1-5 g", "min_g": 1.0, "max_g": 5.0, "daily_gain_28_g": 0.15, "evidence": "provisório consolidado"},
    {"label": "5-20 g", "min_g": 5.0, "max_g": 20.0, "daily_gain_28_g": 0.75, "evidence": "âncora bibliográfica"},
    {"label": "20-100 g", "min_g": 20.0, "max_g": 100.0, "daily_gain_28_g": 1.80, "evidence": "síntese técnica"},
    {"label": "100-250 g", "min_g": 100.0, "max_g": 250.0, "daily_gain_28_g": 3.80, "evidence": "síntese técnica"},
    {"label": "250-650 g", "min_g": 250.0, "max_g": 650.0, "daily_gain_28_g": 6.00, "evidence": "âncora Embrapa"},
    {"label": "650-1000 g", "min_g": 650.0, "max_g": 1000.0, "daily_gain_28_g": 5.50, "evidence": "faixa controlada"},
    {"label": "1000-2000 g", "min_g": 1000.0, "max_g": 2000.0, "daily_gain_28_g": 3.50, "evidence": "faixa controlada"},
]



def circular_diameter_from_volume(volume_m3: float, depth_m: float) -> float:
    if depth_m <= 0:
        return 0.0
    return math.sqrt((4.0 * volume_m3) / (math.pi * depth_m))


def compute_geometry(inp: DashboardProjectInput) -> dict:
    structure = getattr(inp, "system_type", "Circular revestido")
    depth = max(float(getattr(inp, "water_depth_m", 1.2)), 0.2)

    if structure == "Circular revestido":
        volume = max(float(inp.unit_volume_m3), 0.1)
        diameter = circular_diameter_from_volume(volume, depth)
        area = math.pi * (diameter ** 2) / 4.0
        length = diameter
        width = diameter
    else:
        length = max(float(getattr(inp, "tank_length_m", 10.0)), 0.1)
        width = max(float(getattr(inp, "tank_width_m", 10.0)), 0.1)
        area = length * width
        volume = area * depth
        diameter = 0.0

    return {
        "depth_m": depth,
        "unit_volume_m3": volume,
        "surface_area_m2": area,
        "diameter_m": diameter,
        "length_m": length,
        "width_m": width,
        "shape": "circular" if structure == "Circular revestido" else "rectangular",
    }


def recommended_depth_for_structure(system_type: str) -> float:
    return 1.5 if system_type == "Escavado revestido" else 1.2


def structure_warning(system_type: str, depth_m: float) -> str:
    suggested = recommended_depth_for_structure(system_type)
    if depth_m > suggested * 1.25:
        return f"Altura de água acima da sugestão usual para {system_type.lower()} ({suggested:.1f} m)."
    if depth_m < suggested * 0.70:
        return f"Altura de água abaixo da sugestão usual para {system_type.lower()} ({suggested:.1f} m)."
    return ""


def _clear_span_for_surface_aeration(geometry: dict) -> float:
    diameter = float(geometry.get("diameter_m", 0.0) or 0.0)
    if diameter > 0:
        return diameter
    length = float(geometry.get("length_m", 0.0) or 0.0)
    width = float(geometry.get("width_m", 0.0) or 0.0)
    positive = [v for v in (length, width) if v > 0]
    return min(positive) if positive else 0.0


def _surface_geometry_check(technology: str, equipment: dict, geometry: dict) -> tuple[bool, str]:
    if technology != "Chafariz":
        return True, ""
    launch = float(equipment.get("launch_diameter_m", 0.0) or 0.0)
    span = _clear_span_for_surface_aeration(geometry)
    if launch <= 0 or span <= 0:
        return True, ""
    required_span = launch * 1.20
    if span < required_span:
        return False, (
            f"Modelo {equipment.get('model','-')} não recomendado: o lance/diâmetro de lançamento (~{launch:.2f} m) "
            f"pode ser excessivo para a menor dimensão útil do tanque ({span:.2f} m)."
        )
    return True, ""


def _surface_effective_sort(equipment: dict, temp_factor: float, altitude_factor: float, field_factor: float) -> float:
    return equipment["sort_kg_h"] * temp_factor * altitude_factor * field_factor


def _fountain_arrangement_for_quantity(qty: int) -> tuple[str, str]:
    if qty <= 1:
        return "A1", "1 central"
    if qty == 2:
        return "A2", "2 opostos a 180°"
    if qty == 3:
        return "A3", "3 em triângulo a 120°"
    return "A4", "4 em quadrantes a 90°"


def _fountain_max_units_for_model(geometry: dict, equipment: dict, margin_m: float = 0.50) -> tuple[int, dict]:
    """
    Máximo geométrico de chafarizes em tanque circular, com base nos critérios
    da tabela A1-A4: folga mínima de borda e não sobreposição da mancha/lance.
    """
    diameter = float(geometry.get("diameter_m", 0.0) or 0.0)
    launch = float(equipment.get("launch_diameter_m", 0.0) or 0.0)

    if diameter <= 0.0:
        span = _clear_span_for_surface_aeration(geometry)
        if span <= 0.0 or launch <= 0.0:
            return 1, {"arrangement": "A1", "arrangement_label": "1 central", "install_radius_m": 0.0, "edge_clearance_m": 0.0}
        ok = span >= launch * 1.20
        return (1 if ok else 0), {"arrangement": "A1", "arrangement_label": "1 central", "install_radius_m": 0.0, "edge_clearance_m": round(max(0.0, span / 2.0 - launch / 2.0), 2)}

    tank_radius = diameter / 2.0
    if launch <= 0.0:
        return 1, {"arrangement": "A1", "arrangement_label": "1 central", "install_radius_m": 0.0, "edge_clearance_m": round(tank_radius, 2)}

    spot_radius = launch / 2.0
    max_install_radius = tank_radius - spot_radius - margin_m

    def _fits(qty: int) -> tuple[bool, float]:
        if qty <= 1:
            return tank_radius >= spot_radius + margin_m, 0.0
        if qty == 2:
            min_radius = spot_radius
        elif qty == 3:
            min_radius = launch / math.sqrt(3.0)
        else:
            min_radius = launch / math.sqrt(2.0)
        return max_install_radius >= min_radius, max_install_radius

    best_qty = 0
    best_radius = 0.0
    for qty in (1, 2, 3, 4):
        fits, install_radius = _fits(qty)
        if fits:
            best_qty = qty
            best_radius = install_radius

    arrangement, label = _fountain_arrangement_for_quantity(best_qty)
    edge_clearance = tank_radius - best_radius - spot_radius if best_qty > 1 else tank_radius - spot_radius
    return best_qty, {
        "arrangement": arrangement,
        "arrangement_label": label,
        "install_radius_m": round(best_radius, 2),
        "edge_clearance_m": round(edge_clearance, 2),
        "launch_diameter_m": round(launch, 2),
        "tank_diameter_m": round(diameter, 2),
        "margin_m": margin_m,
    }


def _surface_max_units_per_tank(system_type: str, technology: str, equipment: dict | None = None, geometry: dict | None = None) -> int:
    """Compatibilidade antiga: retorna só o número máximo."""
    max_units, _info = _surface_max_units_per_tank_info(system_type, technology, equipment, geometry)
    return max_units


def _surface_max_units_per_tank_info(system_type: str, technology: str, equipment: dict | None = None, geometry: dict | None = None) -> tuple[int, dict]:
    """Limite geométrico-operacional por tanque com dados do arranjo."""
    geometry = geometry or {}
    equipment = equipment or {}
    span = _clear_span_for_surface_aeration(geometry)
    shape = str(geometry.get("shape", "")).lower()

    if technology == "Chafariz":
        if system_type == "Circular revestido" or shape == "circular":
            return _fountain_max_units_for_model(geometry, equipment)
        launch = float(equipment.get("launch_diameter_m", 0.0) or 0.0)
        if span <= 0.0 or launch <= 0.0:
            return 1, {"arrangement": "A1", "arrangement_label": "1 central"}
        return (1 if span >= launch * 1.20 else 0), {"arrangement": "A1", "arrangement_label": "1 central"}

    if technology == "Pás":
        diameter = float(geometry.get("diameter_m", 0.0) or 0.0)
        area = float(geometry.get("surface_area_m2", 0.0) or 0.0)
        if system_type == "Circular revestido" or shape == "circular":
            # Pás não são limitadas por lançamento de água como o chafariz.
            # Em tanques circulares grandes, o limite físico pode ser maior que 4.
            # O sistema separa limite geométrico de alerta econômico/energético.
            if diameter >= 26.0:
                return 12, {"arrangement": "cruz/X", "arrangement_label": "até 12 pás em arranjos cruzados ou em X; avaliar custo energético"}
            if diameter >= 20.0:
                return 8, {"arrangement": "cruz/X", "arrangement_label": "até 8 pás em tanque circular grande; avaliar custo energético"}
            if diameter >= 14.0:
                return 4, {"arrangement": "auxiliar", "arrangement_label": "até 4 pás auxiliares em tanque circular médio/grande"}
            if diameter >= 10.0:
                return 2, {"arrangement": "auxiliar", "arrangement_label": "até 2 pás auxiliares com cautela operacional"}
            return 0, {"arrangement": "não recomendado", "arrangement_label": "diâmetro insuficiente para pás"}
        if area < 120.0:
            return 1, {"arrangement": "linear", "arrangement_label": "1 pá por unidade"}
        return max(1, min(int(area // 180.0) + 1, 12)), {"arrangement": "linear", "arrangement_label": "pás distribuídas no comprimento; avaliar custo energético"}

    return 1, {}


def _surface_technology_allowed(system_type: str, technology: str, geometry: dict | None = None) -> bool:
    geometry = geometry or {}
    span = _clear_span_for_surface_aeration(geometry)
    if technology == "Chafariz":
        return system_type in ("Circular revestido", "Suspenso revestido retangular", "Escavado revestido")
    if technology == "Pás":
        if system_type == "Circular revestido":
            return span >= 10.0
        return system_type in ("Circular revestido", "Suspenso revestido retangular", "Escavado revestido")
    return True


def suggest_surface_aerator(
    technology: str,
    system_type: str,
    oxygen_demand_per_tank_kg_h: float,
    temp_factor: float,
    altitude_factor: float,
    field_factor: float,
    geometry: dict | None = None,
) -> dict:
    """Dimensiona aeradores superficiais com leitura geométrica e operacional."""
    library = FOUNTAIN_LIBRARY if technology == "Chafariz" else PADDLEWHEEL_LIBRARY
    geometry = geometry or {}
    allowed = _surface_technology_allowed(system_type, technology, geometry)

    best = None
    for equipment in library:
        sea_level_effective_sort = _surface_effective_sort(equipment, temp_factor, 1.0, field_factor)
        effective_sort = _surface_effective_sort(equipment, temp_factor, altitude_factor, field_factor)
        max_units, arrangement_info = _surface_max_units_per_tank_info(system_type, technology, equipment, geometry)
        qty_required = math.ceil(oxygen_demand_per_tank_kg_h / effective_sort) if effective_sort > 0 else max_units + 1
        qty_required = max(qty_required, 0)
        qty_installed = min(qty_required, max_units) if allowed else 0

        geom_allowed, geom_warning = _surface_geometry_check(technology, equipment, geometry)
        if technology == "Chafariz":
            geom_allowed = max_units > 0
            if not geom_allowed:
                geom_warning = "Nenhum arranjo A1-A4 atende à folga geométrica mínima para este modelo no tanque informado."
        feasible = allowed and geom_allowed and qty_required <= max_units and qty_installed > 0
        installed_supply = effective_sort * max(qty_installed, 0)
        sea_level_supply = sea_level_effective_sort * max(qty_installed, 0)
        peak_use_pct = (oxygen_demand_per_tank_kg_h / installed_supply * 100.0) if installed_supply > 0 else 999.0
        excess_ratio = (installed_supply / oxygen_demand_per_tank_kg_h) if oxygen_demand_per_tank_kg_h > 0 else 0.0

        if not allowed:
            if technology == "Pás" and system_type == "Circular revestido":
                warning = "Aerador de pás não recomendado para tanque circular pequeno; em tanques circulares grandes pode ser usado como tecnologia auxiliar de circulação/vórtice."
            else:
                warning = f"Tecnologia {technology} não recomendada para {system_type}."
        elif not geom_allowed:
            warning = geom_warning
        elif max_units <= 0:
            warning = f"Geometria insuficiente para instalar {technology.lower()} com segurança neste tanque."
        elif qty_required > max_units:
            warning = (
                f"A condição simulada exige cerca de {qty_required} equipamento(s) por tanque, "
                f"mas o limite geométrico-operacional estimado para {technology.lower()} é {max_units}. "
                "Recomenda-se equipamento mais robusto, tecnologia combinada, soprador/difusão ou revisão da biomassa/densidade."
            )
        elif technology == "Pás" and system_type == "Circular revestido":
            warning = (
                "Aerador de pás permitido para tanque circular grande como tecnologia de circulação/vórtice. "
                "O limite exibido é geométrico-operacional; acima de 4 unidades, avaliar custo de aquisição, energia e eficiência marginal. "
                "Validar posicionamento para favorecer concentração de sólidos no dreno central sem ressuspensão excessiva."
            )
        else:
            warning = ""

        score = (
            0 if feasible else 1,
            max(0.0, oxygen_demand_per_tank_kg_h - installed_supply),
            abs(peak_use_pct - 85.0),
            equipment.get("consumption_kwh", 0.0) * max(qty_installed, 0),
            equipment.get("power_cv", 0.0),
        )
        candidate = {
            "technology": technology,
            "allowed": allowed,
            "feasible": feasible,
            "max_units_per_tank": max_units,
            "arrangement": arrangement_info.get("arrangement", "-") if isinstance(arrangement_info, dict) else "-",
            "arrangement_label": arrangement_info.get("arrangement_label", "-") if isinstance(arrangement_info, dict) else "-",
            "install_radius_m": arrangement_info.get("install_radius_m", 0.0) if isinstance(arrangement_info, dict) else 0.0,
            "edge_clearance_m": arrangement_info.get("edge_clearance_m", 0.0) if isinstance(arrangement_info, dict) else 0.0,
            "launch_diameter_m": arrangement_info.get("launch_diameter_m", equipment.get("launch_diameter_m", 0.0)) if isinstance(arrangement_info, dict) else equipment.get("launch_diameter_m", 0.0),
            "tank_diameter_m": arrangement_info.get("tank_diameter_m", geometry.get("diameter_m", 0.0)) if isinstance(arrangement_info, dict) else geometry.get("diameter_m", 0.0),
            "qty_required_per_tank": qty_required,
            "model": equipment["model"],
            "power_cv": equipment["power_cv"],
            "consumption_kwh_each": equipment["consumption_kwh"],
            "sort_nominal_kg_h": equipment["sort_kg_h"],
            "sea_level_effective_sort_kg_h": sea_level_effective_sort,
            "effective_sort_kg_h": effective_sort,
            "altitude_factor": altitude_factor,
            "qty_per_tank": max(qty_installed, 0),
            "installed_supply_per_tank_kg_h": installed_supply,
            "sea_level_supply_per_tank_kg_h": sea_level_supply,
            "peak_use_pct": round(peak_use_pct, 1),
            "excess_ratio": round(excess_ratio, 3),
            "warning": warning,
            "geometry_span_m": _clear_span_for_surface_aeration(geometry),
            "_score": score,
        }
        if best is None or score < best["_score"]:
            best = candidate

    if best is None:
        return {
            "technology": technology,
            "allowed": False,
            "feasible": False,
            "max_units_per_tank": 0,
            "model": "-",
            "qty_per_tank": 0,
            "effective_sort_kg_h": 0.0,
            "installed_supply_per_tank_kg_h": 0.0,
            "warning": "Sem modelo disponível.",
        }
    best.pop("_score", None)
    return best


def _diffuser_otr_reference(diffusion_eff_pct: float, diffuser: dict) -> tuple[float, str]:
    """Converte a seleção simples de eficiência em OTR preliminar por metro.

    Base operacional:
    - conservador: 0,015 kg O₂/h/m
    - padrão: 0,025 kg O₂/h/m
    - otimista: 0,040 kg O₂/h/m
    - alta eficiência: 0,050 a 0,080 kg O₂/h/m
    """
    try:
        eff = float(diffusion_eff_pct)
    except (TypeError, ValueError):
        eff = float(diffuser.get("transfer_efficiency_pct_default", 12.0) or 12.0)
    if eff <= 8.0:
        return float(diffuser.get("otr_kg_o2_h_m_conservative", 0.015)), "conservador"
    if eff <= 14.0:
        return float(diffuser.get("otr_kg_o2_h_m_standard", 0.025)), "padrão/intermediário"
    if eff <= 22.0:
        return float(diffuser.get("otr_kg_o2_h_m_optimistic", 0.040)), "otimista"
    return float(diffuser.get("otr_kg_o2_h_m_high_efficiency", 0.060)), "alta eficiência"


def _operational_diffuser_meter_limits(unit_volume_m3: float, density_kg_m3: float) -> tuple[float, float, str]:
    """Faixa operacional preliminar de mangueira por tanque."""
    volume = max(float(unit_volume_m3 or 0.0), 0.1)
    density = max(float(density_kg_m3 or 0.0), 0.0)
    if density <= 25.0:
        rec = volume * 0.45
        max_reasonable = volume * 0.80
        note = "densidade até 25 kg/m³: mangueira porosa pode atuar como fonte principal com soprador adequado e reserva."
    elif density <= 50.0:
        rec = volume * 0.65
        max_reasonable = volume * 0.95
        note = "densidade de 25 a 50 kg/m³: usar como fonte principal apenas com cautela; tecnologia combinada é recomendável."
    elif density <= 75.0:
        rec = volume * 0.90
        max_reasonable = volume * 1.20
        note = "densidade acima de 50 kg/m³: não confiar em mangueira porosa com ar como única fonte de segurança."
    else:
        rec = volume * 1.10
        max_reasonable = volume * 1.50
        note = "densidade muito alta: mangueira porosa deve ser suporte/backup/distribuição; avaliar oxigênio puro ou tecnologia combinada."
    return rec, max_reasonable, note


def _estimate_diffuser_layout(
    oxygen_demand_per_tank_kg_h: float,
    number_of_units: int,
    geometry: dict,
    diffusion_eff_pct: float,
    altitude_factor: float,
    field_factor: float,
    blower_airflow_m3_h_each: float,
    blower_qty: int,
    density_kg_m3: float = 0.0,
) -> dict:
    """Estimativa preliminar de metros de mangueira/difusor por tanque."""
    diffuser = DIFFUSER_LIBRARY[0]
    otr_base, otr_class = _diffuser_otr_reference(diffusion_eff_pct, diffuser)
    kg_o2_per_m_h = max(0.001, otr_base * altitude_factor)
    meters_required = oxygen_demand_per_tank_kg_h / kg_o2_per_m_h if kg_o2_per_m_h > 0 else 0.0

    unit_volume = float(geometry.get("unit_volume_m3", 0.0) or 0.0)
    recommended_m, max_reasonable_m, density_note = _operational_diffuser_meter_limits(unit_volume, density_kg_m3)
    meters_recommended = min(meters_required, max_reasonable_m)
    is_excessive = meters_required > max_reasonable_m

    air_per_m = float(diffuser.get("airflow_m3_h_m", 0.20) or 0.20)
    available_air_per_tank = (blower_airflow_m3_h_each * max(blower_qty, 0)) / max(number_of_units, 1)
    max_meters_by_air = available_air_per_tank / air_per_m if air_per_m > 0 else 0.0
    diameter = float(geometry.get("diameter_m", 0.0) or 0.0)
    circumference = math.pi * diameter if diameter > 0 else 0.0
    rings = math.ceil(meters_recommended / circumference) if circumference > 0 else 0

    if is_excessive:
        layout_note = (
            "A metragem calculada para suprir toda a demanda de O₂ ultrapassa a faixa operacional/econômica razoável. "
            "Recomenda-se tecnologia combinada, soprador/difusor de maior eficiência, redução de densidade ou oxigênio suplementar."
        )
    else:
        layout_note = "Distribuir em anéis ou segmentos próximos ao fundo, mantendo acesso para limpeza e evitando interferência com dreno central."

    return {
        "diffuser_name": diffuser["name"],
        "diffuser_note": diffuser["note"],
        "airflow_m3_h_per_m": air_per_m,
        "effective_transfer_efficiency_pct": diffusion_eff_pct,
        "otr_reference_class": otr_class,
        "kg_o2_per_m_h": kg_o2_per_m_h,
        "meters_per_tank_required": meters_required,
        "meters_per_tank_recommended": meters_recommended,
        "meters_total_required": meters_required * max(number_of_units, 1),
        "meters_total_recommended": meters_recommended * max(number_of_units, 1),
        "operational_recommended_m_per_tank": recommended_m,
        "operational_max_reasonable_m_per_tank": max_reasonable_m,
        "is_metrage_excessive": is_excessive,
        "density_note": density_note,
        "available_air_m3_h_per_tank": available_air_per_tank,
        "max_meters_by_available_air_per_tank": max_meters_by_air,
        "estimated_rings_per_tank": rings,
        "layout_note": layout_note,
    }

def _blower_capacity_kg_h(blower: dict, diffusion_eff_pct: float, altitude_factor: float, field_factor: float) -> float:
    # 1 m3 de ar contém aproximadamente 0,275 kg de O2; aplicamos eficiência efetiva de transferência.
    oxygen_in_air_kg_m3 = 0.275
    return blower["airflow_m3_h"] * oxygen_in_air_kg_m3 * (diffusion_eff_pct / 100.0) * altitude_factor * field_factor


def _default_control_strategy(technology: str) -> str:
    if "Soprador Lobular" in technology:
        return "Inversor de frequência"
    if "Soprador" in technology:
        return "Inversor de frequência"
    if technology == "Chafariz":
        return "Acionamento por etapas"
    if technology == "Pás":
        return "Acionamento por etapas"
    return "Acionamento por etapas"


def _recommended_control_equipment(technology: str, strategy: str) -> str:
    if strategy == "Potência fixa no ciclo inteiro":
        return "Sem equipamento adicional obrigatório"
    if "Soprador Lobular" in technology:
        return "Inversor de frequência"
    if "Soprador Radial" in technology or technology == "Soprador":
        return "Inversor de frequência (verificar compatibilidade) ou painel por etapas"
    if technology == "Chafariz":
        return "Painel de acionamento por etapas; inversor opcional se compatível"
    if technology == "Pás":
        return "Painel de acionamento por etapas; inversor com uso limitado"
    return "Painel de acionamento por etapas"


def _recommended_control_note(technology: str, strategy: str) -> str:
    if strategy == "Potência fixa no ciclo inteiro":
        return "Operação simples e conservadora, com maior custo energético ao longo do ciclo."
    if "Soprador Lobular" in technology:
        return "Tecnologia adequada para modulação progressiva de vazão de ar conforme a biomassa aumenta."
    if "Soprador Radial" in technology or technology == "Soprador":
        return "A modulação é possível, mas deve respeitar a faixa eficiente de operação do soprador."
    if technology == "Chafariz":
        return "A redução excessiva da rotação pode prejudicar lançamento d'água, circulação e incorporação de oxigênio."
    if technology == "Pás":
        return "A rotação muito baixa pode reduzir a eficiência hidráulica e a circulação do tanque."
    return "Ajuste a potência conforme a biomassa cresce, preservando a segurança operacional."


def _minimum_operational_pct(inp: DashboardProjectInput, technology: str) -> float:
    if "Soprador" in technology:
        return max(0.0, min(100.0, float(getattr(inp, "blower_min_operational_pct", 35.0)))) / 100.0
    if technology == "Chafariz":
        return max(0.0, min(100.0, float(getattr(inp, "fountain_min_operational_pct", 50.0)))) / 100.0
    if technology == "Pás":
        return max(0.0, min(100.0, float(getattr(inp, "paddle_min_operational_pct", 50.0)))) / 100.0
    return 0.35


def _phase_aeration_modulation(inp: DashboardProjectInput, feeding_plan: list[dict], fish_stocked: float, selected_aeration: dict) -> tuple[list[dict], dict]:
    installed_supply = float(selected_aeration.get("installed_oxygen_supply_kg_h", 0.0) or 0.0)
    installed_power_kw = float(selected_aeration.get("power_installed_kw", 0.0) or 0.0)
    strategy_mode = getattr(inp, "aeration_power_mode", "Potência modulada por fase")
    technology = str(selected_aeration.get("technology", "-"))
    control_strategy = getattr(inp, "aeration_control_strategy", "Automático")
    if control_strategy == "Automático":
        control_strategy = _default_control_strategy(technology)
    min_pct = _minimum_operational_pct(inp, technology)
    oxygen_base = float(getattr(inp, "oxygen_demand_mg_per_kg_h", 550.0)) / 1_000_000.0
    safety_factor = 1.0 + float(getattr(inp, "aeration_safety_factor_pct", 20.0)) / 100.0
    hours_day = float(getattr(inp, "aeration_hours_per_day", 24.0))
    energy_price = float(getattr(inp, "electricity_price_kwh", 0.45))
    details = selected_aeration.get("details", {})
    per_unit_supply = 0.0
    total_units = max(1, int(selected_aeration.get("quantity_total", 0) or 0))
    per_tank_units = max(1, int(selected_aeration.get("quantity_per_tank", 1) or 1))
    if technology in ("Chafariz", "Pás") and isinstance(details, dict):
        per_unit_supply = float(details.get("effective_sort_kg_h", 0.0) or 0.0)
    elif "Soprador" in technology and isinstance(details, dict):
        per_unit_supply = float(details.get("effective_oxygen_capacity_each_kg_h", 0.0) or 0.0)
    rows = []
    modulated_cost = 0.0
    fixed_cost = installed_power_kw * hours_day * sum(float(r.get("days_in_phase", 0.0) or 0.0) for r in feeding_plan) * energy_price
    active_power_sum_weighted = 0.0
    total_days = 0.0
    per_tank_power_kw = installed_power_kw / total_units if total_units > 0 else 0.0

    for row in feeding_plan:
        biomass_start = float(row.get("biomass_start_phase_kg", 0.0) or 0.0)
        biomass_end = float(row.get("biomass_end_phase_kg", 0.0) or 0.0)
        biomass_mean = (biomass_start + biomass_end) / 2.0
        days_phase = float(row.get("days_in_phase", 0.0) or 0.0)
        demand_phase = biomass_mean * oxygen_base * safety_factor
        raw_use = (demand_phase / installed_supply) if installed_supply > 0 else 0.0
        limited = False

        if strategy_mode == "Potência fixa no ciclo inteiro":
            use_pct = 1.0
            active_units = total_units
            active_power_kw = installed_power_kw
        else:
            if technology in ("Chafariz", "Pás"):
                # Em tecnologias individuais por tanque, todos os equipamentos permanecem ativos;
                # o que varia é a potência média aplicada a cada motor.
                active_units = total_units
                use_pct = max(min_pct, raw_use)
                if use_pct > 1.0:
                    use_pct = 1.0
                    limited = True
                active_power_kw = installed_power_kw * use_pct
            elif control_strategy == "Acionamento por etapas" and per_unit_supply > 0 and total_units > 0:
                active_units = max(1, math.ceil(demand_phase / per_unit_supply)) if demand_phase > 0 else 1
                active_units = min(active_units, total_units)
                use_pct = active_units / total_units
                if use_pct < min_pct:
                    use_pct = min_pct
                    limited = True
                active_power_kw = installed_power_kw * use_pct
            elif control_strategy == "Híbrido" and per_unit_supply > 0 and total_units > 0:
                active_units = max(1, math.ceil(demand_phase / per_unit_supply)) if demand_phase > 0 else 1
                active_units = min(active_units, total_units)
                use_pct = max(min_pct, raw_use)
                use_pct = min(use_pct, 1.0)
                active_power_kw = installed_power_kw * use_pct
            else:
                active_units = total_units
                use_pct = max(min_pct, raw_use)
                if use_pct > 1.0:
                    use_pct = 1.0
                    limited = True
                active_power_kw = installed_power_kw * use_pct

        energy_phase = active_power_kw * hours_day * days_phase
        cost_phase = energy_phase * energy_price
        modulated_cost += cost_phase
        active_power_sum_weighted += active_power_kw * days_phase
        total_days += days_phase
        rows.append({
            "Fase": row.get("phase_name", "-"),
            "Biomassa média da fase (kg)": round(biomass_mean, 2),
            "Demanda de O₂ da fase (kg/h)": round(demand_phase, 3),
            "% de uso da capacidade": round(use_pct * 100.0, 1),
            "Equipamentos ativos": int(active_units),
            "Potência ativa da fase (kW)": round(active_power_kw, 2),
            "Dias da fase": int(round(days_phase)),
            "Custo da fase (R$)": round(cost_phase, 2),
            "Observação": (
                "Tecnologia individual por tanque: todos os equipamentos permanecem ativos com potência modulada."
                if technology in ("Chafariz", "Pás")
                else ("Ajustado ao mínimo operacional" if limited and strategy_mode != "Potência fixa no ciclo inteiro" else "")
            ),
        })
    avg_power = (active_power_sum_weighted / total_days) if total_days > 0 else installed_power_kw
    savings = fixed_cost - modulated_cost if strategy_mode != "Potência fixa no ciclo inteiro" else 0.0
    savings_pct = (savings / fixed_cost * 100.0) if fixed_cost > 0 and strategy_mode != "Potência fixa no ciclo inteiro" else 0.0
    summary = {
        "strategy_mode": strategy_mode,
        "control_strategy": control_strategy,
        "control_equipment_recommended": _recommended_control_equipment(technology, strategy_mode),
        "control_note": _recommended_control_note(technology, strategy_mode),
        "cost_cycle_fixed_power": fixed_cost,
        "cost_cycle_modulated": modulated_cost if strategy_mode != "Potência fixa no ciclo inteiro" else fixed_cost,
        "savings_cycle_rs": savings,
        "savings_cycle_pct": savings_pct,
        "average_active_power_kw": avg_power,
        "peak_installed_power_kw": installed_power_kw,
        "all_units_always_active": technology in ("Chafariz", "Pás"),
    }
    return rows, summary


def suggest_blower(
    blower_type: str,
    oxygen_demand_total_kg_h: float,
    diffusion_eff_pct: float,
    altitude_factor: float,
    field_factor: float,
    oxygen_demand_per_tank_kg_h: float = 0.0,
    number_of_units: int = 1,
    geometry: dict | None = None,
) -> dict:
    if blower_type == "Radial":
        library = RADIAL_BLOWER_LIBRARY
    elif blower_type == "Lobular":
        library = LOBULAR_BLOWER_LIBRARY
    else:
        library = RADIAL_BLOWER_LIBRARY + LOBULAR_BLOWER_LIBRARY

    geometry = geometry or {}
    best = None
    for blower in library:
        sea_level_cap_each = _blower_capacity_kg_h(blower, diffusion_eff_pct, 1.0, field_factor)
        cap_each = _blower_capacity_kg_h(blower, diffusion_eff_pct, altitude_factor, field_factor)
        qty = math.ceil(oxygen_demand_total_kg_h / cap_each) if cap_each > 0 else 99
        total_power = blower["power_kw"] * max(qty, 0)
        diffuser_layout = _estimate_diffuser_layout(
            oxygen_demand_per_tank_kg_h=oxygen_demand_per_tank_kg_h,
            number_of_units=number_of_units,
            geometry=geometry,
            diffusion_eff_pct=diffusion_eff_pct,
            altitude_factor=altitude_factor,
            field_factor=field_factor,
            blower_airflow_m3_h_each=blower["airflow_m3_h"],
            blower_qty=max(qty, 0),
            density_kg_m3=float(geometry.get("density_kg_m3", 0.0) or 0.0),
        )
        score = (total_power, qty, blower["power_kw"])
        candidate = {
            "technology": "Soprador",
            "blower_family": "Radial" if blower in RADIAL_BLOWER_LIBRARY else "Lobular",
            "model": blower["model"],
            "power_kw_each": blower["power_kw"],
            "airflow_m3_h_each": blower["airflow_m3_h"],
            "pressure_mbar": blower["pressure_mbar"],
            "qty_system": max(qty, 0),
            "sea_level_oxygen_capacity_each_kg_h": sea_level_cap_each,
            "effective_oxygen_capacity_each_kg_h": cap_each,
            "altitude_factor": altitude_factor,
            "installed_supply_total_kg_h": cap_each * max(qty, 0),
            "sea_level_supply_total_kg_h": sea_level_cap_each * max(qty, 0),
            "diffuser_layout": diffuser_layout,
            "_score": score,
        }
        if best is None or score < best["_score"]:
            best = candidate
    best.pop("_score", None)
    return best


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


def pellet_recommendation_text(start_g: float, end_g: float, pellet_mm: float) -> str:
    if end_g <= 20.0:
        return "1,0–1,5 mm"
    if end_g <= 250.0:
        return "2,0–4,0 mm"
    if end_g <= 650.0:
        return "4,0–6,0 mm"
    if end_g <= 1000.0:
        return "6,0–8,0 mm"
    return "8,0 mm"


def growth_curve_adjustment_factor(inp: DashboardProjectInput) -> float:
    adj = getattr(inp, "growth_curve_adjustment_pct", 100.0)
    try:
        adj = float(adj) / 100.0
    except (TypeError, ValueError):
        adj = 1.0
    return max(0.8, min(adj, 1.2))


def growth_segments(inp: DashboardProjectInput, fish_stocked: float) -> tuple[list[dict], list[dict], float]:
    temp_factor = temperature_growth_factor(inp.water_temperature_c)
    adjust_factor = growth_curve_adjustment_factor(inp)

    segments: list[dict] = []
    growth_curve: list[dict] = []
    current_day = 0.0

    growth_curve.append({
        "day": 0.0,
        "weight_g": inp.initial_weight_g,
        "biomass_kg": fish_stocked * (inp.initial_weight_g / 1000.0),
    })

    for band in GROWTH_SUBRANGES_V2:
        start_g = max(inp.initial_weight_g, band["min_g"])
        end_g = min(inp.target_weight_g, band["max_g"])
        if end_g <= start_g:
            continue

        daily_gain = band["daily_gain_28_g"] * temp_factor * adjust_factor
        daily_gain = max(daily_gain, 0.05)
        exact_days = (end_g - start_g) / daily_gain

        current_day += exact_days
        biomass_end = fish_stocked * (end_g / 1000.0)

        segments.append({
            "label": band["label"],
            "start_g": start_g,
            "end_g": end_g,
            "daily_gain_g": daily_gain,
            "days": exact_days,
            "evidence": band["evidence"],
        })
        growth_curve.append({
            "day": current_day,
            "weight_g": end_g,
            "biomass_kg": biomass_end,
        })

    return segments, growth_curve, current_day


def days_between_weights(start_g: float, end_g: float, segments: list[dict]) -> float:
    total_days = 0.0
    for seg in segments:
        overlap_start = max(start_g, seg["start_g"])
        overlap_end = min(end_g, seg["end_g"])
        if overlap_end <= overlap_start:
            continue
        total_days += (overlap_end - overlap_start) / seg["daily_gain_g"]
    return total_days


def adjusted_daily_growth_g(inp: DashboardProjectInput) -> float:
    relevant = []
    for band in GROWTH_SUBRANGES_V2:
        start_g = max(inp.initial_weight_g, band["min_g"])
        end_g = min(inp.target_weight_g, band["max_g"])
        if end_g <= start_g:
            continue
        relevant.append(band["daily_gain_28_g"] * temperature_growth_factor(inp.water_temperature_c) * growth_curve_adjustment_factor(inp))
    return sum(relevant) / len(relevant) if relevant else 0.0


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
        {
            "phase_name": "Fase 5",
            "min_g": inp.phase5_min_g,
            "max_g": inp.phase5_max_g,
            "feeding_rate_percent": inp.phase5_feeding_rate_percent,
            "meals_per_day": inp.phase5_meals_per_day,
            "protein_percent": inp.phase5_protein_percent,
            "pellet_mm": inp.phase5_pellet_mm,
            "feed_price_per_kg": inp.phase5_feed_price_per_kg,
            "phase_fcr": inp.phase5_fcr,
        },
    ]


def build_feeding_plan(
    inp: DashboardProjectInput,
    fish_stocked: float,
) -> tuple[list[dict], list[dict], list[dict], float, float, list[dict]]:
    feeding_plan: list[dict] = []
    cost_curve: list[dict] = []
    total_feed_kg = 0.0
    cumulative_feed_cost = 0.0

    segments, growth_curve, cycle_days = growth_segments(inp, fish_stocked)

    for phase in phase_rows(inp):
        start_g = max(inp.initial_weight_g, phase["min_g"])
        end_g = min(inp.target_weight_g, phase["max_g"])

        if end_g <= start_g:
            continue

        phase_days = max(1, round(days_between_weights(start_g, end_g, segments)))

        biomass_start = fish_stocked * (start_g / 1000.0)
        biomass_end = fish_stocked * (end_g / 1000.0)
        biomass_gain = max(biomass_end - biomass_start, 0.0)

        phase_fcr = phase["phase_fcr"]
        feed_phase = biomass_gain * phase_fcr
        cost_phase = feed_phase * phase["feed_price_per_kg"]

        total_feed_kg += feed_phase
        cumulative_feed_cost += cost_phase

        curve_day = days_between_weights(inp.initial_weight_g, end_g, segments)
        cost_curve.append({
            "day": curve_day,
            "cumulative_feed_cost": cumulative_feed_cost,
        })

        cumulative_days_end = curve_day
        cumulative_days_start = max(cumulative_days_end - phase_days, 0.0)
        cycle_share_pct = (phase_days / cycle_days * 100.0) if cycle_days > 0 else 0.0

        feeding_plan.append({
            "phase_name": phase["phase_name"],
            "weight_range": f"{start_g:.0f}-{end_g:.0f} g",
            "start_weight_g": start_g,
            "end_weight_g": end_g,
            "biomass_start_phase_kg": biomass_start,
            "biomass_end_phase_kg": biomass_end,
            "days_in_phase": phase_days,
            "days_in_phase_exact": days_between_weights(start_g, end_g, segments),
            "cumulative_days_start": cumulative_days_start,
            "cumulative_days_end": cumulative_days_end,
            "cycle_share_pct": cycle_share_pct,
            "feeding_rate_percent": phase["feeding_rate_percent"],
            "meals_per_day": phase["meals_per_day"],
            "protein_percent": phase["protein_percent"],
            "pellet_mm": phase["pellet_mm"],
            "pellet_recommendation": pellet_recommendation_text(start_g, end_g, phase["pellet_mm"]),
            "feed_price_per_kg": phase["feed_price_per_kg"],
            "phase_fcr": phase_fcr,
            "biomass_gain_phase_kg": biomass_gain,
            "feed_phase_kg": feed_phase,
            "feed_phase_cost": cost_phase,
            "phase_daily_growth_g": biomass_gain * 1000 / fish_stocked / phase_days if fish_stocked > 0 and phase_days > 0 else 0.0,
        })

    return feeding_plan, growth_curve, cost_curve, cycle_days, total_feed_kg, segments


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
) -> dict:
    strategy = getattr(inp, "production_strategy", "Ciclos simultâneos")
    basis = getattr(inp, "scheduling_basis", "Intervalo entre despescas")
    cycle_months = cycle_days / 30.44 if cycle_days else 0.0

    if strategy == "Ciclos simultâneos":
        batches_in_parallel = 1
        harvest_interval_months = cycle_months
        units_per_batch_exact = float(inp.number_of_units)
        suggested_units = inp.number_of_units
        status = "Operação simultânea"
        recommendation = "Todos os tanques entram e saem juntos."
    else:
        if basis == "Intervalo entre despescas":
            harvest_interval_months = max(getattr(inp, "harvest_interval_months", 1.0), 0.25)
            batches_in_parallel = max(1, math.ceil(cycle_months / harvest_interval_months)) if harvest_interval_months > 0 else 1
            units_per_batch_exact = 1.0
            suggested_units = batches_in_parallel
            if inp.number_of_units < suggested_units:
                status = "Insuficiente para a meta informada"
                recommendation = f"Para despescas a cada {harvest_interval_months:.2f} mês(es), o sistema sugere pelo menos {suggested_units} tanque(s)."
            elif inp.number_of_units == suggested_units:
                status = "Compatível com a meta"
                recommendation = "O número informado de tanques atende a meta de despescas."
            else:
                status = "Com folga operacional"
                recommendation = "Há folga operacional em relação à meta de despescas informada."
        elif basis == "Número de lotes":
            batches_in_parallel = max(1, int(getattr(inp, "manual_parallel_batches", 1)))
            harvest_interval_months = cycle_months / batches_in_parallel if batches_in_parallel > 0 else cycle_months
            units_per_batch_exact = inp.number_of_units / batches_in_parallel if batches_in_parallel > 0 else float(inp.number_of_units)
            suggested_units = batches_in_parallel
            status = "Escalonamento por número de lotes"
            recommendation = "Revise se a quantidade de tanques por lote ficou operacionalmente coerente."
        else:
            desired_units_per_batch = max(1, int(getattr(inp, "desired_units_per_batch", 1)))
            batches_in_parallel = max(1, math.floor(inp.number_of_units / desired_units_per_batch))
            harvest_interval_months = cycle_months / batches_in_parallel if batches_in_parallel > 0 else cycle_months
            units_per_batch_exact = float(desired_units_per_batch)
            suggested_units = batches_in_parallel * desired_units_per_batch
            status = "Escalonamento por tanques por lote"
            recommendation = "Revise se o número de lotes formado atende à frequência desejada de despescas."

    harvests_per_year_stable = 12.0 / harvest_interval_months if harvest_interval_months > 0 else 0.0
    production_per_harvest_kg = production_per_year_kg / harvests_per_year_stable if harvests_per_year_stable > 0 else production_per_cycle_kg
    feed_per_harvest_kg = feed_consumption_year_kg / harvests_per_year_stable if harvests_per_year_stable > 0 else feed_consumption_cycle_kg
    revenue_per_harvest = revenue_year / harvests_per_year_stable if harvests_per_year_stable > 0 else revenue_cycle
    fingerling_cost_per_harvest = fingerling_cost_year / harvests_per_year_stable if harvests_per_year_stable > 0 else fingerling_cost_cycle

    # Ano 1: considera a lacuna até a primeira despesca.
    warmup_months = cycle_months
    remaining_months_year1 = max(12.0 - warmup_months, 0.0)
    harvests_year1 = max(0, math.floor(remaining_months_year1 / harvest_interval_months)) if strategy == "Escalonada" and harvest_interval_months > 0 else (1 if cycle_months <= 12 else 0)
    production_year1_kg = production_per_harvest_kg * harvests_year1
    revenue_year1 = revenue_per_harvest * harvests_year1
    feed_year1_kg = feed_per_harvest_kg * harvests_year1

    # Ano 2 / regime estabilizado: depois da rampa biológica inicial,
    # o sistema passa a operar com despescas regulares.
    harvests_year2_stable = harvests_per_year_stable
    production_year2_kg = production_per_harvest_kg * harvests_year2_stable
    revenue_year2 = revenue_per_harvest * harvests_year2_stable
    feed_year2_kg = feed_per_harvest_kg * harvests_year2_stable
    monthly_production_stable_kg = production_year2_kg / 12.0 if production_year2_kg else 0.0
    monthly_revenue_stable = revenue_year2 / 12.0 if revenue_year2 else 0.0
    monthly_feed_stable_kg = feed_year2_kg / 12.0 if feed_year2_kg else 0.0

    # Alevinos por despesca/lote considera a quantidade de tanques por lote.
    fish_stocked_per_harvest_batch = fish_stocked_per_cycle * max(units_per_batch_exact, 1.0)
    fish_stocked_year1 = fish_stocked_per_harvest_batch * harvests_year1
    fish_stocked_year2 = fish_stocked_per_harvest_batch * harvests_year2_stable

    batch_distribution_note = ""
    if strategy == "Escalonada" and basis == "Intervalo entre despescas":
        batch_distribution_note = f"Com {inp.number_of_units} tanque(s) e intervalo de {harvest_interval_months:.2f} mês(es), o sistema trabalha com {batches_in_parallel} lote(s) em paralelo; a primeira receita ocorre apenas após o fechamento do ciclo biológico inicial."

    return {
        "production_strategy": strategy,
        "scheduling_basis": basis,
        "biological_cycle_days": cycle_days,
        "biological_cycle_months": cycle_months,
        "warmup_months_without_revenue": warmup_months,
        "harvest_interval_months": harvest_interval_months,
        "harvest_interval_days": harvest_interval_months * 30.44,
        "harvests_per_year": harvests_per_year_stable,
        "harvests_year1": harvests_year1,
        "batches_in_parallel": batches_in_parallel,
        "units_per_batch_exact": units_per_batch_exact,
        "batch_volume_m3": units_per_batch_exact * inp.unit_volume_m3,
        "production_per_harvest_kg": production_per_harvest_kg,
        "feed_per_harvest_kg": feed_per_harvest_kg,
        "revenue_per_harvest": revenue_per_harvest,
        "fingerling_cost_per_harvest": fingerling_cost_per_harvest,
        "fish_stocked_per_harvest": fish_stocked_per_cycle,
        "first_harvest_after_days": cycle_days,
        "first_harvest_after_months": cycle_months,
        "production_year1_kg": production_year1_kg,
        "revenue_year1": revenue_year1,
        "feed_year1_kg": feed_year1_kg,
        "harvests_year2_stable": harvests_year2_stable,
        "production_year2_kg": production_year2_kg,
        "revenue_year2": revenue_year2,
        "feed_year2_kg": feed_year2_kg,
        "monthly_production_stable_kg": monthly_production_stable_kg,
        "monthly_revenue_stable": monthly_revenue_stable,
        "monthly_feed_stable_kg": monthly_feed_stable_kg,
        "fish_stocked_per_harvest_batch": fish_stocked_per_harvest_batch,
        "fish_stocked_year1": fish_stocked_year1,
        "fish_stocked_year2": fish_stocked_year2,
        "minimum_units_suggested": suggested_units,
        "status": status,
        "recommendation": recommendation,
        "actual_interval_months_with_informed_units": (cycle_months / max(inp.number_of_units, 1)) if strategy == "Escalonada" and basis == "Intervalo entre despescas" else harvest_interval_months,
        "batch_distribution_note": batch_distribution_note,
    }


def resolve_economic_costs(inp: DashboardProjectInput) -> dict:
    economic_model_mode = getattr(inp, "economic_model_mode", "Simplificado")

    if economic_model_mode == "Fixo + por tanque":
        electricity_fixed = float(getattr(inp, "electricity_cost_fixed_cycle", 0.0))
        electricity_variable = float(getattr(inp, "electricity_cost_per_unit_cycle", 0.0)) * inp.number_of_units
        labor_fixed = float(getattr(inp, "labor_cost_fixed_cycle", 0.0))
        labor_variable = float(getattr(inp, "labor_cost_per_unit_cycle", 0.0)) * inp.number_of_units
        other_fixed = float(getattr(inp, "other_cost_fixed_cycle", 0.0))
        other_variable = float(getattr(inp, "other_cost_per_unit_cycle", 0.0)) * inp.number_of_units
        capex_fixed = float(getattr(inp, "capex_fixed_total", 0.0))
        capex_variable = float(getattr(inp, "capex_per_unit", 0.0)) * inp.number_of_units

        return {
            "economic_model_mode": economic_model_mode,
            "cost_scaling_mode": "Fixos (não escalar)",
            "cost_reference_units": max(inp.number_of_units, 1),
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

    if economic_model_mode == "Manual (CAPEX total)":
        return {
            "economic_model_mode": economic_model_mode,
            "cost_scaling_mode": "Fixos (não escalar)",
            "cost_reference_units": max(inp.number_of_units, 1),
            "cost_scale_factor": 1.0,
            "electricity_cost_cycle_effective": float(inp.electricity_cost_cycle),
            "labor_cost_cycle_effective": float(inp.labor_cost_cycle),
            "other_costs_cycle_effective": float(inp.other_costs_cycle),
            "capex_total_effective": float(inp.capex_total),
            "electricity_cost_fixed_cycle_effective": float(inp.electricity_cost_cycle),
            "electricity_cost_variable_cycle_effective": 0.0,
            "labor_cost_fixed_cycle_effective": float(inp.labor_cost_cycle),
            "labor_cost_variable_cycle_effective": 0.0,
            "other_cost_fixed_cycle_effective": float(inp.other_costs_cycle),
            "other_cost_variable_cycle_effective": 0.0,
            "capex_fixed_total_effective": float(inp.capex_total),
            "capex_variable_total_effective": 0.0,
        }

    cost_reference_units = max(int(getattr(inp, "cost_reference_units", max(inp.number_of_units, 1))), 1)
    if getattr(inp, "cost_scaling_mode", "Fixos (não escalar)") == "Escalonar pelo nº de tanques":
        cost_scale_factor = inp.number_of_units / cost_reference_units
    else:
        cost_scale_factor = 1.0

    electricity_cost_cycle_effective = float(inp.electricity_cost_cycle) * cost_scale_factor
    labor_cost_cycle_effective = float(inp.labor_cost_cycle) * cost_scale_factor
    other_costs_cycle_effective = float(inp.other_costs_cycle) * cost_scale_factor
    capex_total_effective = float(inp.capex_total) * cost_scale_factor

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





def suggest_hybrid_fountain_paddle(
    system_type: str,
    oxygen_demand_per_tank_kg_h: float,
    temp_factor: float,
    altitude_factor: float,
    field_factor: float,
    geometry: dict,
) -> dict:
    """
    Dimensionamento híbrido preliminar: chafariz para oxigenação superficial
    e pás como complemento de oxigenação/circulação quando a geometria permitir.

    A lógica usa primeiro o melhor arranjo A1-A4 de chafariz. Havendo déficit,
    complementa com pás até o limite geométrico-operacional. Em tanques circulares
    grandes, pode incluir 1 pá auxiliar para reforço de vórtice/circulação.
    """
    fountain = suggest_surface_aerator(
        "Chafariz", system_type, oxygen_demand_per_tank_kg_h,
        temp_factor, altitude_factor, field_factor, geometry
    )
    paddle = suggest_surface_aerator(
        "Pás", system_type, oxygen_demand_per_tank_kg_h,
        temp_factor, altitude_factor, field_factor, geometry
    )

    f_qty = int(fountain.get("qty_per_tank", 0) or 0)
    f_supply = float(fountain.get("installed_supply_per_tank_kg_h", 0.0) or 0.0)
    f_supply_sea = float(fountain.get("sea_level_supply_per_tank_kg_h", f_supply) or 0.0)
    f_power = float(fountain.get("consumption_kwh_each", 0.0) or 0.0) * f_qty

    shortfall = max(0.0, oxygen_demand_per_tank_kg_h - f_supply)
    paddle_allowed = bool(paddle.get("allowed", False))
    p_unit_supply = float(paddle.get("effective_sort_kg_h", 0.0) or 0.0)
    p_unit_supply_sea = float(paddle.get("sea_level_effective_sort_kg_h", p_unit_supply) or 0.0)
    p_max = int(paddle.get("max_units_per_tank", 0) or 0)

    diameter = float(geometry.get("diameter_m", 0.0) or 0.0)
    # Em tanque circular grande, admite-se 1 pá auxiliar para vórtice/circulação,
    # mesmo quando o chafariz já cobre a demanda de O2.
    auxiliary_for_vortex = 1 if (paddle_allowed and diameter >= 14.0 and shortfall <= 0.0) else 0
    p_qty_needed = math.ceil(shortfall / p_unit_supply) if shortfall > 0.0 and p_unit_supply > 0.0 else auxiliary_for_vortex
    p_qty = min(max(p_qty_needed, 0), p_max) if paddle_allowed else 0

    p_supply = p_unit_supply * p_qty
    p_supply_sea = p_unit_supply_sea * p_qty
    p_power = float(paddle.get("consumption_kwh_each", 0.0) or 0.0) * p_qty

    total_supply = f_supply + p_supply
    total_supply_sea = f_supply_sea + p_supply_sea
    ratio = total_supply / oxygen_demand_per_tank_kg_h if oxygen_demand_per_tank_kg_h > 0 else 0.0
    feasible = ratio >= 1.0

    warnings = []
    if fountain.get("warning"):
        warnings.append(str(fountain.get("warning")))
    if shortfall > 0 and p_qty <= 0:
        warnings.append("O arranjo de chafariz não cobre a demanda e não houve complementação por pás viável.")
    elif shortfall > 0 and total_supply < oxygen_demand_per_tank_kg_h:
        warnings.append("Mesmo com tecnologia híbrida, a oferta ainda fica abaixo da demanda estimada.")
    if p_qty > 0:
        warnings.append("Pás consideradas como apoio de circulação/vórtice; validar posicionamento para não ressuspender sólidos nem comprometer o dreno central.")

    rows = []
    if f_qty > 0:
        rows.append({
            "tecnologia": "Chafariz",
            "modelo": fountain.get("model", "-"),
            "quantidade_por_tanque": f_qty,
            "quantidade": f_qty,
            "arranjo": fountain.get("arrangement", "-"),
            "arranjo_descricao": fountain.get("arrangement_label", "-"),
            "oferta_por_tanque_kg_h": round(f_supply, 3),
        })
    if p_qty > 0:
        rows.append({
            "tecnologia": "Pás",
            "modelo": paddle.get("model", "-"),
            "quantidade_por_tanque": p_qty,
            "quantidade": p_qty,
            "arranjo": paddle.get("arrangement", "auxiliar"),
            "arranjo_descricao": paddle.get("arrangement_label", "circulação/vórtice auxiliar"),
            "oferta_por_tanque_kg_h": round(p_supply, 3),
        })

    return {
        "technology": "Híbrido: Chafariz + Pás",
        "model": " + ".join([r["modelo"] for r in rows]) if rows else "-",
        "qty_per_tank": f_qty + p_qty,
        "qty_fountain_per_tank": f_qty,
        "qty_paddle_per_tank": p_qty,
        "installed_supply_per_tank_kg_h": total_supply,
        "sea_level_supply_per_tank_kg_h": total_supply_sea,
        "power_kw_per_tank": f_power + p_power,
        "feasible": feasible,
        "oxygen_offer_demand_ratio": ratio,
        "warning": " ".join(warnings).strip(),
        "rows": rows,
        "fountain_details": fountain,
        "paddle_details": paddle,
    }


def suggest_hybrid_air_surface(blower: dict, surface_items: list[dict], oxygen_demand_total_kg_h: float, number_of_units: int) -> dict:
    """
    Combina soprador com chafariz e/ou pás sem somar equipamentos completos.

    A versão anterior somava o soprador dimensionado para 100% da demanda com
    aeradores superficiais também dimensionados para 100% da demanda. Isso criava
    oferta artificialmente alta. Aqui a lógica passa a ser por parcelas:

    - Chafariz: parcela superficial de oxigenação/renovação da lâmina d'água.
    - Pás: parcela auxiliar, principalmente circulação/vórtice.
    - Soprador: cobre apenas o residual de O₂ depois das parcelas superficiais.

    Assim, o híbrido deixa de ser uma soma bruta e passa a ser uma composição
    técnico-operacional orientada pela demanda real de O₂.
    """
    units = max(1, int(number_of_units or 1))
    demand_total = max(0.0, float(oxygen_demand_total_kg_h or 0.0))
    demand_per_tank = demand_total / units if units > 0 else demand_total

    rows: list[dict] = []
    total_supply = 0.0
    sea_supply = 0.0
    total_power = 0.0
    total_qty = 0
    warnings: list[str] = []

    has_fountain = any(isinstance(i, dict) and i.get("technology") == "Chafariz" for i in surface_items)
    has_paddle = any(isinstance(i, dict) and i.get("technology") == "Pás" for i in surface_items)

    # Parcelas operacionais preliminares.
    # Elas são intencionalmente conservadoras para evitar superdimensionamento:
    # o soprador cobre o residual e as pás não devem ser tratadas como fonte principal.
    target_share_by_technology = {
        "Chafariz": 0.40 if has_paddle else 0.55,
        "Pás": 0.15 if has_fountain else 0.25,
    }

    remaining_total = demand_total

    for item in surface_items:
        if not isinstance(item, dict):
            continue

        tech = str(item.get("technology", "superficial"))
        unit_supply = max(0.0, float(item.get("effective_sort_kg_h", 0.0) or 0.0))
        unit_supply_sea = max(0.0, float(item.get("sea_level_effective_sort_kg_h", unit_supply) or unit_supply))
        max_qpt = max(0, int(item.get("max_units_per_tank", item.get("qty_per_tank", 0)) or 0))
        power_each = max(0.0, float(item.get("consumption_kwh_each", 0.0) or 0.0))

        if unit_supply <= 0.0 or max_qpt <= 0:
            if item.get("warning"):
                warnings.append(str(item.get("warning")))
            continue

        target_share = target_share_by_technology.get(tech, 0.20)
        target_per_tank = demand_per_tank * target_share

        # Nunca dimensionar a parcela superficial acima do residual por tanque.
        target_per_tank = min(target_per_tank, max(0.0, remaining_total / units))

        qpt_needed = math.ceil(target_per_tank / unit_supply) if target_per_tank > 0 else 0
        qpt = min(max_qpt, max(0, qpt_needed))

        # Para pás em tanque circular grande, admite-se uma unidade auxiliar para
        # circulação/vórtice quando existe demanda total e a geometria permite.
        if tech == "Pás" and qpt == 0 and demand_total > 0 and max_qpt > 0:
            qpt = 1

        q = qpt * units
        supply_tank = unit_supply * qpt
        sea_tank = unit_supply_sea * qpt
        supply_total_component = supply_tank * units
        sea_total_component = sea_tank * units

        if qpt > 0:
            rows.append({
                "tecnologia": tech,
                "modelo": item.get("model", "-"),
                "quantidade_por_tanque": qpt,
                "quantidade": q,
                "arranjo": item.get("arrangement", "-"),
                "arranjo_descricao": item.get("arrangement_label", "-"),
                "oferta_por_tanque_kg_h": round(supply_tank, 3),
                "papel_no_hibrido": (
                    "oxigenação superficial parcial"
                    if tech == "Chafariz"
                    else "circulação/vórtice e apoio parcial de O₂"
                ),
            })
            total_supply += supply_total_component
            sea_supply += sea_total_component
            total_power += power_each * q
            total_qty += q
            remaining_total = max(0.0, remaining_total - supply_total_component)

    # Soprador cobre o residual, não a demanda inteira.
    if isinstance(blower, dict) and remaining_total > 0:
        cap_each = max(0.0, float(blower.get("effective_oxygen_capacity_each_kg_h", 0.0) or 0.0))
        cap_each_sea = max(0.0, float(blower.get("sea_level_oxygen_capacity_each_kg_h", cap_each) or cap_each))
        power_each = max(0.0, float(blower.get("power_kw_each", 0.0) or 0.0))

        if cap_each > 0:
            q = max(1, math.ceil(remaining_total / cap_each))
            supply = cap_each * q
            sea = cap_each_sea * q
            total_supply += supply
            sea_supply += sea
            total_power += power_each * q
            total_qty += q

            rows.append({
                "tecnologia": "Soprador",
                "modelo": blower.get("model", "-"),
                "quantidade_por_tanque": "sistema",
                "quantidade": q,
                "arranjo": "difusão",
                "arranjo_descricao": blower.get("diffuser_layout", {}).get("diffuser_name", "mangueira/difusor"),
                "oferta_por_tanque_kg_h": round(supply / units, 3),
                "papel_no_hibrido": "cobertura do residual de O₂",
            })

            # Ajuste proporcional da metragem exibida quando houver layout.
            # A metragem original é calculada para demanda plena; no híbrido, ela
            # deve ser proporcional ao residual coberto pelo soprador.
            layout = blower.get("diffuser_layout")
            if isinstance(layout, dict) and demand_total > 0:
                residual_fraction = min(1.0, max(0.0, remaining_total / demand_total))
                adjusted_layout = dict(layout)
                for key in ("meters_per_tank_required", "meters_total_required", "meters_per_tank_recommended", "meters_total_recommended"):
                    if key in adjusted_layout and isinstance(adjusted_layout.get(key), (int, float)):
                        adjusted_layout[key] = adjusted_layout[key] * residual_fraction
                adjusted_layout["hybrid_residual_fraction"] = residual_fraction
                rows[-1]["layout_hibrido"] = adjusted_layout

            remaining_total = max(0.0, remaining_total - supply)
        else:
            warnings.append("Soprador selecionado sem capacidade efetiva calculável para cobrir o residual de O₂.")

    ratio = total_supply / demand_total if demand_total > 0 else 0.0

    if ratio < 1.0:
        warnings.append("Tecnologia híbrida ainda abaixo da demanda estimada de O₂; revisar densidade, potência ou tecnologia.")
    if ratio > 1.60:
        warnings.append(
            "A oferta híbrida ficou muito acima da demanda. Isso pode indicar equipamento mínimo muito grande "
            "para o residual calculado; avaliar custo, modulação, escolha de modelos menores ou operação por etapas."
        )
    if has_paddle:
        warnings.append("Pás usadas como apoio de circulação/vórtice; avaliar posicionamento e custo energético.")
    if isinstance(blower, dict):
        warnings.append("Soprador/difusão dimensionado para o residual do híbrido; validar pressão, perdas de carga e metragem em campo.")

    return {
        "technology": "Híbrido",
        "model": " + ".join([str(r.get("modelo", "-")) for r in rows]) if rows else "-",
        "qty_per_tank": None,
        "quantity_total": total_qty,
        "installed_supply_total_kg_h": total_supply,
        "sea_level_supply_total_kg_h": sea_supply,
        "installed_supply_per_tank_kg_h": total_supply / units,
        "sea_level_supply_per_tank_kg_h": sea_supply / units,
        "power_kw_total": total_power,
        "feasible": ratio >= 1.0,
        "oxygen_offer_demand_ratio": ratio,
        "warning": " ".join(dict.fromkeys([w for w in warnings if w]).keys()),
        "rows": rows,
        "blower_details": blower,
        "surface_details": surface_items,
        "hybrid_logic_note": (
            "Dimensionamento por demanda residual: componentes superficiais cobrem parcelas operacionais "
            "e o soprador cobre apenas o O₂ remanescente."
        ),
    }


def calculate_dashboard_project(inp: DashboardProjectInput) -> dict:
    geometry = compute_geometry(inp)
    geometry["density_kg_m3"] = float(getattr(inp, "density_kg_m3", 0.0) or 0.0)
    inp.unit_volume_m3 = geometry["unit_volume_m3"]

    total_volume_m3 = inp.number_of_units * geometry["unit_volume_m3"]
    final_biomass_total_kg = total_volume_m3 * inp.density_kg_m3
    final_biomass_per_tank_kg = geometry["unit_volume_m3"] * inp.density_kg_m3

    target_weight_kg = inp.target_weight_g / 1000.0
    fish_harvested = final_biomass_total_kg / target_weight_kg if target_weight_kg > 0 else 0.0
    fish_stocked = fish_harvested / inp.survival_rate if inp.survival_rate > 0 else 0.0
    fish_stocked_per_tank = fish_stocked / max(inp.number_of_units, 1)
    fish_harvested_per_tank = fish_harvested / max(inp.number_of_units, 1)

    feeding_plan, growth_curve, cost_curve, cycle_days, feed_consumption_cycle_kg, growth_segments_used = build_feeding_plan(
        inp,
        fish_stocked,
    )

    # ciclos/ano passam a ser consequência da base biológica
    cycles_per_year_effective = 365.0 / cycle_days if cycle_days > 0 else 0.0
    revenue_cycle = final_biomass_total_kg * inp.sale_price_per_kg

    safety_factor = 1.0 + (getattr(inp, "aeration_safety_factor_pct", 20.0) / 100.0)
    oxygen_demand_kg_h = final_biomass_total_kg * (inp.oxygen_demand_mg_per_kg_h / 1_000_000.0) * safety_factor
    oxygen_demand_per_tank_kg_h = final_biomass_per_tank_kg * (inp.oxygen_demand_mg_per_kg_h / 1_000_000.0) * safety_factor

    altitude_factor = altitude_transfer_factor(getattr(inp, "site_altitude_m", 0.0))
    temp_aeration_factor = surface_aeration_base_factor(inp.water_temperature_c)
    field_factor = max(min(getattr(inp, "field_efficiency_pct", 85.0) / 100.0, 1.0), 0.1)

    aeration_mode = getattr(inp, "aeration_mode", "Automático")
    automatic_tech = getattr(inp, "automatic_aeration_technology", "Chafariz")
    blower_type = getattr(inp, "blower_type", "Automático")

    suggested_fountain = suggest_surface_aerator("Chafariz", inp.system_type, oxygen_demand_per_tank_kg_h, temp_aeration_factor, altitude_factor, field_factor, geometry)
    suggested_paddle = suggest_surface_aerator("Pás", inp.system_type, oxygen_demand_per_tank_kg_h, temp_aeration_factor, altitude_factor, field_factor, geometry)
    suggested_blower = suggest_blower(blower_type if blower_type in ("Radial", "Lobular") else "Automático", oxygen_demand_kg_h, getattr(inp, "diffusion_efficiency_pct", 12.0), altitude_factor, field_factor, oxygen_demand_per_tank_kg_h, inp.number_of_units, geometry)

    selected_aeration = {
        "mode": aeration_mode,
        "technology": automatic_tech if aeration_mode == "Automático" else "Manual",
        "model": "-",
        "quantity_total": 0,
        "installed_oxygen_supply_kg_h": 0.0,
        "installed_oxygen_supply_sea_level_kg_h": 0.0,
        "aeration_energy_cost_cycle": 0.0,
        "power_installed_kw": 0.0,
        "compatibility_warning": "",
        "details": {},
    }

    if aeration_mode == "Automático":
        if automatic_tech == "Chafariz":
            chosen = suggested_fountain
            total_qty = chosen["qty_per_tank"] * inp.number_of_units
            supply = chosen["installed_supply_per_tank_kg_h"] * inp.number_of_units
            sea_level_supply = chosen.get("sea_level_supply_per_tank_kg_h", chosen["installed_supply_per_tank_kg_h"]) * inp.number_of_units
            power_kw = chosen["consumption_kwh_each"] * total_qty
            selected_aeration.update({
                "technology": "Chafariz",
                "model": chosen["model"],
                "quantity_total": total_qty,
                "installed_oxygen_supply_kg_h": supply,
                "installed_oxygen_supply_sea_level_kg_h": sea_level_supply,
                "power_installed_kw": power_kw,
                "compatibility_warning": chosen["warning"],
                "details": chosen,
            })
        elif automatic_tech == "Pás":
            chosen = suggested_paddle
            total_qty = chosen["qty_per_tank"] * inp.number_of_units
            supply = chosen["installed_supply_per_tank_kg_h"] * inp.number_of_units
            sea_level_supply = chosen.get("sea_level_supply_per_tank_kg_h", chosen["installed_supply_per_tank_kg_h"]) * inp.number_of_units
            power_kw = chosen["consumption_kwh_each"] * total_qty
            selected_aeration.update({
                "technology": "Pás",
                "model": chosen["model"],
                "quantity_total": total_qty,
                "installed_oxygen_supply_kg_h": supply,
                "installed_oxygen_supply_sea_level_kg_h": sea_level_supply,
                "power_installed_kw": power_kw,
                "compatibility_warning": chosen["warning"],
                "details": chosen,
            })
        elif automatic_tech == "Híbrido: Chafariz + Pás":
            chosen = suggest_hybrid_fountain_paddle(
                inp.system_type,
                oxygen_demand_per_tank_kg_h,
                temp_aeration_factor,
                altitude_factor,
                field_factor,
                geometry,
            )
            total_qty = int(chosen.get("qty_per_tank", 0) or 0) * inp.number_of_units
            supply = float(chosen.get("installed_supply_per_tank_kg_h", 0.0) or 0.0) * inp.number_of_units
            sea_level_supply = float(chosen.get("sea_level_supply_per_tank_kg_h", supply) or 0.0) * inp.number_of_units
            power_kw = float(chosen.get("power_kw_per_tank", 0.0) or 0.0) * inp.number_of_units
            selected_aeration.update({
                "technology": "Híbrido: Chafariz + Pás",
                "model": chosen["model"],
                "quantity_total": total_qty,
                "installed_oxygen_supply_kg_h": supply,
                "installed_oxygen_supply_sea_level_kg_h": sea_level_supply,
                "power_installed_kw": power_kw,
                "compatibility_warning": chosen["warning"],
                "details": chosen,
            })
        elif automatic_tech == "Soprador":
            chosen = suggested_blower
            total_qty = chosen["qty_system"]
            supply = chosen["installed_supply_total_kg_h"]
            sea_level_supply = chosen.get("sea_level_supply_total_kg_h", supply)
            power_kw = chosen["power_kw_each"] * total_qty
            selected_aeration.update({
                "technology": f"Soprador {chosen['blower_family']}",
                "model": chosen["model"],
                "quantity_total": total_qty,
                "installed_oxygen_supply_kg_h": supply,
                "installed_oxygen_supply_sea_level_kg_h": sea_level_supply,
                "power_installed_kw": power_kw,
                "compatibility_warning": chosen.get("warning", ""),
                "details": chosen,
            })
        elif automatic_tech in ("Híbrido: Soprador + Pás", "Híbrido: Soprador + Chafariz", "Híbrido: Soprador + Chafariz + Pás"):
            surface_items = []
            if "Chafariz" in automatic_tech:
                surface_items.append(suggested_fountain)
            if "Pás" in automatic_tech:
                surface_items.append(suggested_paddle)
            chosen = suggest_hybrid_air_surface(suggested_blower, surface_items, oxygen_demand_kg_h, inp.number_of_units)
            total_qty = int(chosen.get("quantity_total", 0) or 0)
            supply = float(chosen.get("installed_supply_total_kg_h", 0.0) or 0.0)
            sea_level_supply = float(chosen.get("sea_level_supply_total_kg_h", supply) or supply)
            power_kw = float(chosen.get("power_kw_total", 0.0) or 0.0)
            selected_aeration.update({
                "technology": automatic_tech,
                "model": chosen.get("model", "-"),
                "quantity_total": total_qty,
                "installed_oxygen_supply_kg_h": supply,
                "installed_oxygen_supply_sea_level_kg_h": sea_level_supply,
                "power_installed_kw": power_kw,
                "compatibility_warning": chosen.get("warning", ""),
                "details": chosen,
            })
    else:
        total_supply = 0.0
        total_supply_sea_level = 0.0
        total_power_kw = 0.0
        total_qty = 0
        detail_rows = []

        if getattr(inp, "manual_use_fountain", False):
            equipment = next((e for e in FOUNTAIN_LIBRARY if e["model"] == getattr(inp, "manual_fountain_model", "")), FOUNTAIN_LIBRARY[0])
            qty = max(0, int(getattr(inp, "manual_fountain_qty", 0)))
            eff_sort = _surface_effective_sort(equipment, temp_aeration_factor, altitude_factor, field_factor)
            eff_sort_sea_level = _surface_effective_sort(equipment, temp_aeration_factor, 1.0, field_factor)
            total_supply += eff_sort * qty
            total_supply_sea_level += eff_sort_sea_level * qty
            total_power_kw += equipment["consumption_kwh"] * qty
            total_qty += qty
            detail_rows.append({"tecnologia": "Chafariz", "modelo": equipment["model"], "quantidade": qty})

        if getattr(inp, "manual_use_paddlewheel", False):
            equipment = next((e for e in PADDLEWHEEL_LIBRARY if e["model"] == getattr(inp, "manual_paddle_model", "")), PADDLEWHEEL_LIBRARY[0])
            qty = max(0, int(getattr(inp, "manual_paddle_qty", 0)))
            eff_sort = _surface_effective_sort(equipment, temp_aeration_factor, altitude_factor, field_factor)
            eff_sort_sea_level = _surface_effective_sort(equipment, temp_aeration_factor, 1.0, field_factor)
            total_supply += eff_sort * qty
            total_supply_sea_level += eff_sort_sea_level * qty
            total_power_kw += equipment["consumption_kwh"] * qty
            total_qty += qty
            detail_rows.append({"tecnologia": "Pás", "modelo": equipment["model"], "quantidade": qty})

        if getattr(inp, "manual_use_radial", False):
            equipment = next((e for e in RADIAL_BLOWER_LIBRARY if e["model"] == getattr(inp, "manual_radial_model", "")), RADIAL_BLOWER_LIBRARY[0])
            qty = max(0, int(getattr(inp, "manual_radial_qty", 0)))
            cap_each = _blower_capacity_kg_h(equipment, getattr(inp, "diffusion_efficiency_pct", 12.0), altitude_factor, field_factor)
            cap_each_sea_level = _blower_capacity_kg_h(equipment, getattr(inp, "diffusion_efficiency_pct", 12.0), 1.0, field_factor)
            total_supply += cap_each * qty
            total_supply_sea_level += cap_each_sea_level * qty
            total_power_kw += equipment["power_kw"] * qty
            total_qty += qty
            detail_rows.append({"tecnologia": "Soprador radial", "modelo": equipment["model"], "quantidade": qty})

        if getattr(inp, "manual_use_lobular", False):
            equipment = next((e for e in LOBULAR_BLOWER_LIBRARY if e["model"] == getattr(inp, "manual_lobular_model", "")), LOBULAR_BLOWER_LIBRARY[0])
            qty = max(0, int(getattr(inp, "manual_lobular_qty", 0)))
            cap_each = _blower_capacity_kg_h(equipment, getattr(inp, "diffusion_efficiency_pct", 12.0), altitude_factor, field_factor)
            cap_each_sea_level = _blower_capacity_kg_h(equipment, getattr(inp, "diffusion_efficiency_pct", 12.0), 1.0, field_factor)
            total_supply += cap_each * qty
            total_supply_sea_level += cap_each_sea_level * qty
            total_power_kw += equipment["power_kw"] * qty
            total_qty += qty
            detail_rows.append({"tecnologia": "Soprador lobular", "modelo": equipment["model"], "quantidade": qty})

        selected_aeration.update({
            "technology": "Configuração manual",
            "model": "Múltiplos" if len(detail_rows) > 1 else (detail_rows[0]["modelo"] if detail_rows else "-"),
            "quantity_total": total_qty,
            "installed_oxygen_supply_kg_h": total_supply,
            "installed_oxygen_supply_sea_level_kg_h": total_supply_sea_level,
            "power_installed_kw": total_power_kw,
            "details": {"rows": detail_rows},
            "compatibility_warning": "" if total_supply >= oxygen_demand_kg_h else "A soma dos equipamentos manuais não atende a demanda estimada do sistema.",
        })

    altitude_warning = ""
    if altitude_factor <= 0.35:
        altitude_warning = (
            "Altitude extremamente elevada: a pressão atmosférica reduz fortemente a transferência efetiva de oxigênio. "
            "O cenário deve ser tratado como operacionalmente crítico e exige validação técnica específica."
        )
    elif altitude_factor <= 0.70:
        altitude_warning = (
            "Altitude elevada: a transferência efetiva de oxigênio foi reduzida no dimensionamento. "
            "Confirme desempenho real dos equipamentos em campo."
        )

    if altitude_warning:
        selected_aeration["compatibility_warning"] = (
            f"{selected_aeration.get('compatibility_warning', '').strip()} {altitude_warning}"
        ).strip()

    aeration_phase_operation, aeration_modulation_summary = _phase_aeration_modulation(inp, feeding_plan, fish_stocked, selected_aeration)
    aeration_energy_cost_cycle = aeration_modulation_summary["cost_cycle_modulated"]

    fingerling_cost_cycle = fish_stocked * inp.fingerling_price
    feed_cost_cycle = sum(item["feed_phase_cost"] for item in feeding_plan)

    economic_costs = resolve_economic_costs(inp)

    opex_cycle = (
        feed_cost_cycle
        + fingerling_cost_cycle
        + economic_costs["electricity_cost_cycle_effective"]
        + economic_costs["labor_cost_cycle_effective"]
        + economic_costs["other_costs_cycle_effective"]
        + aeration_energy_cost_cycle
    )

    gross_margin_cycle = revenue_cycle - opex_cycle

    biomass_initial = fish_stocked * (inp.initial_weight_g / 1000.0)
    biomass_gain = max(final_biomass_total_kg - biomass_initial, 0.0)
    biomass_gain_planned = sum(item.get("biomass_gain_phase_kg", 0.0) for item in feeding_plan)

    implied_fcr = (
        feed_consumption_cycle_kg / biomass_gain
        if biomass_gain > 0
        else None
    )

    production_per_year_kg = final_biomass_total_kg * cycles_per_year_effective
    feed_consumption_year_kg = feed_consumption_cycle_kg * cycles_per_year_effective
    feed_cost_year = feed_cost_cycle * cycles_per_year_effective
    revenue_year = revenue_cycle * cycles_per_year_effective
    gross_margin_year = gross_margin_cycle * cycles_per_year_effective
    opex_year = opex_cycle * cycles_per_year_effective
    fingerling_cost_year = fingerling_cost_cycle * cycles_per_year_effective
    aeration_energy_cost_year = aeration_energy_cost_cycle * cycles_per_year_effective

    production_schedule = build_production_schedule(
        inp=inp,
        cycle_days=cycle_days,
        production_per_cycle_kg=final_biomass_total_kg,
        production_per_year_kg=production_per_year_kg,
        feed_consumption_cycle_kg=feed_consumption_cycle_kg,
        feed_consumption_year_kg=feed_consumption_year_kg,
        fish_stocked_per_cycle=fish_stocked_per_tank,
        revenue_cycle=revenue_cycle,
        revenue_year=revenue_year,
        fingerling_cost_cycle=fingerling_cost_cycle,
        fingerling_cost_year=fingerling_cost_year,
    )

    base = {
        "scenario": "Base",
        "input": asdict(inp),

        "geometry": geometry,
        "total_volume_m3": total_volume_m3,
        "surface_area_per_unit_m2": geometry["surface_area_m2"],
        "diameter_m": geometry["diameter_m"],
        "water_depth_m": geometry["depth_m"],
        "final_biomass_total_kg": final_biomass_total_kg,
        "final_biomass_per_tank_kg": final_biomass_per_tank_kg,
        "fish_harvested": fish_harvested,
        "fish_harvested_per_tank": fish_harvested_per_tank,
        "fish_stocked": fish_stocked,
        "fish_stocked_per_tank": fish_stocked_per_tank,
        "biomass_gain_kg": biomass_gain,
        "biomass_gain_planned_kg": biomass_gain_planned,

        "production_per_cycle_kg": final_biomass_total_kg,
        "production_per_year_kg": production_per_year_kg,
        "cycles_per_year_effective": cycles_per_year_effective,

        "feed_consumption_kg": feed_consumption_cycle_kg,
        "feed_consumption_cycle_kg": feed_consumption_cycle_kg,
        "feed_consumption_year_kg": feed_consumption_year_kg,
        "feed_cost_cycle": feed_cost_cycle,
        "feed_cost_year": feed_cost_year,
        "implied_fcr": implied_fcr,

        "revenue_cycle": revenue_cycle,
        "revenue_year": revenue_year,
        "gross_margin_cycle": gross_margin_cycle,
        "gross_margin_year": gross_margin_year,
        "opex_cycle": opex_cycle,
        "opex_year": opex_year,
        "economic_model_mode": economic_costs["economic_model_mode"],
        "cost_scaling_mode": economic_costs["cost_scaling_mode"],
        "cost_reference_units": economic_costs["cost_reference_units"],
        "cost_scale_factor": economic_costs["cost_scale_factor"],

        "fingerling_cost_cycle": fingerling_cost_cycle,
        "fingerling_cost_year": fingerling_cost_year,

        "aeration_mode": aeration_mode,
        "selected_aeration_technology": selected_aeration["technology"],
        "selected_aeration_model": selected_aeration["model"],
        "selected_aeration_qty_total": selected_aeration["quantity_total"],
        "selected_aeration_power_kw": selected_aeration["power_installed_kw"],
        "selected_aeration_warning": selected_aeration["compatibility_warning"],
        "aeration_details": selected_aeration["details"],
        "suggested_fountain_details": suggested_fountain,
        "suggested_paddle_details": suggested_paddle,
        "suggested_blower_details": suggested_blower,
        "oxygen_demand_kg_h": oxygen_demand_kg_h,
        "oxygen_demand_per_tank_kg_h": oxygen_demand_per_tank_kg_h,
        "altitude_factor": altitude_factor,
        "altitude_transfer_factor": altitude_factor,
        "altitude_warning": altitude_warning,
        "temp_aeration_factor": temp_aeration_factor,
        "field_factor": field_factor,
        "installed_oxygen_supply_kg_h": selected_aeration["installed_oxygen_supply_kg_h"],
        "installed_oxygen_supply_sea_level_kg_h": selected_aeration.get("installed_oxygen_supply_sea_level_kg_h", selected_aeration["installed_oxygen_supply_kg_h"]),
        "oxygen_offer_demand_ratio": (
            selected_aeration["installed_oxygen_supply_kg_h"] / oxygen_demand_kg_h
            if oxygen_demand_kg_h > 0 else None
        ),
        "required_aerators": selected_aeration["quantity_total"],
        "required_aerators_auto": selected_aeration["quantity_total"] if aeration_mode == "Automático" else 0,
        "aeration_energy_cost_cycle": aeration_energy_cost_cycle,
        "aeration_energy_cost_year": aeration_energy_cost_year,
        "aeration_phase_operation": aeration_phase_operation,
        "peak_installed_power_kw": aeration_modulation_summary["peak_installed_power_kw"],
        "average_active_power_kw": aeration_modulation_summary["average_active_power_kw"],
        "aeration_operation_mode": aeration_modulation_summary["strategy_mode"],
        "aeration_control_strategy": aeration_modulation_summary["control_strategy"],
        "aeration_control_equipment": aeration_modulation_summary["control_equipment_recommended"],
        "aeration_control_note": aeration_modulation_summary["control_note"],
        "aeration_energy_cost_cycle_fixed_power": aeration_modulation_summary["cost_cycle_fixed_power"],
        "aeration_energy_cost_cycle_strategy": aeration_modulation_summary["cost_cycle_modulated"],
        "aeration_savings_cycle_rs": aeration_modulation_summary["savings_cycle_rs"],
        "aeration_savings_cycle_pct": aeration_modulation_summary["savings_cycle_pct"],

        "electricity_cost_cycle_effective": economic_costs["electricity_cost_cycle_effective"],
        "labor_cost_cycle_effective": economic_costs["labor_cost_cycle_effective"],
        "other_costs_cycle_effective": economic_costs["other_costs_cycle_effective"],
        "capex_total_effective": economic_costs["capex_total_effective"],

        "production_schedule": production_schedule,
        "feeding_plan": feeding_plan,
        "growth_curve": growth_curve,
        "cost_curve": cost_curve,
        "growth_segments_used": growth_segments_used,
        "estimated_cycle_days": cycle_days,
        "adjusted_daily_growth_g": adjusted_daily_growth_g(inp),
        "geometry_warning": structure_warning(inp.system_type, geometry["depth_m"]),

        "cost_per_kg": opex_cycle / final_biomass_total_kg if final_biomass_total_kg else 0.0,
        "payback_years": (
            economic_costs["capex_total_effective"] / gross_margin_year
            if gross_margin_year > 0
            else None
        ),
    }

    return {"base": base}
