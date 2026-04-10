from __future__ import annotations
from datetime import datetime
from typing import Any


def brl(value: float | None) -> str:
    if value is None:
        return "-"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")




def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def build_profile_sections(results: dict[str, Any], profile: str = "Produtor") -> dict[str, list[str] | str]:
    base = results["base"]
    sale_price = float(base.get("input", {}).get("sale_price_per_kg", 0.0) or 0.0)
    cost_per_kg = float(base.get("cost_per_kg", 0.0) or 0.0)
    gross_margin_cycle = float(base.get("gross_margin_cycle", 0.0) or 0.0)
    revenue_cycle = float(base.get("revenue_cycle", 0.0) or 0.0)
    implied_fcr = base.get("implied_fcr")
    oxygen_demand = float(base.get("oxygen_demand_kg_h", 0.0) or 0.0)
    oxygen_supply = float(base.get("installed_oxygen_supply_kg_h", 0.0) or 0.0)
    cycle_days = float(base.get("estimated_cycle_days", 0.0) or 0.0)
    feed_cost_cycle = float(base.get("feed_cost_cycle", 0.0) or 0.0)
    opex_cycle = float(base.get("opex_cycle", 0.0) or 0.0)
    payback = base.get("payback_years")
    schedule = base.get("production_schedule", {})
    margin_pct = safe_ratio(gross_margin_cycle, revenue_cycle)
    feed_share = safe_ratio(feed_cost_cycle, opex_cycle)
    oxygen_safety = safe_ratio(oxygen_supply, oxygen_demand)

    if profile == "Produtor":
        title = "Leitura gerencial para o produtor"
        highlights = [
            f"A margem operacional estimada por ciclo é de {brl(gross_margin_cycle)}.",
            f"O custo por kg projetado é {brl(cost_per_kg)}/kg, frente a um preço de venda de {brl(sale_price)}/kg.",
            f"A ração representa aproximadamente {num((feed_share or 0) * 100, 1)}% do OPEX do ciclo.",
        ]
        recommendations = [
            "Trabalhar com biometria periódica e ajuste fino do arraçoamento para evitar sobras e derrubar custo por kg.",
            "Programar a compra de ração e alevinos antes do início do ciclo para reduzir pressão de caixa durante a fase de maior consumo.",
            "Acompanhar mortalidade, conversão alimentar e velocidade de crescimento como três indicadores operacionais semanais.",
        ]
        if schedule.get("production_strategy") == "Escalonada":
            recommendations.append("Usar o escalonamento para organizar fluxo de caixa e vendas mensais, evitando concentração de receita em poucas despescas.")
        if implied_fcr is not None and implied_fcr > 1.7:
            recommendations.append("O FCR implícito está elevado; convém revisar manejo alimentar, qualidade de ração e frequência de biometria.")
        if oxygen_safety is not None and oxygen_safety < 1.10:
            recommendations.append("A folga de aeração está curta para operação segura; convém rever número de aeradores ou manejo de biomassa.")
        if cycle_days > 210:
            recommendations.append("O ciclo projetado está longo; planejar capital de giro suficiente até a despesca para não estrangular a operação.")
        decisions = [
            "Decidir antecipadamente estratégia de compra de insumos, calendário de povoamento e janela de comercialização.",
            "Validar se o preço de venda local sustenta o custo por kg projetado com margem comercial desejada.",
        ]
    elif profile == "Técnico":
        title = "Leitura operacional para o responsável técnico"
        highlights = [
            f"O ciclo estimado está em {num(cycle_days, 0)} dias, com ganho diário ajustado de {num(base.get('adjusted_daily_growth_g'))} g/dia.",
            f"A demanda de oxigênio foi estimada em {num(oxygen_demand)} kg O₂/h, com oferta instalada de {num(oxygen_supply)} kg O₂/h.",
            f"O FCR implícito projetado é {num(implied_fcr) if implied_fcr is not None else '-'} e deve ser validado em campo com biometria e sobra de ração.",
        ]
        recommendations = [
            "Estabelecer rotina formal de biometria, ajuste de arraçoamento e conferência do consumo real por fase.",
            "Monitorar oxigênio dissolvido, temperatura e comportamento alimentar em horários críticos, principalmente madrugada e manhã cedo.",
            "Usar o plano alimentar do sistema como base, mas recalibrar proteína, pellet e frequência conforme resposta zootécnica observada.",
            "Formalizar pontos de intervenção para mortalidade acima do esperado, queda de consumo e atraso de crescimento.",
        ]
        if oxygen_safety is not None and oxygen_safety < 1.10:
            recommendations.append("O índice de segurança de aeração está baixo; tecnicamente convém ampliar capacidade instalada ou reduzir biomassa crítica.")
        if implied_fcr is not None and implied_fcr > 1.6:
            recommendations.append("Conversão alimentar projetada em faixa de atenção; revisar densidade, qualidade de água e consistência do manejo.")
        decisions = [
            "Definir protocolo mínimo de qualidade de água, frequência de análises e critérios de correção operacional.",
            "Amarrar o cronograma de manejo ao cronograma de crescimento para evitar desvios silenciosos do projeto.",
        ]
    else:
        title = "Leitura orientada para financiamento e investimento"
        highlights = [
            f"O projeto projeta receita anual de {brl(base.get('revenue_year'))} e margem anual de {brl(base.get('gross_margin_year'))}.",
            f"O CAPEX considerado foi de {brl(base.get('capex_total_effective'))}, com payback estimado em {num(payback, 2)} anos.",
            f"O custo por kg estimado é {brl(cost_per_kg)}/kg, frente a um preço de venda de {brl(sale_price)}/kg.",
        ]
        recommendations = [
            "Apresentar o projeto com premissas claramente documentadas para preço de venda, custo de ração, custo energético e sobrevivência.",
            "Anexar memória de cálculo, cronograma operacional e plano de mitigação para oscilações de preço e desempenho zootécnico.",
            "Demonstrar que a estrutura de aeração e a estratégia de manejo são compatíveis com a biomassa final proposta.",
            "Separar custos fixos, variáveis e necessidade de capital de giro para leitura financeira mais robusta.",
        ]
        if payback is not None and payback > 5:
            recommendations.append("O payback está alongado; para financiamento, convém revisar premissas, escala produtiva ou estrutura de CAPEX.")
        if margin_pct is not None and margin_pct < 0.20:
            recommendations.append("A margem operacional projetada está estreita para uma tese de crédito confortável; convém construir cenário conservador adicional.")
        decisions = [
            "Apresentar cenário base, conservador e otimista para reforçar a consistência econômica do investimento.",
            "Demonstrar governança operacional mínima: responsável técnico, rotina de monitoramento, fornecedores e canais de comercialização.",
        ]

    return {
        "title": title,
        "highlights": highlights,
        "recommendations": recommendations,
        "decisions": decisions,
    }

