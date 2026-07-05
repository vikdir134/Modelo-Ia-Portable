from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


TRADUCCIONES_VARIABLES = {
    "Patient_Age": "edad del paciente",
    "Patient_Gender": "género del paciente",
    "Diagnosis_Code": "código de diagnóstico",
    "Procedure_Code": "código de procedimiento",
    "Claim_Amount": "monto reclamado",
    "Approved_Amount": "monto aprobado",
    "Insurance_Type": "tipo de seguro",
    "Provider_Specialty": "especialidad del proveedor",
    "Patient_State": "estado del paciente",
    "Claim_Status": "estado de la reclamación",
    "Visit_Type": "tipo de visita",
    "Length_of_Stay": "duración de la estancia",
    "Chronic_Condition_Flag": "condición crónica",
    "Prior_Visits_12m": "visitas previas en 12 meses",
    "Days_Between_Service_and_Claim": "días entre el servicio y la reclamación",
    "Number_of_Claims_Per_Provider_Monthly": "reclamaciones mensuales del proveedor",
    "Submission_Month": "mes de presentación",
    "Submission_Year": "año de presentación",
    "Approval_Ratio": "proporción aprobada",
    "Amount_Diff": "diferencia entre monto reclamado y aprobado"
}


TRADUCCIONES_VALORES = {
    "Female": "femenino",
    "Male": "masculino",
    "Emergency": "emergencia",
    "Inpatient": "hospitalización",
    "Outpatient": "consulta externa",
    "Approved": "aprobada",
    "Pending": "pendiente",
    "Rejected": "rechazada",
    "Private": "seguro privado",
    "Self-Pay": "pago particular",
    "Cardiology": "cardiología",
    "General Practice": "medicina general",
    "Internal Medicine": "medicina interna",
    "Neurology": "neurología",
    "Orthopedics": "ortopedia",
    "Pulmonology": "neumología",
    "PA": "Pensilvania",
    "CA": "California",
    "FL": "Florida",
    "GA": "Georgia",
    "IL": "Illinois",
    "NY": "Nueva York",
    "OH": "Ohio",
    "TX": "Texas"
}


def gemini_disponible() -> bool:
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def traducir_texto_tecnico(valor: Any) -> Any:
    """
    Traduce nombres técnicos antes de enviarlos a Gemini.
    Así evitamos que Gemini escriba Approval_Ratio, Claim_Amount, etc.
    """

    if isinstance(valor, str):
        texto = valor

        for ingles, espanol in TRADUCCIONES_VARIABLES.items():
            texto = texto.replace(ingles, espanol)

        for ingles, espanol in TRADUCCIONES_VALORES.items():
            texto = texto.replace(ingles, espanol)

        return texto

    if isinstance(valor, list):
        return [
            traducir_texto_tecnico(item)
            for item in valor
        ]

    if isinstance(valor, dict):
        return {
            clave: traducir_texto_tecnico(contenido)
            for clave, contenido in valor.items()
        }

    return valor


def extraer_json_desde_texto(texto: str) -> dict:
    """
    Gemini puede devolver JSON puro o JSON dentro de ```json.
    Esta función limpia la respuesta antes de hacer json.loads().
    """

    texto = texto.strip()

    texto = re.sub(
        r"^```json\s*",
        "",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"^```\s*",
        "",
        texto
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto
    )

    return json.loads(texto)


def construir_prompt_narrativas(
    slides: list[dict[str, Any]]
) -> str:
    datos_resumidos = []

    for slide in slides:
        datos_resumidos.append({
            "id": slide.get("id"),
            "tipo": slide.get("tipo"),
            "titulo": slide.get("titulo"),
            "datos": traducir_texto_tecnico(
                slide.get("datos")
            )
        })

    return f"""
Eres un agente redactor y analista dentro de un Sistema Multiagente
de auditoría médica.

Tu tarea es generar narrativas breves, profesionales y explicativas
para un dossier de posible fraude en reclamaciones de seguros de salud.

Objetivo:
No solo describas los datos. Explica por qué el resultado puede ser
una señal de alerta para auditoría humana, usando los factores del modelo.

Reglas obligatorias:
- Escribe absolutamente todo en español.
- No uses nombres técnicos en inglés.
- No escribas Approval_Ratio, Amount_Diff, Claim_Amount, Claim_Status,
  Days_Between_Service_and_Claim ni Provider_Specialty.
- Usa nombres entendibles como proporción aprobada, monto reclamado,
  estado de la reclamación, especialidad del proveedor y días entre
  el servicio y la reclamación.
- No afirmes que existe fraude confirmado.
- Usa términos como riesgo estimado, posible fraude, señal de alerta,
  revisión humana o auditoría especializada.
- No inventes datos.
- No cambies probabilidades, montos, códigos ni niveles de riesgo.
- Cada narrativa debe tener entre 25 y 45 palabras.
- El estilo debe ser claro, ejecutivo y entendible para una exposición.
- Devuelve únicamente JSON válido.
- No uses Markdown.
- No uses bloques ```json.

Formato exacto de salida:
{{
  "narrativas": [
    {{
      "id": "riesgo-principal",
      "narrativa": "texto explicativo breve"
    }}
  ]
}}

Diapositivas:
{json.dumps(datos_resumidos, ensure_ascii=False, indent=2)}
""".strip()


def enriquecer_slides_con_gemini(
    slides: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    """
    Reemplaza las narrativas base por narrativas generadas
    por Gemini. Si falla, conserva las narrativas locales.
    """

    if not gemini_disponible():
        print(
            "Gemini no disponible: falta GEMINI_API_KEY o GOOGLE_API_KEY."
        )
        return slides, "Local"

    try:
        print("Gemini disponible. Generando narrativas explicativas...")

        client = genai.Client()

        prompt = construir_prompt_narrativas(
            slides
        )

        respuesta = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        texto = respuesta.text or ""

        print("Respuesta cruda de Gemini:")
        print(texto[:1000])

        datos = extraer_json_desde_texto(
            texto
        )

        narrativas = {
            item["id"]: item["narrativa"]
            for item in datos.get("narrativas", [])
            if "id" in item and "narrativa" in item
        }

        print(
            "Narrativas recibidas:",
            len(narrativas)
        )

        if not narrativas:
            print(
                "Gemini respondió, pero no devolvió narrativas válidas."
            )
            return slides, "Local"

        slides_enriquecidas = []

        for slide in slides:
            copia = dict(slide)

            if copia.get("id") in narrativas:
                copia["narrativa"] = narrativas[
                    copia["id"]
                ]

            slides_enriquecidas.append(copia)

        print(
            "Narrativas aplicadas correctamente con Gemini."
        )

        return slides_enriquecidas, "Gemini"

    except Exception as error:
        print("Gemini falló dentro del dossier:")
        print(type(error).__name__)
        print(str(error))

        return slides, "Local"