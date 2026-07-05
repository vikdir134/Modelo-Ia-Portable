from __future__ import annotations

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]

ARTEFACTOS_DIR = BACKEND_DIR / "artefactos_lightgbm"

RUTA_MODELO = (
    ARTEFACTOS_DIR
    / "modelo_fraude_lightgbm_portable.joblib"
)

RUTA_METRICAS = (
    ARTEFACTOS_DIR
    / "metricas_lightgbm.json"
)

RUTA_IMPORTANCIA_GLOBAL = (
    ARTEFACTOS_DIR
    / "importancia_global_shap.csv"
)