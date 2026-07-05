from __future__ import annotations

from fastapi import APIRouter

from api_lightgbm import modelo, UMBRAL_CLASIFICACION


router = APIRouter(
    prefix="/health",
    tags=["Estado"]
)


@router.get("")
def verificar_estado():
    return {
        "status": "ok",
        "modelo": "LightGBM",
        "modelo_cargado": modelo is not None,
        "umbral": UMBRAL_CLASIFICACION
    }