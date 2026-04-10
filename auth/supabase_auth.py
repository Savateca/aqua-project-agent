from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


def is_supabase_configured() -> bool:
    return bool(
        os.getenv("SUPABASE_URL")
        and os.getenv("SUPABASE_ANON_KEY")
        and os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )


def _base_url() -> str:
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL não configurada no .env")
    return url.rstrip("/")


def _anon_key() -> str:
    key = os.getenv("SUPABASE_ANON_KEY")
    if not key:
        raise RuntimeError("SUPABASE_ANON_KEY não configurada no .env")
    return key


def _service_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY não configurada no .env")
    return key


def public_headers() -> dict[str, str]:
    key = _anon_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def service_headers(prefer: str | None = None) -> dict[str, str]:
    key = _service_key()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    response = requests.post(
        f"{_base_url()}/auth/v1/token?grant_type=password",
        headers=public_headers(),
        json={"email": email, "password": password},
        timeout=30,
    )

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Falha no login: {detail}")

    data = response.json()
    user = data.get("user") or {}
    return {
        "user_id": user.get("id"),
        "email": user.get("email", email),
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
    }
