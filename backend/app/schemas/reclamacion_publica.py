from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from api_lightgbm import ReclamacionEntrada


class ReclamacionPublicaEntrada(BaseModel):
    """
    Entrada simplificada para el frontend.

    No solicita Provider_ID ni Claim_ID porque esos
    datos son técnicos y se generan automáticamente.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )

    Patient_Age: int = Field(
        ge=0,
        le=120,
        description="Edad del paciente"
    )

    Patient_Gender: str = Field(
        min_length=1,
        description="Género del paciente"
    )

    Diagnosis_Code: str = Field(
        min_length=1,
        description="Código de diagnóstico"
    )

    Procedure_Code: str = Field(
        min_length=1,
        description="Código de procedimiento"
    )

    Claim_Amount: float = Field(
        gt=0,
        description="Monto reclamado"
    )

    Approved_Amount: float = Field(
        ge=0,
        description="Monto aprobado"
    )

    Insurance_Type: str = Field(
        min_length=1,
        description="Tipo de seguro"
    )

    Provider_Specialty: str = Field(
        min_length=1,
        description="Especialidad del proveedor"
    )

    Patient_State: str = Field(
        min_length=1,
        description="Estado del paciente"
    )

    Claim_Submission_Date: date = Field(
        description="Fecha de presentación"
    )

    Days_Between_Service_and_Claim: int = Field(
        ge=0,
        description="Días entre servicio y reclamación"
    )

    Number_of_Claims_Per_Provider_Monthly: int = Field(
        ge=0,
        description="Reclamaciones mensuales del proveedor"
    )

    Claim_Status: str = Field(
        min_length=1,
        description="Estado de la reclamación"
    )

    Length_of_Stay: int = Field(
        ge=0,
        description="Duración de estancia"
    )

    Chronic_Condition_Flag: Literal[0, 1] = Field(
        description="Condición crónica"
    )

    Prior_Visits_12m: int = Field(
        ge=0,
        description="Visitas previas en 12 meses"
    )

    Visit_Type: str = Field(
        min_length=1,
        description="Tipo de visita"
    )


def convertir_publica_a_modelo(
    entrada: ReclamacionPublicaEntrada
) -> ReclamacionEntrada:
    """
    Convierte la entrada simple del usuario al formato exacto
    que espera el modelo entrenado.
    """

    datos = entrada.model_dump()

    return ReclamacionEntrada(
        Provider_ID="PROVIDER_AUTO",
        Claim_ID=f"CLAIM_{uuid4().hex[:12].upper()}",
        **datos
    )