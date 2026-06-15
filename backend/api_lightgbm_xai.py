
from __future__ import annotations

import os

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agente_auditoria import (
    construir_paquete_auditoria,
    construir_prompt_super_agente,
    generar_informe_markdown,
    construir_prompt_notebooklm
)
from api_lightgbm import (
    app as app_base,
    modelo,
    ReclamacionEntrada,
    convertir_a_dataframe
)

from xai_lightgbm import (
    ExplicadorFraudeLightGBM
)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

RUTA_IMPORTANCIA = os.path.join(
    BASE_DIR,
    "artefactos_lightgbm",
    "importancia_global_shap.csv"
)


# ============================================================
# NUEVA APLICACIÓN
# ============================================================

app = FastAPI(
    title=(
        "Sistema de detección de fraude "
        "con LightGBM y SHAP"
    ),
    description=(
        "API de predicción y explicación "
        "de reclamaciones de salud."
    ),
    version="2.0.0"
)


# Permitirá que el frontend local se conecte.
# Para un despliegue público debe limitarse
# a dominios específicos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Copiar las rutas de la API original:
# /health, /modelo, /predecir
app.include_router(
    app_base.router
)


explicador = ExplicadorFraudeLightGBM(
    pipeline=modelo,
    umbral=0.50
)


# ============================================================
# ENDPOINT: SOLO EXPLICACIÓN
# ============================================================

@app.post("/explicar")
def explicar_reclamacion(
    entrada: ReclamacionEntrada
):

    try:
        registro = convertir_a_dataframe(
            entrada
        )

        resultado = (
            explicador.explicar_registro(
                registro,
                top_n=8
            )
        )

        return resultado

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo explicar la reclamación. "
                f"Error: {str(error)}"
            )
        ) from error


# ============================================================
# ENDPOINT: PREDICCIÓN + XAI + GRÁFICO
# ============================================================

@app.post("/predecir-explicar")
def predecir_y_explicar(
    entrada: ReclamacionEntrada
):

    try:
        registro = convertir_a_dataframe(
            entrada
        )

        resultado = (
            explicador.explicar_registro(
                registro,
                top_n=8
            )
        )

        resultado["grafico_shap_base64"] = (
            explicador.grafico_local_base64(
                registro,
                top_n=10
            )
        )

        resultado["claim_id"] = (
            entrada.Claim_ID
        )

        return resultado

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo predecir y explicar. "
                f"Error: {str(error)}"
            )
        ) from error


# ============================================================
# ENDPOINT: IMPORTANCIA GLOBAL
# ============================================================

@app.get("/importancia-global")
def obtener_importancia_global():

    if not os.path.exists(
        RUTA_IMPORTANCIA
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "No se encontró el archivo de "
                "importancia global."
            )
        )

    tabla = pd.read_csv(
        RUTA_IMPORTANCIA
    )

    return {
        "modelo": "LightGBM",
        "cantidad_variables": len(tabla),
        "variables": tabla.to_dict(
            orient="records"
        )
    }

# ============================================================
# CATÁLOGOS PARA LOS SELECTORES DEL FRONTEND
# ============================================================

@app.get("/catalogos")
def obtener_catalogos():
    """
    Obtiene las categorías aprendidas por el OneHotEncoder.

    Esto permite que el frontend muestre únicamente
    las categorías utilizadas durante el entrenamiento.
    """

    try:
        preprocessor = modelo.named_steps[
            "preprocessor"
        ]

        columnas_categoricas = None
        pipeline_categorico = None

        for nombre, transformador, columnas in (
            preprocessor.transformers_
        ):
            if nombre == "cat":
                columnas_categoricas = list(columnas)
                pipeline_categorico = transformador
                break

        if pipeline_categorico is None:
            raise RuntimeError(
                "No se encontró el transformador categórico."
            )

        encoder = None

        if hasattr(
            pipeline_categorico,
            "named_steps"
        ):
            for paso in (
                pipeline_categorico
                .named_steps
                .values()
            ):
                if hasattr(paso, "categories_"):
                    encoder = paso
                    break

        if encoder is None:
            raise RuntimeError(
                "No se encontró el OneHotEncoder entrenado."
            )

        catalogos = {}

        for columna, categorias in zip(
            columnas_categoricas,
            encoder.categories_
        ):
            catalogos[columna] = [
                str(categoria)
                for categoria in categorias
            ]

        return {
            "modelo": "LightGBM",
            "categorias": catalogos
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudieron recuperar los catálogos. "
                f"Error: {str(error)}"
            )
        ) from error


# ============================================================
# SERVIR EL FRONTEND
# ============================================================

FRONTEND_DIR = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "frontend"
    )
)

if os.path.isdir(FRONTEND_DIR):
    app.mount(
        "/app",
        StaticFiles(
            directory=FRONTEND_DIR,
            html=True
        ),
        name="frontend"
    )
else:
    print(
        "Advertencia: no se encontró el frontend en:",
        FRONTEND_DIR
    )
    

    # ============================================================
# ENDPOINT COMPLETO:
# PREDICCIÓN + XAI + INFORME + PROMPTS
# ============================================================

@app.post("/analizar-completo")
def analizar_reclamacion_completa(
    entrada: ReclamacionEntrada
):
    try:
        # Convertir entrada a DataFrame
        registro = convertir_a_dataframe(
            entrada
        )

        # Predicción y explicación SHAP
        resultado_xai = (
            explicador.explicar_registro(
                registro,
                top_n=8
            )
        )

        # Gráfico SHAP individual
        resultado_xai[
            "grafico_shap_base64"
        ] = explicador.grafico_local_base64(
            registro,
            top_n=10
        )

        resultado_xai[
            "claim_id"
        ] = entrada.Claim_ID

        # Datos originales en formato JSON
        datos_reclamacion = (
            entrada.model_dump(
                mode="json"
            )
        )

        # Paquete integrado de auditoría
        paquete = construir_paquete_auditoria(
            datos_reclamacion=datos_reclamacion,
            resultado_xai=resultado_xai
        )

        # Prompt reutilizable para un LLM
        prompt_super_agente = (
            construir_prompt_super_agente(
                paquete
            )
        )

        # Informe generado localmente
        informe = generar_informe_markdown(
            paquete
        )

        # Prompt específico para NotebookLM
        prompt_notebooklm = (
            construir_prompt_notebooklm()
        )

        return {
            **resultado_xai,

            "paquete_auditoria":
                paquete,

            "prompt_super_agente":
                prompt_super_agente,

            "informe_auditoria_markdown":
                informe,

            "prompt_presentacion_notebooklm":
                prompt_notebooklm
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo generar el análisis completo. "
                f"Error: {str(error)}"
            )
        ) from error