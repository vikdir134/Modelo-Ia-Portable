from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# NOMBRES AMIGABLES DE LAS VARIABLES
# ============================================================

ETIQUETAS_VARIABLES = {
    "Provider_ID": "ID del proveedor",
    "Claim_ID": "ID de reclamación",
    "Patient_Age": "Edad del paciente",
    "Patient_Gender": "Género del paciente",
    "Diagnosis_Code": "Código de diagnóstico",
    "Procedure_Code": "Código de procedimiento",
    "Claim_Amount": "Monto reclamado",
    "Approved_Amount": "Monto aprobado",
    "Insurance_Type": "Tipo de seguro",
    "Provider_Specialty": "Especialidad del proveedor",
    "Patient_State": "Estado del paciente",
    "Claim_Submission_Date": "Fecha de presentación",
    "Days_Between_Service_and_Claim":
        "Días entre servicio y reclamación",
    "Number_of_Claims_Per_Provider_Monthly":
        "Reclamaciones mensuales del proveedor",
    "Claim_Status": "Estado de reclamación",
    "Length_of_Stay": "Duración de estancia",
    "Chronic_Condition_Flag": "Condición crónica",
    "Prior_Visits_12m":
        "Visitas durante los últimos 12 meses",
    "Visit_Type": "Tipo de visita",
    "Submission_Month": "Mes de presentación",
    "Submission_Year": "Año de presentación",
    "Approval_Ratio": "Proporción aprobada",
    "Amount_Diff":
        "Diferencia entre monto reclamado y aprobado"
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def es_faltante(valor: Any) -> bool:
    if valor is None:
        return True

    if isinstance(valor, str):
        return not valor.strip() or valor.lower() == "nan"

    try:
        resultado = pd.isna(valor)

        if isinstance(resultado, (bool, np.bool_)):
            return bool(resultado)

    except Exception:
        pass

    return False


def valor_json_seguro(valor: Any) -> Any:
    if es_faltante(valor):
        return None

    if isinstance(valor, np.generic):
        return valor.item()

    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()

    if isinstance(valor, (str, int, float, bool)):
        return valor

    return str(valor)


def texto_valor(valor: Any) -> str:
    if es_faltante(valor):
        return "No disponible"

    if isinstance(valor, float):
        return f"{valor:,.4f}"

    return str(valor)


def nombre_variable(variable: str) -> str:
    return ETIQUETAS_VARIABLES.get(
        variable,
        variable
    )


def escapar_markdown(valor: Any) -> str:
    return (
        texto_valor(valor)
        .replace("|", "\\|")
        .replace("\n", " ")
    )


# ============================================================
# CREAR PAQUETE DE AUDITORÍA
# ============================================================

def construir_paquete_auditoria(
    datos_reclamacion: dict,
    resultado_xai: dict
) -> dict:
    """
    Integra datos originales, variables derivadas,
    predicción LightGBM y explicación SHAP.
    """

    datos_limpios = {
        clave: valor_json_seguro(valor)
        for clave, valor in datos_reclamacion.items()
    }

    claim_amount = datos_limpios.get(
        "Claim_Amount"
    )

    approved_amount = datos_limpios.get(
        "Approved_Amount"
    )

    approval_ratio = None
    amount_diff = None

    if (
        claim_amount is not None
        and approved_amount is not None
    ):
        claim_amount = float(claim_amount)
        approved_amount = float(approved_amount)

        if claim_amount != 0:
            approval_ratio = (
                approved_amount / claim_amount
            )

        amount_diff = (
            claim_amount - approved_amount
        )

    fecha = pd.to_datetime(
        datos_limpios.get(
            "Claim_Submission_Date"
        ),
        errors="coerce"
    )

    submission_month = None
    submission_year = None

    if not pd.isna(fecha):
        submission_month = int(fecha.month)
        submission_year = int(fecha.year)

    variables_derivadas = {
        "Submission_Month":
            submission_month,

        "Submission_Year":
            submission_year,

        "Approval_Ratio":
            valor_json_seguro(approval_ratio),

        "Amount_Diff":
            valor_json_seguro(amount_diff)
    }

    datos_modelo = {
        **datos_limpios,
        **variables_derivadas
    }

    campos_faltantes = [
        clave
        for clave, valor in datos_limpios.items()
        if es_faltante(valor)
    ]

    transformaciones = [
        (
            "Conversión de Claim_Submission_Date "
            "en Submission_Month y Submission_Year."
        ),
        (
            "Cálculo de Approval_Ratio mediante "
            "Approved_Amount / Claim_Amount."
        ),
        (
            "Cálculo de Amount_Diff mediante "
            "Claim_Amount - Approved_Amount."
        ),
        (
            "Imputación de variables numéricas "
            "faltantes mediante la mediana."
        ),
        (
            "Imputación de variables categóricas "
            "faltantes mediante la categoría más frecuente."
        ),
        (
            "Codificación One-Hot de las "
            "variables categóricas."
        )
    ]

    return {
        "metadatos": {
            "sistema": (
                "Sistema Multiagente de apoyo "
                "a la auditoría médica"
            ),
            "modelo_predictivo": "LightGBM",
            "metodo_xai": "SHAP",
            "clase_positiva": "Posible fraude",
            "naturaleza_resultado": (
                "Apoyo a la decisión; "
                "no confirma fraude"
            )
        },

        "datos_reclamacion":
            datos_modelo,

        "calidad_datos": {
            "campos_faltantes":
                campos_faltantes,

            "cantidad_campos_faltantes":
                len(campos_faltantes),

            "transformaciones_aplicadas":
                transformaciones
        },

        "resultado_predictivo": {
            "prediccion":
                resultado_xai.get(
                    "prediccion_texto"
                ),

            "probabilidad_fraude":
                resultado_xai.get(
                    "probabilidad_fraude"
                ),

            "probabilidad_legitimo":
                resultado_xai.get(
                    "probabilidad_legitimo"
                ),

            "nivel_riesgo":
                resultado_xai.get(
                    "nivel_riesgo"
                ),

            "umbral":
                resultado_xai.get(
                    "umbral"
                )
        },

        "explicacion_xai": {
            "factores_aumentan_riesgo":
                resultado_xai.get(
                    "factores_aumentan_riesgo",
                    []
                ),

            "factores_reducen_riesgo":
                resultado_xai.get(
                    "factores_reducen_riesgo",
                    []
                ),

            "resumen":
                resultado_xai.get(
                    "resumen",
                    ""
                ),

            "nota":
                resultado_xai.get(
                    "nota_xai",
                    ""
                )
        }
    }


# ============================================================
# PROMPT DEL SUPERAGENTE
# ============================================================

def construir_prompt_super_agente(
    paquete: dict
) -> str:
    paquete_json = json.dumps(
        paquete,
        indent=2,
        ensure_ascii=False,
        allow_nan=False
    )

    return f"""
Actúa como un SUPER AGENTE de apoyo a la auditoría médica
dentro de un Sistema Multiagente basado en Machine Learning
e Inteligencia Artificial Explicable para la detección de
posible fraude en reclamaciones de seguros de salud.

Usa únicamente la información contenida en el paquete de
auditoría incluido al final de este mensaje. No inventes
datos, antecedentes clínicos, normativas ni explicaciones
que no estén respaldaladas por el paquete.

Tu función es coordinar los siguientes subagentes:

1. Agente de preprocesamiento y calidad de datos
- Revisa qué datos fueron usados.
- Identifica campos faltantes.
- Describe las transformaciones aplicadas.
- Advierte si la calidad de datos limita la interpretación.

2. Agente de análisis de factores de riesgo
- Identifica las señales que merecen revisión.
- Considera montos, proporción aprobada, diferencia de montos,
  frecuencia de reclamaciones, tipo de visita, estancia,
  visitas previas y condición crónica.
- No inventes umbrales ni reglas médicas.

3. Agente predictivo basado en Machine Learning
- Interpreta la predicción del modelo LightGBM.
- Explica la probabilidad estimada y el nivel de riesgo.
- No presentes la predicción como fraude confirmado.

4. Agente explicativo basado en XAI
- Interpreta los factores SHAP.
- Explica qué variables aumentan o reducen la salida del modelo.
- Aclara que SHAP explica el comportamiento del modelo y
  no demuestra causalidad.

5. Agente de apoyo a la auditoría
- Integra los resultados anteriores.
- Genera acciones concretas para revisión humana.
- Diferencia claramente predicción, explicación y recomendación.

Antes del informe, incluye una tabla titulada:

“Coordinación de subagentes del SMA”

con las columnas:

- Subagente
- Entrada utilizada
- Análisis realizado
- Salida generada

Genera después un informe con esta estructura:

# Informe de Auditoría de Reclamación Médica

1. Resumen ejecutivo
2. Datos principales de la reclamación
3. Análisis de factores de riesgo
4. Resultado del agente predictivo
5. Explicación del agente XAI
6. Evaluación integrada del superagente
7. Checklist para auditoría manual
8. Recomendación final
9. Limitaciones del sistema

Reglas obligatorias:

- No afirmes que existe fraude confirmado.
- Usa términos como riesgo, posible fraude,
  caso sospechoso o reclamación que requiere revisión.
- Indica que el sistema apoya la decisión,
  pero no reemplaza al auditor humano.
- Usa lenguaje académico y formal.
- No conviertas los valores SHAP directamente en porcentajes.
- No agregues información que no aparezca en el paquete.
- Señala explícitamente los campos faltantes.
- La recomendación debe ser proporcional al nivel de riesgo.

PAQUETE DE AUDITORÍA:

{paquete_json}
""".strip()


# ============================================================
# INFORME AUTOMÁTICO SIN LLM
# ============================================================

def generar_informe_markdown(
    paquete: dict
) -> str:
    datos = paquete["datos_reclamacion"]
    calidad = paquete["calidad_datos"]
    predictivo = paquete["resultado_predictivo"]
    xai = paquete["explicacion_xai"]

    probabilidad = float(
        predictivo.get(
            "probabilidad_fraude"
        ) or 0
    )

    nivel = str(
        predictivo.get(
            "nivel_riesgo"
        ) or "No determinado"
    )

    prediccion = str(
        predictivo.get(
            "prediccion"
        ) or "No determinada"
    )

    campos_faltantes = calidad.get(
        "campos_faltantes",
        []
    )

    if campos_faltantes:
        texto_faltantes = ", ".join(
            nombre_variable(campo)
            for campo in campos_faltantes
        )
    else:
        texto_faltantes = (
            "No se identificaron campos faltantes "
            "en la entrada recibida."
        )

    factores_aumentan = xai.get(
        "factores_aumentan_riesgo",
        []
    )

    factores_reducen = xai.get(
        "factores_reducen_riesgo",
        []
    )

    def filas_factores(factores: list) -> str:
        if not factores:
            return (
                "| No disponible | No disponible | "
                "No se identificó un impacto destacado |\n"
            )

        filas = []

        for factor in factores:
            filas.append(
                "| "
                + escapar_markdown(
                    nombre_variable(
                        factor.get(
                            "variable",
                            "Variable"
                        )
                    )
                )
                + " | "
                + escapar_markdown(
                    factor.get("valor")
                )
                + " | "
                + escapar_markdown(
                    factor.get(
                        "impacto_shap"
                    )
                )
                + " |"
            )

        return "\n".join(filas)

    orden_datos = [
        "Claim_ID",
        "Provider_ID",
        "Patient_Age",
        "Patient_Gender",
        "Diagnosis_Code",
        "Procedure_Code",
        "Claim_Amount",
        "Approved_Amount",
        "Approval_Ratio",
        "Amount_Diff",
        "Insurance_Type",
        "Provider_Specialty",
        "Patient_State",
        "Claim_Status",
        "Visit_Type",
        "Length_of_Stay",
        "Days_Between_Service_and_Claim",
        "Number_of_Claims_Per_Provider_Monthly",
        "Chronic_Condition_Flag",
        "Prior_Visits_12m",
        "Claim_Submission_Date"
    ]

    filas_datos = []

    for variable in orden_datos:
        if variable in datos:
            filas_datos.append(
                "| "
                + escapar_markdown(
                    nombre_variable(variable)
                )
                + " | "
                + escapar_markdown(
                    datos.get(variable)
                )
                + " |"
            )

    if nivel.lower() in [
        "crítico",
        "critico"
    ]:
        recomendacion = (
            "Priorizar la reclamación para una auditoría "
            "manual especializada antes de continuar con "
            "una decisión definitiva. Se recomienda revisar "
            "la documentación clínica, la coherencia de los "
            "códigos, los montos y el comportamiento del proveedor."
        )

    elif nivel.lower() == "alto":
        recomendacion = (
            "Enviar la reclamación a revisión manual reforzada, "
            "verificando los documentos justificativos, los montos, "
            "la frecuencia de reclamaciones y la coherencia entre "
            "diagnóstico, procedimiento y tipo de visita."
        )

    elif nivel.lower() == "moderado":
        recomendacion = (
            "Realizar una revisión selectiva antes de aprobar "
            "definitivamente la reclamación, concentrándose en "
            "los factores destacados por SHAP."
        )

    else:
        recomendacion = (
            "Continuar con el procedimiento habitual, manteniendo "
            "los controles normales y la posibilidad de revisión "
            "si aparecen nuevos antecedentes."
        )

    return f"""
# Coordinación de subagentes del SMA

| Subagente | Entrada utilizada | Análisis realizado | Salida generada |
|---|---|---|---|
| Preprocesamiento y calidad de datos | Campos originales y variables derivadas | Revisión de faltantes, tipos de datos, imputaciones e ingeniería de características | Resumen de calidad y transformaciones |
| Análisis de factores de riesgo | Montos, frecuencia, estancia, visita, antecedentes y variables SHAP | Identificación de elementos que merecen revisión | Señales relevantes para auditoría |
| Predictivo basado en Machine Learning | Variables preprocesadas de la reclamación | Clasificación mediante LightGBM | Predicción, probabilidad y nivel de riesgo |
| Explicativo basado en XAI | Modelo LightGBM y registro transformado | Cálculo e interpretación de valores SHAP | Factores que aumentan o reducen el riesgo |
| Apoyo a la auditoría | Resultados de todos los subagentes | Integración de evidencia predictiva y explicativa | Recomendación para el auditor humano |

# Informe de Auditoría de Reclamación Médica

## 1. Resumen ejecutivo

El sistema LightGBM clasificó la reclamación como **{prediccion}**,
con una probabilidad estimada de posible fraude de
**{probabilidad:.2%}** y un nivel de riesgo **{nivel}**.

Este resultado no confirma la existencia de fraude. Representa una
estimación automatizada destinada a apoyar la priorización y revisión
por parte de un auditor humano.

## 2. Datos principales de la reclamación

| Variable | Valor |
|---|---|
{chr(10).join(filas_datos)}

### Calidad de datos

{texto_faltantes}

El pipeline aplicó imputación de datos faltantes, codificación de
variables categóricas e ingeniería de características. Entre las
variables derivadas se encuentran `Approval_Ratio`, `Amount_Diff`,
`Submission_Month` y `Submission_Year`.

## 3. Análisis de factores de riesgo

La reclamación fue evaluada considerando los montos reclamado y
aprobado, la diferencia entre ambos importes, la proporción aprobada,
la frecuencia mensual de reclamaciones del proveedor, el tipo de
visita, la duración de la estancia, las visitas previas y la presencia
de una condición crónica.

Las señales consideradas relevantes son las identificadas por el
modelo y por los valores SHAP. Estas señales deben interpretarse como
elementos de priorización y no como evidencia concluyente de fraude.

## 4. Resultado del agente predictivo

- **Modelo:** LightGBM
- **Clasificación:** {prediccion}
- **Probabilidad estimada de posible fraude:** {probabilidad:.2%}
- **Nivel de riesgo:** {nivel}
- **Umbral de clasificación:** {texto_valor(predictivo.get("umbral"))}

La predicción indica el nivel de riesgo estimado por el modelo a partir
de los patrones aprendidos durante su entrenamiento.

## 5. Explicación del agente XAI

### Factores que aumentaron el riesgo estimado

| Variable | Valor observado | Impacto SHAP |
|---|---:|---:|
{filas_factores(factores_aumentan)}

### Factores que redujeron el riesgo estimado

| Variable | Valor observado | Impacto SHAP |
|---|---:|---:|
{filas_factores(factores_reducen)}

Los valores SHAP expresan la dirección y magnitud de la contribución
de cada variable a la salida interna de LightGBM. No representan
directamente porcentajes de fraude ni demuestran una relación causal.

## 6. Evaluación integrada del superagente

La evaluación integrada considera la probabilidad producida por
LightGBM, el nivel de riesgo y las variables destacadas por SHAP.
La reclamación debe analizarse priorizando los factores con mayor
impacto positivo y verificando si cuentan con respaldo documental,
clínico y administrativo suficiente.

El resultado del sistema debe contrastarse con políticas de la
aseguradora, documentación médica, historial del proveedor y criterio
profesional del auditor.

## 7. Checklist para auditoría manual

- [ ] Verificar la identidad y elegibilidad del paciente.
- [ ] Confirmar la autenticidad de la reclamación y del proveedor.
- [ ] Revisar la coherencia entre diagnóstico y procedimiento.
- [ ] Validar la documentación clínica que respalda el servicio.
- [ ] Comparar el monto reclamado con el monto aprobado.
- [ ] Revisar la diferencia y proporción de aprobación.
- [ ] Evaluar la frecuencia mensual de reclamaciones del proveedor.
- [ ] Revisar las fechas de servicio y presentación.
- [ ] Comprobar el estado administrativo de la reclamación.
- [ ] Contrastar el caso con reclamaciones históricas similares.
- [ ] Examinar los factores destacados por SHAP.
- [ ] Documentar la decisión final del auditor humano.

## 8. Recomendación final

{recomendacion}

La decisión final debe ser tomada por un auditor autorizado. El
sistema únicamente proporciona evidencia predictiva y explicativa
para apoyar la revisión.

## 9. Limitaciones del sistema

1. La predicción no constituye una confirmación de fraude.
2. SHAP explica el comportamiento del modelo, pero no demuestra causalidad.
3. El rendimiento observado puede variar en datos reales o futuros.
4. El modelo depende de la calidad y disponibilidad de las variables.
5. Variables como `Approved_Amount`, `Claim_Status`,
   `Approval_Ratio` y `Amount_Diff` podrían no estar disponibles
   antes de una decisión administrativa.
6. El modelo debe complementarse con revisión documental,
   criterio médico y políticas de auditoría.
""".strip()


# ============================================================
# PROMPT PARA NOTEBOOKLM
# ============================================================

def construir_prompt_notebooklm() -> str:
    return """
Utiliza el informe de auditoría proporcionado como única fuente y
genera una presentación académica y profesional de 10 diapositivas.

Estructura solicitada:

1. Título del caso y objetivo del sistema.
2. Descripción de la reclamación analizada.
3. Coordinación de subagentes del SMA.
4. Preprocesamiento y calidad de los datos.
5. Factores de riesgo observados.
6. Resultado predictivo del modelo LightGBM.
7. Explicación XAI mediante SHAP.
8. Evaluación integrada y checklist de auditoría.
9. Recomendación final y rol del auditor humano.
10. Limitaciones y conclusión.

Reglas:

- No afirmar que existe fraude confirmado.
- Usar los términos posible fraude, riesgo o caso sospechoso.
- Incluir tablas o gráficos cuando ayuden a explicar los resultados.
- Resaltar probabilidad, nivel de riesgo y factores SHAP.
- Diferenciar claramente predicción, explicación y recomendación.
- Usar un lenguaje académico, visual y conciso.
- No inventar información que no aparezca en el informe.
- Terminar indicando que el sistema apoya, pero no reemplaza,
  la decisión del auditor humano.
""".strip()