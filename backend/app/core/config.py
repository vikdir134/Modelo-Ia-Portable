from __future__ import annotations

import os


def obtener_origenes_cors() -> list[str]:
    """
    Obtiene los dominios permitidos para CORS.

    En local permite localhost.
    En producción se puede configurar FRONTEND_URL
    desde Render.
    """

    frontend_url = os.getenv(
        "FRONTEND_URL",
        ""
    ).strip()

    origenes = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000"
    ]

    if frontend_url:
        origenes.append(frontend_url)

    return origenes


APP_NAME = (
    "Sistema Multiagente de Detección "
    "de Fraude Médico"
)

APP_VERSION = "3.0.0"

API_PREFIX = "/api"