def build_professional_project_report(
    results: dict[str, Any],
    profile: str = "Banco/Financiamento",
) -> str:
    base = results["base"]
    inp = base["input"]
    now = datetime.now().strftime("%d/%m/%Y")

    feed_rows = []
    for row in base.get("feeding_plan", []):
        feed_rows.append(
            f"| {row.get('phase_name','-')} | {row.get('weight_range','-')} | "
            f"{num(row.get('days_in_phase'),0)} | {num(row.get('protein_percent'),1)} | "
            f"{num(row.get('pellet_mm'),1)} | {brl(row.get('feed_price_per_kg'))} | "
            f"{num(row.get('phase_fcr'),2)} | {num(row.get('biomass_gain_phase_kg'))} | "
            f"{num(row.get('feed_phase_kg'))} | {brl(row.get('feed_phase_cost'))} |"
        )

    table_feed = "\n".join(feed_rows) if feed_rows else "| - | - | - | - | - | - | - | - | - | - |"
    schedule = base.get("production_schedule", {})
    profile_sections = build_profile_sections(results, profile)
    strategy = schedule.get("production_strategy", inp.get("production_strategy", "Ciclos simultâneos"))
    if strategy == "Escalonada":
        schedule_text = f"""## 3. Estratégia de produção e escalonamento\n\n- **Modo operacional:** {strategy}\n- **Intervalo entre despescas:** {num(schedule.get('harvest_interval_months'),2)} mês(es)\n- **Modo de definição dos lotes:** {schedule.get('production_batch_mode', '-')}\n- **Despescas por ano:** {num(schedule.get('harvests_per_year'),2)}\n- **Lotes em paralelo:** {num(schedule.get('batches_in_parallel'),0)}\n- **Lotes automáticos estimados:** {num(schedule.get('automatic_parallel_batches'),0)}\n- **Tanques por lote:** {num(schedule.get('units_per_batch_exact'),2)}\n- **Produção por despesca:** {num(schedule.get('production_per_harvest_kg'))} kg\n- **Ração por despesca:** {num(schedule.get('feed_per_harvest_kg'))} kg\n- **Receita por despesca:** {brl(schedule.get('revenue_per_harvest'))}\n- **Alevinos por despesca:** {num(schedule.get('fish_stocked_per_harvest'),0)}\n- **Distribuição sugerida dos tanques:** {schedule.get('batch_distribution_note', '-')}\n- **Primeira despesca após o início:** {num(schedule.get('first_harvest_after_months'),1)} meses\n"""
    else:
        schedule_text = f"""## 3. Estratégia de produção e escalonamento\n\n- **Modo operacional:** {strategy}\n- **Todos os tanques operam em conjunto por ciclo.**\n- **Colheitas por ano:** {num(schedule.get('harvests_per_year'),2)}\n- **Produção por colheita:** {num(schedule.get('production_per_harvest_kg'))} kg\n"""

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

