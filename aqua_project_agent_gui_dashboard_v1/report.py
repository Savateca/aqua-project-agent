from __future__ import annotations
from datetime import datetime
from typing import Any


def brl(value: Any | None) -> str:
    if value is None or value == "":
        return "-"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(value: Any | None, digits: int = 2) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, str):
        return value
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")




def build_profile_sections(results: dict[str, Any], profile: str = "Banco/Financiamento") -> list[dict[str, str]]:
    """Compatibilidade com exporter.py legado.

    Gera uma lista simples de seções a partir do markdown retornado por
    build_professional_project_report. Cada item contém title e content.
    """
    markdown = build_professional_project_report(results, profile)
    sections: list[dict[str, str]] = []
    current_title = "Relatório"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append({"title": current_title, "content": "\n".join(current_lines).strip()})
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"title": current_title, "content": "\n".join(current_lines).strip()})

    return sections

def build_professional_project_report(
    results: dict[str, Any],
    profile: str = "Banco/Financiamento",
) -> str:
    base = results["base"]
    inp = base["input"]
    now = datetime.now().strftime("%d/%m/%Y")
    schedule = base.get("production_schedule", {})

    feed_rows = []
    for row in base.get("feeding_plan", []):
        pellet_text = row.get("pellet_recommendation", row.get("pellet_mm"))
        feed_rows.append(
            f"| {row.get('phase_name','-')} | {row.get('weight_range','-')} | "
            f"{num(row.get('days_in_phase'),0)} | {num(row.get('protein_percent'),1)} | "
            f"{num(pellet_text,1)} | {brl(row.get('feed_price_per_kg'))} | "
            f"{num(row.get('phase_fcr'),2)} | {num(row.get('biomass_gain_phase_kg'))} | "
            f"{num(row.get('feed_phase_kg'))} | {brl(row.get('feed_phase_cost'))} |"
        )
    table_feed = "\n".join(feed_rows) if feed_rows else "| - | - | - | - | - | - | - | - | - | - |"

    aer_rows = []
    for row in base.get("aeration_phase_operation", []):
        aer_rows.append(
            f"| {row.get('Fase','-')} | {num(row.get('Biomassa média da fase (kg)'))} | "
            f"{num(row.get('Demanda de O₂ da fase (kg/h)'),3)} | {num(row.get('% de uso da capacidade'),1)}% | "
            f"{num(row.get('Equipamentos ativos'),0)} | {num(row.get('Potência ativa da fase (kW)'),2)} | "
            f"{num(row.get('Dias da fase'),0)} | {brl(row.get('Custo da fase (R$)'))} |"
        )
    table_aer = "\n".join(aer_rows) if aer_rows else "| - | - | - | - | - | - | - | - |"

    strategy = schedule.get("production_strategy", inp.get("production_strategy", "Ciclos simultâneos"))
    if strategy == "Escalonada":
        schedule_text = f"""## 3. Estratégia de produção e escalonamento

- **Modo operacional:** {strategy}
- **Critério de escalonamento:** {schedule.get('scheduling_basis', '-')}
- **Ciclo biológico do lote:** {num(base.get('estimated_cycle_days'),0)} dias ({num(schedule.get('biological_cycle_months'),1)} meses)
- **Período de rampa até a 1ª receita:** {num(schedule.get('warmup_months_without_revenue'),1)} meses
- **Primeira despesca / primeira receita após:** {num(schedule.get('first_harvest_after_months'),1)} meses
- **Intervalo entre despescas em regime:** {num(schedule.get('harvest_interval_months'),2)} mês(es)
- **Despescas no 1º ano (com rampa):** {num(schedule.get('harvests_year1'),0)}
- **Despescas por ano em regime estabilizado:** {num(schedule.get('harvests_per_year'),2)}
- **Lotes em paralelo:** {num(schedule.get('batches_in_parallel'),0)}
- **Tanques por lote:** {num(schedule.get('units_per_batch_exact'),2)}
- **Produção por despesca em regime:** {num(schedule.get('production_per_harvest_kg'))} kg
- **Ração por despesca em regime:** {num(schedule.get('feed_per_harvest_kg'))} kg
- **Receita por despesca em regime:** {brl(schedule.get('revenue_per_harvest'))}
- **Produção no 1º ano (com rampa):** {num(schedule.get('production_year1_kg'))} kg
- **Receita no 1º ano (com rampa):** {brl(schedule.get('revenue_year1'))}
- **Distribuição sugerida dos tanques:** {schedule.get('batch_distribution_note', '-')}
"""
    else:
        schedule_text = f"""## 3. Estratégia de produção e escalonamento

- **Modo operacional:** {strategy}
- **Ciclo biológico do lote:** {num(base.get('estimated_cycle_days'),0)} dias ({num(schedule.get('biological_cycle_months'),1)} meses)
- **Todos os tanques operam em conjunto por ciclo.**
- **Colheitas por ano em regime:** {num(schedule.get('harvests_per_year'),2)}
- **Produção por colheita:** {num(schedule.get('production_per_harvest_kg'))} kg
"""

    geometry = base.get("geometry", {})
    shape_lines = []
    if geometry.get("diameter_m", 0):
        shape_lines.append(f"- **Diâmetro interno estimado:** {num(geometry.get('diameter_m'))} m")
    else:
        shape_lines.append(f"- **Comprimento interno:** {num(geometry.get('length_m'))} m")
        shape_lines.append(f"- **Largura interna:** {num(geometry.get('width_m'))} m")
    shape_lines.append(f"- **Altura da água:** {num(geometry.get('depth_m'))} m")
    shape_lines.append(f"- **Área superficial por unidade:** {num(geometry.get('surface_area_m2'))} m²")
    if base.get("geometry_warning"):
        shape_lines.append(f"- **Alerta geométrico:** {base.get('geometry_warning')}")

    return f"""# PROJETO TÉCNICO-ECONÔMICO DE PISCICULTURA

## 1. Identificação do projeto

- **Nome:** {inp.get('project_name', '-')}
- **Autor:** {inp.get('author_name', '-')}
- **Espécie:** {inp.get('species', '-')}
- **Sistema:** {inp.get('system_type', '-')}
- **Região:** {inp.get('region_focus', '-')}
- **Perfil do relatório:** {profile}
- **Data:** {now}

## 2. Resumo executivo

- **Ciclo biológico do lote:** {num(base.get('estimated_cycle_days'),0)} dias ({num(schedule.get('biological_cycle_months'),1)} meses)
- **Período de rampa até a 1ª receita:** {num(schedule.get('warmup_months_without_revenue'),1)} meses
- **Produção por ciclo biológico:** {num(base.get('production_per_cycle_kg'))} kg
- **Produção por despesca em regime:** {num(schedule.get('production_per_harvest_kg'))} kg
- **Produção no 1º ano (com rampa):** {num(schedule.get('production_year1_kg'))} kg
- **Produção anual em regime estabilizado:** {num(base.get('production_per_year_kg'))} kg
- **Receita por ciclo biológico:** {brl(base.get('revenue_cycle'))}
- **Receita no 1º ano (com rampa):** {brl(schedule.get('revenue_year1'))}
- **Receita anual em regime estabilizado:** {brl(base.get('revenue_year'))}
- **OPEX por ciclo biológico:** {brl(base.get('opex_cycle'))}
- **Margem por ciclo biológico:** {brl(base.get('gross_margin_cycle'))}
- **Margem anual em regime estabilizado:** {brl(base.get('gross_margin_year'))}
- **Custo por kg:** {brl(base.get('cost_per_kg'))}/kg
- **Payback estimado:** {num(base.get('payback_years'),2)} anos

{schedule_text}

## 4. Dimensionamento do sistema

- **Volume total do sistema:** {num(base.get('total_volume_m3'))} m³
- **Volume útil por unidade:** {num(geometry.get('unit_volume_m3'))} m³
- **Biomassa final total:** {num(base.get('final_biomass_total_kg'))} kg
- **Biomassa final por tanque:** {num(base.get('final_biomass_per_tank_kg'))} kg
- **Peixes colhidos:** {num(base.get('fish_harvested'))}
- **Peixes estocados:** {num(base.get('fish_stocked'))}
- **Ganho diário ajustado da curva biológica:** {num(base.get('adjusted_daily_growth_g'))} g/peixe/dia
{"\n".join(shape_lines)}

## 5. Oxigênio e aeração

- **Demanda de oxigênio do sistema:** {num(base.get('oxygen_demand_kg_h'))} kg O₂/h
- **Demanda de oxigênio por tanque:** {num(base.get('oxygen_demand_per_tank_kg_h'))} kg O₂/h
- **Tecnologia adotada:** {base.get('selected_aeration_technology', '-')}
- **Modelo adotado:** {base.get('selected_aeration_model', '-')}
- **Equipamentos instalados:** {num(base.get('required_aerators'),0)}
- **Oferta instalada de oxigênio:** {num(base.get('installed_oxygen_supply_kg_h'))} kg O₂/h
- **Potência instalada total:** {num(base.get('peak_installed_power_kw'))} kW
- **Potência média utilizada no ciclo:** {num(base.get('average_active_power_kw'))} kW
- **Modo de operação da aeração:** {base.get('aeration_operation_mode', '-')}
- **Estratégia de controle sugerida:** {base.get('aeration_control_strategy', '-')}
- **Equipamento de controle recomendado:** {base.get('aeration_control_equipment', '-')}
- **Observação técnica:** {base.get('aeration_control_note', '-')}
- **Custo de aeração no ciclo (potência fixa):** {brl(base.get('aeration_energy_cost_cycle_fixed_power'))}
- **Custo de aeração no ciclo (estratégia adotada):** {brl(base.get('aeration_energy_cost_cycle'))}
- **Economia estimada no ciclo:** {brl(base.get('aeration_savings_cycle_rs'))} ({num(base.get('aeration_savings_cycle_pct'),1)}%)
- **Uso estimado do modelo na fase crítica:** {num(base.get('selected_aeration_peak_use_pct'),1)}%
- **Relação oferta/demanda na fase crítica:** {num(base.get('selected_aeration_excess_ratio'),2)}x
- **Compatibilidade geométrica / operacional:** {base.get('selected_aeration_warning', 'Sem restrição crítica sinalizada')}

### 5.1 Operação da aeração por fase

| Fase | Biomassa média (kg) | Demanda O₂ (kg/h) | Modulação sugerida | Equipamentos operando | Potência média ativa (kW) | Dias | Custo da fase |
|---|---:|---:|---:|---:|---:|---:|---:|
{table_aer}

## 6. Plano alimentar por fase

| Fase | Faixa de peso | Dias | PB (%) | Pellet recomendado | Preço/kg | FCR | Ganho biomassa (kg) | Ração fase (kg) | Custo fase |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
{table_feed}

## 7. Custos e indicadores econômicos

- **Custo de ração por ciclo:** {brl(base.get('feed_cost_cycle'))}
- **Custo de ração anual em regime:** {brl(base.get('feed_cost_year'))}
- **Custo de alevinos por ciclo:** {brl(base.get('fingerling_cost_cycle'))}
- **Custo de alevinos anual em regime:** {brl(base.get('fingerling_cost_year'))}
- **Custo de aeração anual em regime:** {brl(base.get('aeration_energy_cost_year'))}
- **OPEX anual em regime:** {brl(base.get('opex_year'))}
- **FCR implícito do ciclo:** {num(base.get('implied_fcr'))}

## 8. Interpretação técnica

O projeto foi calculado com base nos parâmetros produtivos, nutricionais, energéticos, geométricos e econômicos informados no sistema. O desempenho esperado depende diretamente da qualidade do manejo, da biometria periódica, do monitoramento da água e da aderência entre densidade de estocagem, granulometria da ração e infraestrutura de aeração. No caso de chafariz e pás, o sistema considera operação contínua de um equipamento por tanque com modulação de potência, e não desligamento seletivo de tanques.

## 9. Recomendações

- Conferir biometria e ajustar o manejo alimentar em cada fase
- Validar a coerência entre FCR projetado e desempenho real
- Monitorar oxigênio dissolvido, principalmente nos horários críticos
- Revisar custo da ração e custo energético periodicamente
- Confirmar compatibilidade geométrica do chafariz antes da compra definitiva do equipamento

## 10. Observações finais

{inp.get('notes', 'Nenhuma observação adicional informada.')}
"""
