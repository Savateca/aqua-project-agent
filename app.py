from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aqua_project_agent_gui_dashboard_v1.calculator import (
    DEFAULT_FEEDING_CURVE,
    calculate_dashboard_project,
)
from aqua_project_agent_gui_dashboard_v1.exporter import (
    export_dashboard_report_to_docx,
    export_docx_to_pdf,
    export_markdown_to_docx,
)
from aqua_project_agent_gui_dashboard_v1.models import DashboardProjectInput
from aqua_project_agent_gui_dashboard_v1.report import (
    build_professional_project_report,
    brl,
    num,
)

from core_engine.service import run_project_calculation
from auth.supabase_auth import is_supabase_configured, sign_in_with_password
from data_access.local_store import (
    build_project_payload,
    delete_project,
    duplicate_project,
    list_projects,
    load_project,
    save_project,
)
from data_access.supabase_store import (
    delete_project_remote,
    duplicate_project_remote,
    list_projects_remote,
    load_project_remote,
    save_project_remote,
)

st.set_page_config(
    page_title="Aqua Project Agent Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(180deg, #eef7f5 0%, #dcefeb 100%);
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

h1, h2, h3 {
    color: #0f4c5c;
    font-weight: 700;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f4c5c 0%, #1b6b7a 100%);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color: #111827 !important;
    background-color: white !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    color: #111827 !important;
    background-color: white !important;
}

[data-testid="stSidebar"] button {
    color: #ffffff !important;
    background: linear-gradient(180deg, #1f4f5a 0%, #163f48 100%) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] button:hover {
    color: #ffffff !important;
    background: linear-gradient(180deg, #2b6875 0%, #1f5661 100%) !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
}

[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
    color: #ffffff !important;
}

.kpi-card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    border-left: 6px solid #2a9d8f;
    margin-bottom: 12px;
}

.stButton button[kind="primary"] {
    color: #ffffff !important;
    background: linear-gradient(180deg, #c62828 0%, #8e1e1e 100%) !important;
    border: 1px solid #7f1d1d !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.stButton button[kind="primary"]:hover {
    color: #ffffff !important;
    background: linear-gradient(180deg, #d32f2f 0%, #a12626 100%) !important;
    border: 1px solid #991b1b !important;
}

.kpi-title {
    font-size: 14px;
    color: #4f6d7a;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #0f4c5c;
}

.kpi-caption {
    font-size: 12px;
    color: #5b6b73;
    margin-top: 8px;
}

.section-box {
    background: white;
    border: 1px solid #d9e7e3;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}

.hero-box {
    background: linear-gradient(135deg, rgba(15,76,92,0.96), rgba(42,157,143,0.92));
    color: white;
    border-radius: 22px;
    padding: 28px 30px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    margin-bottom: 18px;
}

.hero-title {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 6px;
}

.hero-subtitle {
    font-size: 18px;
    opacity: 0.95;
    margin-bottom: 0;
}
</style>
""",
    unsafe_allow_html=True,
)

sample_data = {
    "project_name": "Projeto dashboard de tilapicultura",
    "author_name": "Luiz Henrique Sousa Salgado",
    "region_focus": "Brasil, com ênfase no Sudeste",
    "system_type": "tanque circular de geomembrana",
    "species": "tilápia",
    "number_of_units": 12,
    "unit_volume_m3": 100.0,
    "density_kg_m3": 25.0,
    "survival_rate": 0.90,
    "cycles_per_year": 2.0,
    "production_strategy": "Ciclos simultâneos",
    "production_batch_mode": "Automático",
    "manual_parallel_batches": 6,
    "harvest_interval_months": 1.0,
    "sale_price_per_kg": 10.0,
    "fingerling_price": 0.30,
    "fingerling_weight_kg": 1.0,
    "fingerling_rounding_mode": "Arredondar para cima",
    "fingerling_rounding_base": 1000,
    "electricity_cost_cycle": 12000.0,
    "labor_cost_cycle": 18000.0,
    "other_costs_cycle": 15000.0,
    "capex_total": 450000.0,
    "cost_scaling_mode": "Fixos (não escalar)",
    "cost_reference_units": 12,
    "economic_model_mode": "Simplificado",
    "electricity_cost_fixed_cycle": 0.0,
    "electricity_cost_per_unit_cycle": 1000.0,
    "labor_cost_fixed_cycle": 0.0,
    "labor_cost_per_unit_cycle": 1500.0,
    "other_cost_fixed_cycle": 0.0,
    "other_cost_per_unit_cycle": 1250.0,
    "capex_fixed_total": 0.0,
    "capex_per_unit": 37500.0,
    "initial_weight_g": 1.0,
    "target_weight_g": 1000.0,
    "water_temperature_c": 28.0,
    "base_daily_growth_g": 4.5,
    "oxygen_demand_mg_per_kg_h": 250.0,
    "aerator_hp_each": 0.75,
    "oxygen_transfer_kg_o2_hp_h": 1.38,
    "aeration_hours_per_day": 24.0,
    "electricity_price_kwh": 0.45,
    "aerator_quantity_mode": "Manual",
    "manual_aerators": 12,
    "phase1_fcr": 1.20,
    "phase2_fcr": 1.35,
    "phase3_fcr": 1.50,
    "phase4_fcr": 1.70,
    "report_profile": "Produtor",
    "notes": "Versão com dashboard visual e relatório profissional.",
}

for i, row in enumerate(DEFAULT_FEEDING_CURVE, start=1):
    sample_data[f"phase{i}_min_g"] = row["min_g"]
    sample_data[f"phase{i}_max_g"] = row["max_g"]
    sample_data[f"phase{i}_feeding_rate_percent"] = row["feeding_rate_percent"]
    sample_data[f"phase{i}_meals_per_day"] = row["meals_per_day"]
    sample_data[f"phase{i}_protein_percent"] = row["protein_percent"]
    sample_data[f"phase{i}_pellet_mm"] = row["pellet_mm"]
    sample_data[f"phase{i}_feed_price_per_kg"] = row["feed_price_per_kg"]

if "dash_form_data" not in st.session_state:
    st.session_state.dash_form_data = sample_data.copy()

if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None

if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None

if "latest_results" not in st.session_state:
    st.session_state.latest_results = None

if "storage_mode" not in st.session_state:
    st.session_state.storage_mode = "Local"

if "auth_user_id" not in st.session_state:
    st.session_state.auth_user_id = None

if "auth_user_email" not in st.session_state:
    st.session_state.auth_user_email = None

def _use_supabase_storage() -> bool:
    return (
        st.session_state.get("storage_mode") == "Supabase beta"
        and bool(st.session_state.get("auth_user_id"))
    )


def _list_projects_active() -> list[dict]:
    if _use_supabase_storage():
        return list_projects_remote(st.session_state["auth_user_id"])
    return list_projects()


def _load_project_active(project_id: str) -> dict:
    if _use_supabase_storage():
        return load_project_remote(project_id, st.session_state["auth_user_id"])
    return load_project(project_id)


def _save_project_active(payload: dict, current_project_id: str | None = None) -> str:
    if _use_supabase_storage():
        return save_project_remote(payload, st.session_state["auth_user_id"], current_project_id=current_project_id)
    return save_project(payload)


def _delete_project_active(project_id: str) -> None:
    if _use_supabase_storage():
        delete_project_remote(project_id, st.session_state["auth_user_id"])
    else:
        delete_project(project_id)


def _duplicate_project_active(project_id: str) -> str:
    if _use_supabase_storage():
        return duplicate_project_remote(project_id, st.session_state["auth_user_id"])
    return duplicate_project(project_id)


with st.sidebar:
    st.markdown("## Aqua Project Agent")
    st.markdown("Planejamento técnico-econômico aquícola")
    st.markdown("---")

    output_dir = st.text_input("Pasta de saída", "outputs")
    output_name = st.text_input("Nome base dos arquivos", "projeto_tilapia_dashboard")

    if st.button("Carregar exemplo"):
        st.session_state.dash_form_data = sample_data.copy()
        st.session_state.current_project_id = None
        st.session_state.selected_project_id = None
        st.session_state.latest_results = None
        st.rerun()

    st.markdown("---")
    st.markdown("### Persistência")

    if is_supabase_configured():
        st.session_state.storage_mode = st.radio(
            "Modo de armazenamento",
            ["Local", "Supabase beta"],
            index=0 if st.session_state.get("storage_mode", "Local") == "Local" else 1,
        )
    else:
        st.session_state.storage_mode = "Local"
        st.info("Supabase ainda não configurado no .env. Usando modo local.")

    if st.session_state.storage_mode == "Supabase beta":
        st.markdown("#### Login beta")
        email_login = st.text_input("Email do testador", key="sb_email_login")
        password_login = st.text_input("Senha", type="password", key="sb_password_login")
        c_auth1, c_auth2 = st.columns(2)

        with c_auth1:
            if st.button("Entrar"):
                try:
                    auth_data = sign_in_with_password(email_login, password_login)
                    st.session_state.auth_user_id = auth_data.get("user_id")
                    st.session_state.auth_user_email = auth_data.get("email")
                    st.success(f"Login realizado: {st.session_state.auth_user_email}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Falha no login: {exc}")

        with c_auth2:
            if st.button("Sair"):
                st.session_state.auth_user_id = None
                st.session_state.auth_user_email = None
                st.session_state.current_project_id = None
                st.session_state.selected_project_id = None
                st.rerun()

        if st.session_state.get("auth_user_email"):
            st.caption(f"Usuário conectado: {st.session_state['auth_user_email']}")
        else:
            st.warning("Faça login para usar o armazenamento remoto.")

    st.markdown("---")
    st.markdown("### Projetos")

    projects = _list_projects_active()
    project_options = [""] + [p["project_id"] for p in projects]
    project_labels = {
        "": "Selecione um projeto salvo",
        **{
            p["project_id"]: f"{p['project_name']} ({str(p.get('updated_at', ''))[:19].replace('T', ' ')})"
            for p in projects
        },
    }

    if st.session_state.selected_project_id not in project_options:
        st.session_state.selected_project_id = None

    selected = st.selectbox(
        "Projetos salvos",
        project_options,
        format_func=lambda x: project_labels.get(x, x),
        index=project_options.index(st.session_state.selected_project_id)
        if st.session_state.selected_project_id in project_options
        else 0,
    )

    st.session_state.selected_project_id = selected if selected else None

    cproj1, cproj2 = st.columns(2)

    with cproj1:
        if st.button("Abrir projeto"):
            if st.session_state.selected_project_id:
                saved = _load_project_active(st.session_state.selected_project_id)
                st.session_state.dash_form_data = saved.get("inputs", sample_data.copy())
                st.session_state.current_project_id = saved.get("project_meta", {}).get("project_id")
                st.session_state.latest_results = saved.get("results")
                st.success("Projeto carregado com sucesso.")
                st.rerun()

    with cproj2:
        if st.button("Novo projeto"):
            st.session_state.dash_form_data = sample_data.copy()
            st.session_state.current_project_id = None
            st.session_state.selected_project_id = None
            st.session_state.latest_results = None
            st.success("Novo projeto iniciado.")
            st.rerun()

    cproj3, cproj4 = st.columns(2)

    with cproj3:
        if st.button("Duplicar projeto"):
            if st.session_state.selected_project_id:
                new_id = _duplicate_project_active(st.session_state.selected_project_id)
                st.session_state.selected_project_id = new_id
                st.session_state.current_project_id = new_id
                st.success(f"Projeto duplicado: {new_id}")
                st.rerun()

    with cproj4:
        if st.button("Excluir projeto"):
            if st.session_state.selected_project_id:
                _delete_project_active(st.session_state.selected_project_id)
                st.session_state.current_project_id = None
                st.session_state.selected_project_id = None
                st.session_state.latest_results = None
                st.success("Projeto excluído.")
                st.rerun()

    if st.session_state.current_project_id:
        st.caption(f"Projeto atual: {st.session_state.current_project_id}")

    st.markdown("---")
    st.markdown("### Uso")
    st.markdown(
        """
- Ajuste os dados técnicos
- Revise a alimentação por fase
- Confira o dashboard
- Gere o projeto completo
- Salve o projeto com resultados
- Use Supabase beta para testes remotos
"""
    )

fd = st.session_state.dash_form_data
report_profile = fd.get("report_profile", "Produtor")

st.markdown(
    """
<div class="hero-box">
    <div class="hero-title">Aqua Project Agent Dashboard</div>
    <div class="hero-subtitle">Planejador técnico-econômico de tilapicultura com visual profissional</div>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Projeto básico",
        "Crescimento",
        "Alimentação avançada",
        "Oxigênio e aeração",
        "Dashboard",
        "Relatório Profissional",
    ]
)

with tab1:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Dados básicos do projeto")

    fd["report_profile"] = st.selectbox(
        "Perfil do relatório",
        ["Produtor", "Técnico", "Banco/Financiamento"],
        index=["Produtor", "Técnico", "Banco/Financiamento"].index(
            fd.get("report_profile", "Produtor")
        ),
    )
    report_profile = fd["report_profile"]

    c1, c2 = st.columns(2)

    with c1:
        fd["project_name"] = st.text_input("Nome do projeto", fd["project_name"])
        fd["author_name"] = st.text_input("Autor", fd["author_name"])
        fd["species"] = st.text_input("Espécie", fd["species"])
        fd["system_type"] = st.text_input("Sistema de cultivo", fd["system_type"])
        fd["region_focus"] = st.text_input("Região de referência", fd["region_focus"])
        fd["number_of_units"] = st.number_input(
            "Número de unidades",
            min_value=1,
            value=int(fd["number_of_units"]),
        )
        fd["unit_volume_m3"] = st.number_input(
            "Volume por unidade (m³)",
            min_value=1.0,
            value=float(fd["unit_volume_m3"]),
            step=1.0,
        )
        fd["density_kg_m3"] = st.number_input(
            "Densidade final (kg/m³)",
            min_value=0.1,
            value=float(fd["density_kg_m3"]),
            step=0.5,
        )
        fd["survival_rate"] = st.number_input(
            "Sobrevivência (0 a 1)",
            min_value=0.01,
            max_value=0.999,
            value=float(fd["survival_rate"]),
            step=0.01,
        )
        fd["cycles_per_year"] = st.number_input(
            "Ciclos por ano",
            min_value=0.1,
            value=float(fd["cycles_per_year"]),
            step=0.1,
        )

        fd["production_strategy"] = st.selectbox(
            "Estratégia de produção",
            ["Ciclos simultâneos", "Escalonada"],
            index=0 if fd.get("production_strategy", "Ciclos simultâneos") == "Ciclos simultâneos" else 1,
        )

        if fd["production_strategy"] == "Escalonada":
            fd["harvest_interval_months"] = st.number_input(
                "Intervalo entre despescas (meses)",
                min_value=0.25,
                value=float(fd.get("harvest_interval_months", 1.0)),
                step=0.25,
            )

            fd["production_batch_mode"] = st.selectbox(
                "Definição dos lotes em paralelo",
                ["Automático", "Personalizado"],
                index=0 if fd.get("production_batch_mode", "Automático") == "Automático" else 1,
            )

            if fd["production_batch_mode"] == "Personalizado":
                fd["manual_parallel_batches"] = st.number_input(
                    "Quantidade de lotes em paralelo",
                    min_value=1,
                    value=int(fd.get("manual_parallel_batches", 6)),
                    step=1,
                )
                st.caption(
                    "Exemplo: 12 tanques e 6 lotes em paralelo = 2 tanques por lote, permitindo 1 despesca por mês após a fase de enchimento da esteira."
                )
            else:
                fd["manual_parallel_batches"] = int(fd.get("manual_parallel_batches", 6))

            st.caption(
                "Use 1,00 para produção mensal. O cálculo econômico anual é mantido, mas distribuído em lotes ao longo do ano."
            )
        else:
            fd["harvest_interval_months"] = float(fd.get("harvest_interval_months", 1.0))
            fd["production_batch_mode"] = fd.get("production_batch_mode", "Automático")
            fd["manual_parallel_batches"] = int(fd.get("manual_parallel_batches", 6))

    with c2:
        fd["sale_price_per_kg"] = st.number_input(
            "Preço de venda (R$/kg)",
            min_value=0.01,
            value=float(fd["sale_price_per_kg"]),
            step=0.1,
        )
        fd["fingerling_price"] = st.number_input(
            "Preço do alevino/recria (R$/unidade)",
            min_value=0.0,
            value=float(fd["fingerling_price"]),
            step=0.05,
        )

        fingerling_weight_g_value = float(fd.get("fingerling_weight_kg", 1.0))
        if fingerling_weight_g_value < 1:
            fingerling_weight_g_value = fingerling_weight_g_value * 1000.0

        fd["fingerling_weight_kg"] = st.number_input(
            "Peso do alevino/recria (g)",
            min_value=1.0,
            value=max(1.0, fingerling_weight_g_value),
            step=0.1,
        )

        fd["fingerling_rounding_mode"] = st.selectbox(
            "Compra de alevinos",
            ["Sem arredondamento", "Arredondar para cima"],
            index=1 if fd.get("fingerling_rounding_mode", "Arredondar para cima") == "Arredondar para cima" else 0,
        )
        if fd["fingerling_rounding_mode"] == "Arredondar para cima":
            fd["fingerling_rounding_base"] = st.number_input(
                "Lote mínimo de arredondamento (unid.)",
                min_value=1,
                value=int(fd.get("fingerling_rounding_base", 1000)),
                step=100,
            )
        else:
            fd["fingerling_rounding_base"] = int(fd.get("fingerling_rounding_base", 1000))

        fd["economic_model_mode"] = st.selectbox(
            "Modelo econômico",
            ["Simplificado", "Fixo + por tanque"],
            index=0 if fd.get("economic_model_mode", "Simplificado") == "Simplificado" else 1,
        )

        if fd["economic_model_mode"] == "Simplificado":
            fd["electricity_cost_cycle"] = st.number_input(
                "Outros custos de energia por ciclo (R$)",
                min_value=0.0,
                value=float(fd["electricity_cost_cycle"]),
                step=500.0,
            )
            fd["labor_cost_cycle"] = st.number_input(
                "Custo de mão de obra por ciclo (R$)",
                min_value=0.0,
                value=float(fd["labor_cost_cycle"]),
                step=500.0,
            )
            fd["other_costs_cycle"] = st.number_input(
                "Outros custos por ciclo (R$)",
                min_value=0.0,
                value=float(fd["other_costs_cycle"]),
                step=500.0,
            )
            fd["capex_total"] = st.number_input(
                "CAPEX base informado (R$)",
                min_value=0.0,
                value=float(fd["capex_total"]),
                step=1000.0,
            )

            fd["cost_scaling_mode"] = st.selectbox(
                "Escalonamento econômico",
                ["Fixos (não escalar)", "Escalonar pelo nº de tanques"],
                index=0 if fd.get("cost_scaling_mode", "Fixos (não escalar)") == "Fixos (não escalar)" else 1,
            )

            if fd["cost_scaling_mode"] == "Escalonar pelo nº de tanques":
                fd["cost_reference_units"] = st.number_input(
                    "Tanques de referência dos custos base",
                    min_value=1,
                    value=int(fd.get("cost_reference_units", fd.get("number_of_units", 1))),
                    step=1,
                )
                st.caption(
                    "Quando ativado, energia adicional, mão de obra, outros custos e CAPEX base são escalonados proporcionalmente ao número de tanques."
                )
            else:
                fd["cost_reference_units"] = int(fd.get("cost_reference_units", fd.get("number_of_units", 1)))
        else:
            st.markdown("#### Estrutura fixa + por tanque")
            e1, e2 = st.columns(2)
            with e1:
                fd["electricity_cost_fixed_cycle"] = st.number_input(
                    "Energia adicional fixa/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("electricity_cost_fixed_cycle", 0.0)),
                    step=100.0,
                )
                fd["labor_cost_fixed_cycle"] = st.number_input(
                    "Mão de obra fixa/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("labor_cost_fixed_cycle", 0.0)),
                    step=100.0,
                )
                fd["other_cost_fixed_cycle"] = st.number_input(
                    "Outros custos fixos/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("other_cost_fixed_cycle", 0.0)),
                    step=100.0,
                )
                fd["capex_fixed_total"] = st.number_input(
                    "CAPEX fixo do empreendimento (R$)",
                    min_value=0.0,
                    value=float(fd.get("capex_fixed_total", 0.0)),
                    step=1000.0,
                )
            with e2:
                fd["electricity_cost_per_unit_cycle"] = st.number_input(
                    "Energia adicional por tanque/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("electricity_cost_per_unit_cycle", 1000.0)),
                    step=50.0,
                )
                fd["labor_cost_per_unit_cycle"] = st.number_input(
                    "Mão de obra por tanque/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("labor_cost_per_unit_cycle", 1500.0)),
                    step=50.0,
                )
                fd["other_cost_per_unit_cycle"] = st.number_input(
                    "Outros custos por tanque/ciclo (R$)",
                    min_value=0.0,
                    value=float(fd.get("other_cost_per_unit_cycle", 1250.0)),
                    step=50.0,
                )
                fd["capex_per_unit"] = st.number_input(
                    "CAPEX por tanque (R$)",
                    min_value=0.0,
                    value=float(fd.get("capex_per_unit", 37500.0)),
                    step=1000.0,
                )

            st.caption(
                "Neste modo, o CAPEX total do relatório é calculado por: CAPEX fixo + (CAPEX por tanque × número de tanques)."
            )
            fd["cost_scaling_mode"] = fd.get("cost_scaling_mode", "Fixos (não escalar)")
            fd["cost_reference_units"] = int(fd.get("cost_reference_units", fd.get("number_of_units", 1)))

        fd["notes"] = st.text_area("Observações", fd["notes"], height=150)

    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Crescimento e temperatura")

    c1, c2 = st.columns(2)

    with c1:
        fd["initial_weight_g"] = st.number_input(
            "Peso inicial (g)",
            min_value=0.1,
            value=float(fd["initial_weight_g"]),
            step=1.0,
        )
        fd["target_weight_g"] = st.number_input(
            "Peso final alvo (g)",
            min_value=1.0,
            value=float(fd["target_weight_g"]),
            step=10.0,
        )
        fd["water_temperature_c"] = st.number_input(
            "Temperatura média da água (°C)",
            min_value=10.0,
            max_value=40.0,
            value=float(fd["water_temperature_c"]),
            step=0.5,
        )

    with c2:
        fd["base_daily_growth_g"] = st.number_input(
            "Ganho médio diário base a 28°C (g/dia)",
            min_value=0.1,
            value=float(fd["base_daily_growth_g"]),
            step=0.1,
        )
        st.info("O crescimento é ajustado pela temperatura e pela proteína das fases.")

    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Plano alimentar por fases")
    st.caption("Edite o FCR por fase aqui, junto com os demais parâmetros da alimentação.")

    for i in range(1, 5):
        with st.expander(f"Fase {i}", expanded=(i == 1)):
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                fd[f"phase{i}_min_g"] = st.number_input(
                    f"Peso mín. fase {i} (g)",
                    min_value=0.0,
                    value=float(fd[f"phase{i}_min_g"]),
                    step=1.0,
                    key=f"min_{i}",
                )
                fd[f"phase{i}_feeding_rate_percent"] = st.number_input(
                    f"Arraçoamento fase {i} (%)",
                    min_value=0.1,
                    value=float(fd[f"phase{i}_feeding_rate_percent"]),
                    step=0.1,
                    key=f"feedr_{i}",
                )

            with c2:
                fd[f"phase{i}_max_g"] = st.number_input(
                    f"Peso máx. fase {i} (g)",
                    min_value=1.0,
                    value=float(fd[f"phase{i}_max_g"]),
                    step=1.0,
                    key=f"max_{i}",
                )
                fd[f"phase{i}_meals_per_day"] = st.number_input(
                    f"Tratos/dia fase {i}",
                    min_value=1,
                    value=int(fd[f"phase{i}_meals_per_day"]),
                    step=1,
                    key=f"meals_{i}",
                )

            with c3:
                fd[f"phase{i}_protein_percent"] = st.number_input(
                    f"Proteína fase {i} (%)",
                    min_value=10.0,
                    max_value=60.0,
                    value=float(fd[f"phase{i}_protein_percent"]),
                    step=0.5,
                    key=f"prot_{i}",
                )
                fd[f"phase{i}_pellet_mm"] = st.number_input(
                    f"Granulometria fase {i} (mm)",
                    min_value=0.1,
                    value=float(fd[f"phase{i}_pellet_mm"]),
                    step=0.1,
                    key=f"pel_{i}",
                )

            with c4:
                fd[f"phase{i}_feed_price_per_kg"] = st.number_input(
                    f"Preço ração fase {i} (R$/kg)",
                    min_value=0.01,
                    value=float(fd[f"phase{i}_feed_price_per_kg"]),
                    step=0.1,
                    key=f"price_{i}",
                )

                fd[f"phase{i}_fcr"] = st.number_input(
                    f"FCR fase {i}",
                    min_value=0.5,
                    max_value=3.0,
                    value=float(fd.get(f"phase{i}_fcr", [1.20, 1.35, 1.50, 1.70][i - 1])),
                    step=0.01,
                    key=f"fcr_{i}",
                )

    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Oxigênio e aeração")

    if "aerator_quantity_mode" not in fd:
        fd["aerator_quantity_mode"] = "Manual"
    if "manual_aerators" not in fd:
        fd["manual_aerators"] = int(fd.get("number_of_units", 1))

    c1, c2 = st.columns(2)

    with c1:
        fd["oxygen_demand_mg_per_kg_h"] = st.number_input(
            "Demanda de oxigênio (mg O₂/kg/h)",
            min_value=10.0,
            value=float(fd["oxygen_demand_mg_per_kg_h"]),
            step=10.0,
        )

        fd["aerator_hp_each"] = st.number_input(
            "Potência de cada aerador (HP)",
            min_value=0.1,
            value=float(fd["aerator_hp_each"]),
            step=0.01,
        )

        fd["oxygen_transfer_kg_o2_hp_h"] = st.number_input(
            "Transferência de O₂ por HP/h",
            min_value=0.01,
            value=float(fd["oxygen_transfer_kg_o2_hp_h"]),
            step=0.01,
        )

    with c2:
        fd["aeration_hours_per_day"] = st.number_input(
            "Horas de aeração por dia",
            min_value=0.0,
            max_value=24.0,
            value=float(fd["aeration_hours_per_day"]),
            step=0.5,
        )

        fd["electricity_price_kwh"] = st.number_input(
            "Preço da energia (R$/kWh)",
            min_value=0.01,
            value=float(fd["electricity_price_kwh"]),
            step=0.05,
        )

        fd["aerator_quantity_mode"] = st.selectbox(
            "Modo de definição da quantidade de aeradores",
            ["Automático", "Manual"],
            index=1 if fd.get("aerator_quantity_mode", "Manual") == "Manual" else 0,
        )

        if fd["aerator_quantity_mode"] == "Manual":
            fd["manual_aerators"] = st.number_input(
                "Quantidade de aeradores a instalar",
                min_value=1,
                value=int(fd.get("manual_aerators", fd.get("number_of_units", 1))),
                step=1,
            )
        else:
            st.info("No modo automático, o sistema calcula a quantidade mínima necessária.")

    st.markdown(
        "Sugestão para aerador chafariz: usar 1 aerador por tanque quando esse for o critério operacional do projeto."
    )

    st.markdown("</div>", unsafe_allow_html=True)

fd_calc = fd.copy()
results = run_project_calculation(fd_calc)
st.session_state.latest_results = results
base_res = results["base"]


def render_kpi_card(
    container,
    title: str,
    value: str,
    accent: str,
    bg: str,
    icon: str = "●",
    caption: str = "",
):
    with container:
        st.markdown(
            f"""
<div class="kpi-card" style="border-left: 6px solid {accent}; border-top: 4px solid {accent}; background: linear-gradient(135deg, {bg} 0%, #ffffff 100%);">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
        <div class="kpi-title">{title}</div>
        <div style="font-size:24px; line-height:1;">{icon}</div>
    </div>
    <div class="kpi-value">{value}</div>
    <div class="kpi-caption">{caption}</div>
</div>
""",
            unsafe_allow_html=True,
        )


with tab5:
    st.subheader("Indicadores principais")

    save_col1, save_col2 = st.columns([1.2, 2.8])
    with save_col1:
        if st.button("Salvar projeto completo", type="primary"):
            payload = build_project_payload(
                st.session_state.dash_form_data,
                results,
                st.session_state.current_project_id,
            )
            project_id = _save_project_active(payload, st.session_state.current_project_id)
            st.session_state.current_project_id = project_id
            st.session_state.selected_project_id = project_id
            st.success(f"Projeto salvo com resultados: {project_id}")

    with save_col2:
        if st.session_state.current_project_id:
            st.caption(f"Projeto ativo: {st.session_state.current_project_id}")
        else:
            st.caption("Projeto ainda não salvo. Use o botão ao lado para registrar este cenário.")

    c1, c2, c3, c4 = st.columns(4)
    render_kpi_card(c1, "Produção/ciclo", f"{num(base_res.get('production_per_cycle_kg'))} kg", "#2f6fdf", "#eef4ff", "📦", "Volume produtivo do ciclo")
    render_kpi_card(c2, "Receita/ciclo", brl(base_res.get("revenue_cycle")), "#2e7d32", "#eef8ef", "💰", "Receita bruta estimada")
    render_kpi_card(c3, "Margem/ciclo", brl(base_res.get("gross_margin_cycle")), "#1b5e20", "#edf7ed", "📈", "Resultado operacional do ciclo")
    render_kpi_card(c4, "Payback estimado", num(base_res.get("payback_years"), 2) + " anos" if base_res.get("payback_years") is not None else "-", "#5d4037", "#f5efec", "⏱️", "Retorno estimado do investimento")

    c5, c6, c7, c8 = st.columns(4)
    energia_total_ciclo = float(base_res.get("electricity_cost_cycle_effective", 0.0) or 0.0) + float(base_res.get("aeration_energy_cost_cycle", 0.0) or 0.0)
    render_kpi_card(c5, "Custo ração/ciclo", brl(base_res.get("feed_cost_cycle")), "#8d6e63", "#f6efeb", "🟧", "Principal componente do OPEX")
    render_kpi_card(c6, "Custo alevino/ciclo", brl(base_res.get("fingerling_cost_cycle")), "#556b2f", "#f1f6e9", "🐠", "Reposição biológica do ciclo")
    render_kpi_card(c7, "Mão de obra/ciclo", brl(base_res.get("labor_cost_cycle_effective")), "#c0392b", "#fbefed", "👷", "Equipe operacional considerada")
    render_kpi_card(c8, "Energia elétrica/ciclo", brl(energia_total_ciclo), "#1565c0", "#edf4fd", "⚡", "Energia adicional + aeração")

    c9, c10, c11, c12 = st.columns(4)
    render_kpi_card(c9, "OPEX/ciclo", brl(base_res.get("opex_cycle")), "#37474f", "#eef2f3", "🧾", "Custo operacional total")
    render_kpi_card(c10, "Custo por kg", brl(base_res.get("cost_per_kg")) + "/kg", "#1e6091", "#eef5f9", "⚖️", "Eficiência econômica unitária")
    render_kpi_card(c11, "FCR implícito", num(base_res.get("implied_fcr")) if base_res.get("implied_fcr") is not None else "-", "#6d4c41", "#f7f0ec", "🎯", "Conversão alimentar do ciclo")
    render_kpi_card(c12, "Aeradores instalados", num(base_res.get("required_aerators"), 0), "#1976d2", "#edf5ff", "🌬️", "Capacidade operacional instalada")

    schedule = base_res.get("production_schedule", {})
    if schedule:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Estratégia operacional de produção")

        s1, s2, s3, s4 = st.columns(4)

        if schedule.get("production_strategy") == "Escalonada":
            schedule_cards = [
                ("Produção por despesca", f"{num(schedule.get('production_per_harvest_kg'))} kg"),
                ("Tanques por lote", num(schedule.get("units_per_batch_exact"), 2)),
                ("Lotes em paralelo", num(schedule.get("batches_in_parallel"), 0)),
                ("1ª despesca após", f"{num(schedule.get('first_harvest_after_months'), 1)} meses"),
            ]
        else:
            schedule_cards = [
                ("Modo", schedule.get("production_strategy", "-")),
                ("Tanques por ciclo", num(schedule.get("units_per_batch_exact"), 0)),
                ("Colheitas/ano", num(schedule.get("harvests_per_year"), 2)),
                ("Produção por colheita", f"{num(schedule.get('production_per_harvest_kg'))} kg"),
            ]

        for col, (title, value) in zip([s1, s2, s3, s4], schedule_cards):
            with col:
                st.markdown(
                    f"""
<div class="kpi-card">
    <div class="kpi-title">{title}</div>
    <div class="kpi-value">{value}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        if schedule.get("production_strategy") == "Escalonada":
            mode_text = schedule.get("production_batch_mode", "Automático")
            st.info(
                f"Modo {mode_text}. Com {int(fd['number_of_units'])} tanques e intervalo de {num(schedule.get('harvest_interval_months'), 2)} mês(es), "
                f"o sistema trabalha com {num(schedule.get('batches_in_parallel'), 0)} lotes em paralelo. "
                f"Distribuição sugerida: {schedule.get('batch_distribution_note', '-')}"
            )
            if schedule.get("production_batch_mode") == "Personalizado" and schedule.get("automatic_parallel_batches"):
                st.caption(
                    f"Lotes automáticos estimados pelo tempo de ciclo: {num(schedule.get('automatic_parallel_batches'), 0)}. "
                    "Se o valor personalizado for menor, você estará assumindo um escalonamento mais agressivo que o tempo biológico calculado."
                )
            st.caption(
                "A primeira despesca acontece após o tempo completo de cultivo do primeiro lote; depois disso, a retirada passa a seguir o intervalo definido."
            )
        else:
            st.info("No modo de ciclos simultâneos, todos os tanques entram e saem do ciclo ao mesmo tempo.")

        st.markdown("</div>", unsafe_allow_html=True)

    if base_res.get("economic_model_mode") == "Fixo + por tanque":
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Estrutura econômica: fixo + por tanque")
        e1, e2, e3, e4 = st.columns(4)
        econ_cards = [
            ("Energia adicional/ciclo", brl(base_res.get("electricity_cost_cycle_effective"))),
            ("Mão de obra/ciclo", brl(base_res.get("labor_cost_cycle_effective"))),
            ("Outros custos/ciclo", brl(base_res.get("other_costs_cycle_effective"))),
            ("CAPEX considerado", brl(base_res.get("capex_total_effective"))),
        ]
        for col, (title, value) in zip([e1, e2, e3, e4], econ_cards):
            with col:
                st.markdown(
                    f"""
<div class="kpi-card">
    <div class="kpi-title">{title}</div>
    <div class="kpi-value">{value}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
        st.caption(
            "O cálculo econômico foi montado com uma parte fixa do empreendimento e outra parte variável por tanque."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif base_res.get("cost_scaling_mode") == "Escalonar pelo nº de tanques":
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Escalonamento econômico aplicado")
        e1, e2, e3, e4 = st.columns(4)
        econ_cards = [
            ("Fator de escala", num(base_res.get("cost_scale_factor"), 3)),
            ("Energia extra/ciclo", brl(base_res.get("electricity_cost_cycle_effective"))),
            ("Mão de obra/ciclo", brl(base_res.get("labor_cost_cycle_effective"))),
            ("CAPEX considerado", brl(base_res.get("capex_total_effective"))),
        ]
        for col, (title, value) in zip([e1, e2, e3, e4], econ_cards):
            with col:
                st.markdown(
                    f"""
<div class="kpi-card">
    <div class="kpi-title">{title}</div>
    <div class="kpi-value">{value}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
        st.caption(
            f"Custos base referenciados em {int(base_res.get('cost_reference_units', 1))} tanque(s) e recalculados para {int(fd['number_of_units'])} tanque(s)."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    df_growth = pd.DataFrame(base_res.get("growth_curve", []))
    df_feed = pd.DataFrame(base_res.get("feeding_plan", []))
    df_cost = pd.DataFrame(base_res.get("cost_curve", []))

    if not df_feed.empty:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Resumo visual da operação")

        cost_breakdown = pd.DataFrame(
            [
                {"categoria": "Ração", "valor": float(base_res.get("feed_cost_cycle", 0.0))},
                {"categoria": "Alevinos", "valor": float(base_res.get("fingerling_cost_cycle", 0.0))},
                {"categoria": "Energia adicional", "valor": float(base_res.get("electricity_cost_cycle_effective", 0.0))},
                {"categoria": "Mão de obra", "valor": float(base_res.get("labor_cost_cycle_effective", 0.0))},
                {"categoria": "Outros custos", "valor": float(base_res.get("other_costs_cycle_effective", 0.0))},
                {"categoria": "Aeração", "valor": float(base_res.get("aeration_energy_cost_cycle", 0.0))},
            ]
        )
        cost_breakdown = cost_breakdown[cost_breakdown["valor"] > 0].copy()

        vis1, vis2 = st.columns(2)

        with vis1:
            if not df_growth.empty and "day" in df_growth.columns and "weight_g" in df_growth.columns:
                fig_growth = px.line(
                    df_growth,
                    x="day",
                    y="weight_g",
                    markers=True,
                    title="Crescimento dos peixes ao longo do ciclo",
                    labels={"day": "Dia", "weight_g": "Peso (g)"},
                )
                fig_growth.update_traces(line=dict(width=4), marker=dict(size=8))
                fig_growth.update_layout(
                    template="plotly_white",
                    height=380,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                )
                st.plotly_chart(fig_growth, use_container_width=True)

        with vis2:
            if not df_growth.empty and "day" in df_growth.columns and "biomass_kg" in df_growth.columns:
                fig_biomass = px.area(
                    df_growth,
                    x="day",
                    y="biomass_kg",
                    markers=True,
                    title="Evolução da biomassa no ciclo",
                    labels={"day": "Dia", "biomass_kg": "Biomassa (kg)"},
                )
                fig_biomass.update_traces(line=dict(width=3))
                fig_biomass.update_layout(
                    template="plotly_white",
                    height=380,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                )
                st.plotly_chart(fig_biomass, use_container_width=True)

        vis3, vis4 = st.columns(2)

        with vis3:
            if not cost_breakdown.empty:
                fig_opex = px.pie(
                    cost_breakdown,
                    names="categoria",
                    values="valor",
                    hole=0.58,
                    title="Composição visual do OPEX por ciclo",
                )
                fig_opex.update_traces(textposition="inside", textinfo="percent+label")
                fig_opex.update_layout(
                    template="plotly_white",
                    height=420,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                    legend_title_text="Categoria",
                )
                st.plotly_chart(fig_opex, use_container_width=True)

        with vis4:
            waterfall_df = pd.DataFrame(
                [
                    {"etapa": "Receita", "valor": float(base_res.get("revenue_cycle", 0.0)), "tipo": "relative"},
                    {"etapa": "Ração", "valor": -float(base_res.get("feed_cost_cycle", 0.0)), "tipo": "relative"},
                    {"etapa": "Alevinos", "valor": -float(base_res.get("fingerling_cost_cycle", 0.0)), "tipo": "relative"},
                    {"etapa": "Energia", "valor": -float(base_res.get("electricity_cost_cycle_effective", 0.0)), "tipo": "relative"},
                    {"etapa": "Mão de obra", "valor": -float(base_res.get("labor_cost_cycle_effective", 0.0)), "tipo": "relative"},
                    {"etapa": "Outros", "valor": -float(base_res.get("other_costs_cycle_effective", 0.0)), "tipo": "relative"},
                    {"etapa": "Aeração", "valor": -float(base_res.get("aeration_energy_cost_cycle", 0.0)), "tipo": "relative"},
                    {"etapa": "Margem", "valor": 0.0, "tipo": "total"},
                ]
            )
            fig_margin = go.Figure(
                go.Waterfall(
                    name="Margem por ciclo",
                    orientation="v",
                    measure=waterfall_df["tipo"],
                    x=waterfall_df["etapa"],
                    y=waterfall_df["valor"],
                    connector={"line": {"width": 1}},
                )
            )
            fig_margin.update_layout(
                template="plotly_white",
                title="Formação da margem por ciclo",
                height=420,
                margin=dict(l=20, r=20, t=60, b=20),
                title_x=0.02,
                showlegend=False,
            )
            st.plotly_chart(fig_margin, use_container_width=True)

        vis5, vis6 = st.columns(2)

        with vis5:
            if "phase_name" in df_feed.columns and "feed_phase_kg" in df_feed.columns:
                fig_feed = px.bar(
                    df_feed,
                    x="feed_phase_kg",
                    y="phase_name",
                    orientation="h",
                    text="feed_phase_kg",
                    title="Consumo de ração por fase",
                    labels={"feed_phase_kg": "Ração (kg)", "phase_name": "Fase"},
                )
                fig_feed.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig_feed.update_layout(
                    template="plotly_white",
                    height=380,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                    yaxis=dict(categoryorder="array", categoryarray=list(df_feed["phase_name"])[::-1]),
                )
                st.plotly_chart(fig_feed, use_container_width=True)

        with vis6:
            if "phase_name" in df_feed.columns and "feed_phase_cost" in df_feed.columns:
                fig_phase_cost = px.bar(
                    df_feed,
                    x="phase_name",
                    y="feed_phase_cost",
                    text="feed_phase_cost",
                    title="Custo de ração por fase",
                    labels={"phase_name": "Fase", "feed_phase_cost": "Custo (R$)"},
                )
                fig_phase_cost.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig_phase_cost.update_layout(
                    template="plotly_white",
                    height=380,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                )
                st.plotly_chart(fig_phase_cost, use_container_width=True)

        if not df_cost.empty and "day" in df_cost.columns and "cumulative_feed_cost" in df_cost.columns:
            fig_cost_curve = px.area(
                df_cost,
                x="day",
                y="cumulative_feed_cost",
                markers=True,
                title="Custo acumulado da ração",
                labels={"day": "Dia", "cumulative_feed_cost": "Custo acumulado (R$)"},
            )
            fig_cost_curve.update_traces(line=dict(width=3))
            fig_cost_curve.update_layout(
                template="plotly_white",
                height=400,
                margin=dict(l=20, r=20, t=60, b=20),
                title_x=0.02,
            )
            st.plotly_chart(fig_cost_curve, use_container_width=True)

        if schedule.get("production_strategy") == "Escalonada":
            harvests_per_year = float(schedule.get("harvests_per_year", 0) or 0)
            if harvests_per_year > 0:
                months = [
                    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
                ]
                production_month = [0.0] * 12
                full_harvests = int(harvests_per_year)
                for i in range(min(full_harvests, 12)):
                    production_month[i] = float(schedule.get("production_per_harvest_kg", 0.0))
                df_month = pd.DataFrame({"mês": months, "produção_kg": production_month})

                fig_month = px.bar(
                    df_month,
                    x="mês",
                    y="produção_kg",
                    text="produção_kg",
                    title="Distribuição visual da produção mensal",
                    labels={"mês": "Mês", "produção_kg": "Produção (kg)"},
                )
                fig_month.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig_month.update_layout(
                    template="plotly_white",
                    height=380,
                    margin=dict(l=20, r=20, t=60, b=20),
                    title_x=0.02,
                )
                st.plotly_chart(fig_month, use_container_width=True)

        with st.expander("Tabela detalhada do plano alimentar por fase", expanded=False):
            st.caption("Para alterar FCR, use a aba Alimentação avançada.")
            columns = [
                "phase_name",
                "weight_range",
                "days_in_phase",
                "protein_percent",
                "pellet_mm",
                "feed_price_per_kg",
                "phase_fcr",
                "biomass_gain_phase_kg",
                "feed_phase_kg",
                "feed_phase_cost",
            ]
            existing = [c for c in columns if c in df_feed.columns]
            st.dataframe(df_feed[existing], use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

with tab6:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Relatório Profissional")
    st.caption("Estruturado para produtor, técnico ou banco/financiamento.")

    professional_report = build_professional_project_report(
        results,
        profile=report_profile,
    )

    st.markdown("### Pré-visualização do relatório")
    st.markdown(professional_report)

    project_root = Path(__file__).resolve().parent
    save_dir = project_root / output_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    st.info(f"Pasta de saída atual: {save_dir}")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Gerar Relatório (Markdown)"):
            md_path = save_dir / f"{output_name}_completo.md"
            md_path.write_text(professional_report, encoding="utf-8")
            st.success(f"Relatório Markdown salvo em: {md_path}")

    with col2:
        if st.button("Gerar Relatório Premium (DOCX)"):
            md_path = save_dir / f"{output_name}_completo.md"
            md_path.write_text(professional_report, encoding="utf-8")

            docx_path = save_dir / f"{output_name}_completo.docx"
            export_dashboard_report_to_docx(
                results,
                docx_path,
                inp.project_name,
                inp.author_name,
                report_profile,
            )
            st.success(f"Relatório DOCX premium salvo em: {docx_path}")

    with col3:
        if st.button("Gerar Relatório Premium (DOCX + PDF)"):
            md_path = save_dir / f"{output_name}_completo.md"
            md_path.write_text(professional_report, encoding="utf-8")

            docx_path = save_dir / f"{output_name}_completo.docx"
            export_dashboard_report_to_docx(
                results,
                docx_path,
                inp.project_name,
                inp.author_name,
                report_profile,
            )

            try:
                pdf_path = export_docx_to_pdf(docx_path, save_dir)
                st.success(f"Relatórios salvos em: {docx_path} e {pdf_path}")
            except Exception as e:
                st.warning(f"DOCX salvo em {docx_path}, mas o PDF não foi gerado: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
