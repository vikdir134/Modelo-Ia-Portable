from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agente_auditoria import (
    construir_paquete_auditoria,
    construir_prompt_super_agente,
    generar_informe_markdown
)

from api_lightgbm import convertir_a_dataframe

from xai_lightgbm import ExplicadorFraudeLightGBM

from api_lightgbm import modelo

from app.services.gemini_service import (
    enriquecer_slides_con_gemini
)
from app.schemas.reclamacion_publica import (
    ReclamacionPublicaEntrada,
    convertir_publica_a_modelo
)

from app.agents.agente_dossier import (
    construir_dossier
)


router = APIRouter(
    prefix="/analisis",
    tags=["Análisis SMA"]
)


explicador = ExplicadorFraudeLightGBM(
    pipeline=modelo,
    umbral=0.50
)


@router.post("/dossier")
def analizar_dossier(
    entrada_publica: ReclamacionPublicaEntrada
):
    """
    Endpoint principal del SMA.

    Recibe datos entendibles, genera los IDs técnicos,
    ejecuta LightGBM, calcula SHAP y devuelve un dossier
    listo para ser renderizado por el frontend.
    """

    try:
        entrada_modelo = convertir_publica_a_modelo(
            entrada_publica
        )

        registro = convertir_a_dataframe(
            entrada_modelo
        )

        resultado_xai = explicador.explicar_registro(
            registro,
            top_n=8
        )

        resultado_xai["grafico_shap_base64"] = (
            explicador.grafico_local_base64(
                registro,
                top_n=10
            )
        )

        resultado_xai["claim_id"] = (
            entrada_modelo.Claim_ID
        )

        datos_reclamacion = entrada_modelo.model_dump(
            mode="json"
        )

        paquete = construir_paquete_auditoria(
            datos_reclamacion=datos_reclamacion,
            resultado_xai=resultado_xai
        )

        informe = generar_informe_markdown(
            paquete
        )

        prompt_super_agente = (
            construir_prompt_super_agente(
                paquete
            )
        )

        dossier = construir_dossier(
            paquete_auditoria=paquete,
            resultado_xai=resultado_xai
        )

        slides_enriquecidas, origen_narrativa = (
            enriquecer_slides_con_gemini(
                dossier["slides"]
            )
        )

        dossier["slides"] = slides_enriquecidas
        dossier["narrativa_generada_por"] = origen_narrativa

        dossier["informe_auditoria_markdown"] = informe
        dossier["prompt_super_agente"] = prompt_super_agente

        return dossier

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo generar el dossier SMA. "
                f"Error: {str(error)}"
            )
        ) from error