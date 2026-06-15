
from __future__ import annotations

import json
import os

from datetime import date
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# Esta importación es necesaria para joblib
from fraude_features import FeatureEngineeringFraude


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(
        BASE_DIR,
        "artefactos_lightgbm",
        "modelo_fraude_lightgbm_portable.joblib"
    )
)

METRICS_PATH = os.getenv(
    "METRICS_PATH",
    os.path.join(
        BASE_DIR,
        "artefactos_lightgbm",
        "metricas_lightgbm.json"
    )
)


# ============================================================
# CARGAR MODELO
# ============================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"No se encontró el modelo en: {MODEL_PATH}"
    )

modelo = joblib.load(
    MODEL_PATH
)


# ============================================================
# CARGAR METADATOS
# ============================================================

metricas_modelo = {}

if os.path.exists(METRICS_PATH):

    with open(
        METRICS_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        metricas_modelo = json.load(
            archivo
        )


UMBRAL_CLASIFICACION = float(
    metricas_modelo.get(
        "umbral_clasificacion",
        0.50
    )
)


# ============================================================
# ESQUEMAS DE ENTRADA
# ============================================================

class ReclamacionEntrada(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )

    Provider_ID: str = Field(
        default="API_PROVIDER",
        min_length=1
    )

    Claim_ID: str = Field(
        default="API_CLAIM",
        min_length=1
    )

    Patient_Age: int = Field(
        ge=0,
        le=120
    )

    Patient_Gender: str = Field(
        min_length=1
    )

    Diagnosis_Code: str = Field(
        min_length=1
    )

    Procedure_Code: str = Field(
        min_length=1
    )

    Claim_Amount: float = Field(
        gt=0
    )

    Approved_Amount: float = Field(
        ge=0
    )

    Insurance_Type: str = Field(
        min_length=1
    )

    Provider_Specialty: str = Field(
        min_length=1
    )

    Patient_State: str = Field(
        min_length=1
    )

    Claim_Submission_Date: date

    Days_Between_Service_and_Claim: int = Field(
        ge=0
    )

    Number_of_Claims_Per_Provider_Monthly: int = Field(
        ge=0
    )

    Claim_Status: str = Field(
        min_length=1
    )

    Length_of_Stay: int = Field(
        ge=0
    )

    Chronic_Condition_Flag: Literal[0, 1]

    Prior_Visits_12m: int = Field(
        ge=0
    )

    Visit_Type: str = Field(
        min_length=1
    )


# ============================================================
# ESQUEMAS DE SALIDA
# ============================================================

class VariablesDerivadasSalida(BaseModel):

    Submission_Month: int
    Submission_Year: int
    Approval_Ratio: float
    Amount_Diff: float


class PrediccionSalida(BaseModel):

    modelo: str
    claim_id: str

    prediccion: Literal[0, 1]
    prediccion_texto: str

    probabilidad_fraude: float
    probabilidad_legitimo: float

    nivel_riesgo: str
    umbral: float

    recomendacion: str

    variables_derivadas: (
        VariablesDerivadasSalida
    )


# ============================================================
# CREAR APLICACIÓN
# ============================================================

app = FastAPI(
    title=(
        "API de detección de fraude "
        "en reclamaciones de salud"
    ),
    description=(
        "API para estimar la probabilidad de fraude "
        "mediante un modelo LightGBM."
    ),
    version="1.0.0"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtener_nivel_riesgo(
    probabilidad: float
) -> str:

    if probabilidad < 0.30:
        return "Bajo"

    if probabilidad < 0.50:
        return "Moderado"

    if probabilidad < 0.80:
        return "Alto"

    return "Crítico"


def convertir_a_dataframe(
    entrada: ReclamacionEntrada
) -> pd.DataFrame:

    datos = entrada.model_dump()

    # Convertir date a texto compatible con pandas
    datos["Claim_Submission_Date"] = (
        entrada.Claim_Submission_Date.isoformat()
    )

    return pd.DataFrame(
        [datos]
    )


# ============================================================
# ENDPOINT PRINCIPAL
# ============================================================

@app.get("/")
def inicio():

    return {
        "mensaje": (
            "API de detección de fraude "
            "con LightGBM"
        ),
        "documentacion": "/docs",
        "estado": "/health",
        "prediccion": "/predecir"
    }


# ============================================================
# ESTADO DE LA API
# ============================================================

@app.get("/health")
def verificar_estado():

    return {
        "status": "ok",
        "modelo": "LightGBM",
        "modelo_cargado": modelo is not None,
        "umbral": UMBRAL_CLASIFICACION
    }


# ============================================================
# INFORMACIÓN DEL MODELO
# ============================================================

@app.get("/modelo")
def informacion_modelo():

    return {
        "modelo": metricas_modelo.get(
            "modelo",
            "LightGBM"
        ),
        "objetivo": metricas_modelo.get(
            "objetivo",
            "Is_Fraud"
        ),
        "umbral": UMBRAL_CLASIFICACION,
        "mejores_hiperparametros": (
            metricas_modelo.get(
                "mejores_hiperparametros",
                {}
            )
        ),
        "metricas_validacion_cruzada": (
            metricas_modelo.get(
                "metricas_validacion_cruzada",
                {}
            )
        ),
        "metricas_prueba": (
            metricas_modelo.get(
                "metricas_prueba",
                {}
            )
        )
    }


# ============================================================
# REALIZAR PREDICCIÓN
# ============================================================

@app.post(
    "/predecir",
    response_model=PrediccionSalida
)
def predecir_fraude(
    entrada: ReclamacionEntrada
):

    try:

        registro = convertir_a_dataframe(
            entrada
        )

        probabilidad_fraude = float(
            modelo.predict_proba(
                registro
            )[0, 1]
        )

        probabilidad_legitimo = float(
            1.0 - probabilidad_fraude
        )

        prediccion = int(
            probabilidad_fraude
            >= UMBRAL_CLASIFICACION
        )

        nivel_riesgo = obtener_nivel_riesgo(
            probabilidad_fraude
        )

        approval_ratio = float(
            entrada.Approved_Amount
            / entrada.Claim_Amount
        )

        amount_diff = float(
            entrada.Claim_Amount
            - entrada.Approved_Amount
        )

        if prediccion == 1:

            prediccion_texto = "Fraude"

            recomendacion = (
                "Enviar la reclamación "
                "a revisión especializada."
            )

        else:

            prediccion_texto = "Legítimo"

            recomendacion = (
                "Continuar con el procedimiento habitual."
            )

        return PrediccionSalida(
            modelo="LightGBM",
            claim_id=entrada.Claim_ID,
            prediccion=prediccion,
            prediccion_texto=prediccion_texto,
            probabilidad_fraude=probabilidad_fraude,
            probabilidad_legitimo=probabilidad_legitimo,
            nivel_riesgo=nivel_riesgo,
            umbral=UMBRAL_CLASIFICACION,
            recomendacion=recomendacion,

            variables_derivadas=(
                VariablesDerivadasSalida(
                    Submission_Month=(
                        entrada
                        .Claim_Submission_Date
                        .month
                    ),
                    Submission_Year=(
                        entrada
                        .Claim_Submission_Date
                        .year
                    ),
                    Approval_Ratio=approval_ratio,
                    Amount_Diff=amount_diff
                )
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo realizar la predicción. "
                f"Error: {str(error)}"
            )
        ) from error