- **Produção por ciclo:** {num(base.get('production_per_cycle_kg'))} kg
- **Produção anual:** {num(base.get('production_per_year_kg'))} kg
- **Ração por ciclo:** {num(base.get('feed_consumption_cycle_kg'))} kg
- **Ração anual:** {num(base.get('feed_consumption_year_kg'))} kg
- **Receita por ciclo:** {brl(base.get('revenue_cycle'))}
- **Receita anual:** {brl(base.get('revenue_year'))}
- **OPEX por ciclo:** {brl(base.get('opex_cycle'))}
- **Margem por ciclo:** {brl(base.get('gross_margin_cycle'))}
- **Margem anual:** {brl(base.get('gross_margin_year'))}
- **Custo por kg:** {brl(base.get('cost_per_kg'))}/kg
- **Payback estimado:** {num(base.get('payback_years'),2)} anos
- **CAPEX considerado no cálculo:** {brl(base.get('capex_total_effective', inp.get('capex_total')))}
- **Modelo econômico:** {base.get('economic_model_mode', 'Simplificado')}
- **CAPEX fixo considerado:** {brl(base.get('capex_fixed_total_effective'))}
- **CAPEX variável considerado:** {brl(base.get('capex_variable_total_effective'))}

{schedule_text}

## 4. Leitura específica para o perfil

- **Perfil selecionado:** {profile}
- **Enfoque do relatório:** {profile_sections.get('title', '-')}
{chr(10).join(f"- {item}" for item in profile_sections.get("highlights", []))}

## 5. Recomendações específicas para o perfil

{chr(10).join(f"- {item}" for item in profile_sections.get("recommendations", []))}

## 6. Pontos de decisão e próximos passos

{chr(10).join(f"- {item}" for item in profile_sections.get("decisions", []))}

## 7. Dimensionamento do sistema

