from __future__ import annotations

from typing import Any


def porcentaje(valor: float | int | None) -> str:
    if valor is None:
        return "No disponible"

    try:
        return f"{float(valor) * 100:.2f} %"
    except Exception:
        return "No disponible"


def dinero(valor: float | int | None) -> str:
    if valor is None:
        return "No disponible"

    try:
        return f"{float(valor):,.2f} USD"
    except Exception:
        return "No disponible"


def obtener_factor_principal(
    factores: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not factores:
        return None

    return factores[0]


def construir_dossier(
    paquete_auditoria: dict,
    resultado_xai: dict
) -> dict:
    """
    Construye una presentación tipo dossier en formato JSON.

    El frontend renderiza estas diapositivas con HTML y CSS.
    """

    datos = paquete_auditoria.get(
        "datos_reclamacion",
        {}
    )

    predictivo = paquete_auditoria.get(
        "resultado_predictivo",
        {}
    )

    calidad = paquete_auditoria.get(
        "calidad_datos",
        {}
    )

    xai = paquete_auditoria.get(
        "explicacion_xai",
        {}
    )

    probabilidad = predictivo.get(
        "probabilidad_fraude",
        0
    )

    nivel_riesgo = predictivo.get(
        "nivel_riesgo",
        "No determinado"
    )

    prediccion = predictivo.get(
        "prediccion",
        "No determinada"
    )

    factores_aumentan = xai.get(
        "factores_aumentan_riesgo",
        []
    )

    factor_1 = obtener_factor_principal(
        factores_aumentan
    )

    factor_2 = (
        factores_aumentan[1]
        if len(factores_aumentan) > 1
        else None
    )

    claim_amount = datos.get("Claim_Amount")
    approved_amount = datos.get("Approved_Amount")
    amount_diff = datos.get("Amount_Diff")

    campos_faltantes = calidad.get(
        "campos_faltantes",
        []
    )

    slides = [
        {
            "id": "riesgo-principal",
            "tipo": "portada_riesgo",
            "titulo": (
                "Dossier de intervención: "
                "reclamación médica con alerta de riesgo"
            ),
            "subtitulo": (
                "Alerta generada por el sistema predictivo. "
                "Requiere revisión humana según el nivel estimado."
            ),
            "datos": {
                "probabilidad": porcentaje(probabilidad),
                "nivel_riesgo": nivel_riesgo,
                "prediccion": prediccion,
                "estado": (
                    "Revisión manual recomendada"
                    if str(nivel_riesgo).lower() in [
                        "alto",
                        "crítico",
                        "critico"
                    ]
                    else "Revisión estándar recomendada"
                )
            },
            "narrativa": (
                "El sistema estimó el nivel de riesgo de la "
                "reclamación usando un modelo LightGBM. "
                "Este resultado no confirma fraude; solo prioriza "
                "el caso para revisión."
            )
        },
        {
            "id": "datos-clinicos",
            "tipo": "datos_clinicos",
            "titulo": "Datos principales del encuentro médico",
            "datos": {
                "edad": datos.get("Patient_Age"),
                "genero": datos.get("Patient_Gender"),
                "diagnostico": datos.get("Diagnosis_Code"),
                "procedimiento": datos.get("Procedure_Code"),
                "tipo_visita": datos.get("Visit_Type"),
                "estancia": datos.get("Length_of_Stay"),
                "proveedor_mensual": datos.get(
                    "Number_of_Claims_Per_Provider_Monthly"
                )
            },
            "narrativa": (
                "La reclamación se analiza combinando datos del "
                "paciente, códigos clínicos, características de la "
                "atención y comportamiento mensual del proveedor."
            )
        },
        {
            "id": "comparacion-financiera",
            "tipo": "comparacion_financiera",
            "titulo": (
                "Comparación financiera entre monto reclamado "
                "y monto aprobado"
            ),
            "datos": {
                "monto_reclamado": dinero(claim_amount),
                "monto_aprobado": dinero(approved_amount),
                "diferencia": dinero(amount_diff),
                "approval_ratio": datos.get("Approval_Ratio")
            },
            "narrativa": (
                "La relación entre monto reclamado y monto aprobado "
                "se usa como una señal financiera para identificar "
                "posibles discrepancias que ameritan revisión."
            )
        },
        {
            "id": "factores-shap",
            "tipo": "factores_shap",
            "titulo": (
                "Factores SHAP: variables que impulsan "
                "el riesgo estimado"
            ),
            "datos": {
                "factor_principal": factor_1,
                "factor_secundario": factor_2,
                "factores_aumentan": factores_aumentan[:5],
                "factores_reducen": xai.get(
                    "factores_reducen_riesgo",
                    []
                )[:5]
            },
            "narrativa": (
                "SHAP permite identificar qué variables tuvieron "
                "mayor influencia sobre la salida del modelo. "
                "Estos valores explican el comportamiento del modelo, "
                "pero no demuestran causalidad."
            )
        },
        {
            "id": "riesgo-integrado",
            "tipo": "riesgo_integrado",
            "titulo": (
                "Perfil de riesgo integrado y límites "
                "de interpretación"
            ),
            "datos": {
                "nivel_riesgo": nivel_riesgo,
                "campos_faltantes": campos_faltantes,
                "cantidad_faltantes": len(campos_faltantes),
                "resumen_xai": xai.get("resumen")
            },
            "narrativa": (
                "El análisis integrado combina la predicción, "
                "los factores SHAP y la calidad de datos. "
                "La falta de campos o contexto puede limitar "
                "la interpretación automática."
            )
        },
        {
            "id": "recomendacion",
            "tipo": "recomendacion",
            "titulo": "Mandato de acción para auditoría humana",
            "datos": {
                "recomendacion": (
                    "Retener o priorizar la reclamación para revisión "
                    "manual especializada antes de una decisión final."
                    if str(nivel_riesgo).lower() in [
                        "alto",
                        "crítico",
                        "critico"
                    ]
                    else (
                        "Continuar con revisión estándar, manteniendo "
                        "controles administrativos normales."
                    )
                ),
                "checklist": [
                    "Verificar coherencia entre diagnóstico y procedimiento.",
                    "Validar documentación clínica de respaldo.",
                    "Revisar diferencia entre monto reclamado y aprobado.",
                    "Evaluar frecuencia mensual del proveedor.",
                    "Documentar la decisión final del auditor humano."
                ]
            },
            "narrativa": (
                "La decisión final debe permanecer bajo responsabilidad "
                "del auditor humano. El sistema solo proporciona apoyo "
                "predictivo y explicativo."
            )
        }
    ]

    return {
        "titulo": "Dossier automático de auditoría médica",
        "modelo": "LightGBM",
        "metodo_xai": "SHAP",
        "probabilidad_fraude": probabilidad,
        "nivel_riesgo": nivel_riesgo,
        "slides": slides,
        "detalle_tecnico": {
            "resultado_xai": resultado_xai,
            "paquete_auditoria": paquete_auditoria
        }
    }