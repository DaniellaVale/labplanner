# backend_core/app/doe_client.py

from __future__ import annotations

import os
from typing import Any, Dict

import requests

DOE_SERVICE_URL = os.getenv("DOE_SERVICE_URL", "http://doe_service:8000")


def call_doe_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{DOE_SERVICE_URL}/generate"

    try:
        response = requests.post(url, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise RuntimeError(f"Falha de comunicação com o DOE Service: {str(exc)}") from exc

    if response.status_code >= 400:
        try:
            error_detail = response.json().get("detail", response.text)
        except Exception:
            error_detail = response.text
        raise RuntimeError(f"Erro do DOE Service: {error_detail}")

    try:
        return response.json()
    except Exception as exc:
        raise RuntimeError("Resposta inválida do DOE Service.") from exc