- **Volume total:** {num(base.get('total_volume_m3'))} m³
- **Biomassa final:** {num(base.get('final_biomass_total_kg'))} kg
- **Peixes colhidos:** {num(base.get('fish_harvested'))}
- **Peixes estocados (teórico):** {num(base.get('fish_stocked_theoretical', base.get('fish_stocked')))}
- **Alevinos para compra/ciclo:** {num(base.get('fingerlings_purchase_cycle'),0)}
- **Dias do ciclo:** {num(base.get('estimated_cycle_days'),0)}
- **Ganho diário ajustado:** {num(base.get('adjusted_daily_growth_g'))} g/dia

## 8. Oxigênio e aeração

- **Demanda de oxigênio:** {num(base.get('oxygen_demand_kg_h'))} kg O₂/h
- **Aeradores instalados:** {num(base.get('required_aerators'),0)}
- **Aeradores mínimos automáticos:** {num(base.get('auto_required_aerators'),0)}
- **Modo de definição:** {base.get('aerator_quantity_mode', '-')}
- **Oferta instalada de oxigênio:** {num(base.get('installed_oxygen_supply_kg_h'))} kg O₂/h
- **Custo de aeração por ciclo:** {brl(base.get('aeration_energy_cost_cycle'))}

## 9. Plano alimentar por fase

| Fase | Faixa de peso | Dias | PB (%) | Pellet (mm) | Preço/kg | FCR | Ganho biomassa (kg) | Ração fase (kg) | Custo fase |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
{table_feed}

## 10. Custos e indicadores econômicos

- **Custo de ração por ciclo:** {brl(base.get('feed_cost_cycle'))}
- **Custo de ração anual:** {brl(base.get('feed_cost_year'))}
- **Alevinos para compra/ano:** {num(base.get('fingerlings_purchase_year'),0)}
- **Custo de alevinos por ciclo:** {brl(base.get('fingerling_cost_cycle'))}
- **Custo de alevinos anual:** {brl(base.get('fingerling_cost_year'))}
- **Energia adicional anual considerada:** {brl(base.get('electricity_cost_year'))}
- **Mão de obra anual considerada:** {brl(base.get('labor_cost_year'))}
- **Outros custos anuais considerados:** {brl(base.get('other_costs_year'))}
- **Custo de aeração anual:** {brl(base.get('aeration_energy_cost_year'))}
- **OPEX anual:** {brl(base.get('opex_year'))}
- **FCR implícito do ciclo:** {num(base.get('implied_fcr'))}
- **Energia fixa/ciclo considerada:** {brl(base.get('electricity_cost_fixed_cycle_effective'))}
- **Energia variável/ciclo considerada:** {brl(base.get('electricity_cost_variable_cycle_effective'))}
- **Mão de obra fixa/ciclo considerada:** {brl(base.get('labor_cost_fixed_cycle_effective'))}
- **Mão de obra variável/ciclo considerada:** {brl(base.get('labor_cost_variable_cycle_effective'))}
- **Outros custos fixos/ciclo considerados:** {brl(base.get('other_cost_fixed_cycle_effective'))}
- **Outros custos variáveis/ciclo considerados:** {brl(base.get('other_cost_variable_cycle_effective'))}
- **CAPEX fixo considerado:** {brl(base.get('capex_fixed_total_effective'))}
- **CAPEX variável considerado:** {brl(base.get('capex_variable_total_effective'))}

## 11. Interpretação técnica

O projeto foi calculado com base nos parâmetros produtivos, nutricionais, energéticos e econômicos informados no sistema. O desempenho esperado depende diretamente da qualidade do manejo, da biometria periódica, do monitoramento da água e da aderência entre densidade de estocagem e infraestrutura de aeração.

## 12. Recomendações gerais

- Conferir biometria e ajustar o manejo alimentar em cada fase
- Validar a coerência entre FCR projetado e desempenho real
- Monitorar oxigênio dissolvido, principalmente nos horários críticos
- Revisar custo da ração e custo energético periodicamente
- Reavaliar o número de aeradores conforme a estratégia operacional

## 13. Observações finais

{inp.get('notes', 'Nenhuma observação adicional informada.')}
"""