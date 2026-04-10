from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Permite rodar a API a partir da raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from core_engine.service import run_project_calculation  # noqa: E402


app = FastAPI(
    title="Aqua Project Agent API",
    version="0.1.0",
    description="API inicial para cálculo técnico-econômico do sistema aquícola.",
)


class ProjectCalculationRequest(BaseModel):
    payload: dict[str, Any] = Field(..., description="Dados do formulário do projeto")


class ProjectCalculationResponse(BaseModel):
    ok: bool
    results: dict[str, Any]


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "aqua-project-agent-api",
        "environment": os.getenv("APP_ENV", "development"),
    }


@app.post("/calculate", response_model=ProjectCalculationResponse)
def calculate_project(request: ProjectCalculationRequest) -> ProjectCalculationResponse:
    try:
        results = run_project_calculation(request.payload)
        return ProjectCalculationResponse(ok=True, results=results)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
