from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api_lightgbm import modelo


router = APIRouter(
    prefix="/catalogos",
    tags=["Catálogos"]
)


@router.get("")
def obtener_catalogos():
    """
    Obtiene las categorías aprendidas por el OneHotEncoder.
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