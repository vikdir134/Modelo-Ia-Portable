
from __future__ import annotations

import base64
import io
from typing import Any

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap


class ExplicadorFraudeLightGBM:
    """
    Explica predicciones de un Pipeline compuesto por:

    1. feature_engineering
    2. preprocessor
    3. classifier LightGBM
    """

    def __init__(
        self,
        pipeline,
        umbral: float = 0.50
    ):
        self.pipeline = pipeline
        self.umbral = float(umbral)

        pasos = pipeline.named_steps

        pasos_requeridos = [
            "feature_engineering",
            "preprocessor",
            "classifier"
        ]

        faltantes = [
            paso
            for paso in pasos_requeridos
            if paso not in pasos
        ]

        if faltantes:
            raise ValueError(
                "El pipeline no contiene los pasos: "
                + ", ".join(faltantes)
            )

        self.feature_engineering = pasos[
            "feature_engineering"
        ]

        self.preprocessor = pasos[
            "preprocessor"
        ]

        self.classifier = pasos[
            "classifier"
        ]

        self.nombres_transformados = list(
            self.preprocessor.get_feature_names_out()
        )

        self.variables_numericas = []
        self.variables_categoricas = []

        for nombre, _, columnas in (
            self.preprocessor.transformers_
        ):
            if nombre == "num":
                self.variables_numericas = list(
                    columnas
                )

            elif nombre == "cat":
                self.variables_categoricas = list(
                    columnas
                )

        # Explicador específico para modelos de árboles
        self.explainer = shap.TreeExplainer(
            self.classifier
        )

    # ========================================================
    # FUNCIONES INTERNAS
    # ========================================================

    @staticmethod
    def _convertir_valor_json(valor: Any):

        if valor is None:
            return None

        try:
            if pd.isna(valor):
                return None
        except Exception:
            pass

        if isinstance(valor, np.generic):
            return valor.item()

        if isinstance(valor, pd.Timestamp):
            return valor.isoformat()

        if isinstance(valor, (str, int, float, bool)):
            return valor

        return str(valor)

    def _transformar_registro(
        self,
        registro: pd.DataFrame
    ):
        """
        Aplica exactamente las transformaciones
        del pipeline hasta antes de LightGBM.
        """

        registro_ingenieria = (
            self.feature_engineering.transform(
                registro
            )
        )

        registro_transformado = (
            self.preprocessor.transform(
                registro_ingenieria
            )
        )

        if hasattr(
            registro_transformado,
            "toarray"
        ):
            registro_transformado = (
                registro_transformado.toarray()
            )

        registro_transformado = np.asarray(
            registro_transformado,
            dtype=float
        )

        return (
            registro_ingenieria,
            registro_transformado
        )

    def _obtener_valores_shap(
        self,
        datos_transformados: np.ndarray
    ):
        """
        Maneja diferentes formatos de salida de SHAP.
        """

        try:
            explicacion = self.explainer(
                datos_transformados,
                check_additivity=False
            )
        except TypeError:
            explicacion = self.explainer(
                datos_transformados
            )

        valores = np.asarray(
            explicacion.values
        )

        valores_base = np.asarray(
            explicacion.base_values
        )

        # Algunas versiones devuelven:
        # muestras x variables x clases
        if valores.ndim == 3:

            if valores.shape[-1] >= 2:
                valores = valores[:, :, 1]
            else:
                valores = valores[:, :, 0]

        # Una sola observación
        if valores.ndim == 1:
            valores = valores.reshape(1, -1)

        # Base por clase
        if valores_base.ndim == 2:

            if valores_base.shape[-1] >= 2:
                valores_base = valores_base[:, 1]
            else:
                valores_base = valores_base[:, 0]

        valores_base = np.asarray(
            valores_base
        ).reshape(-1)

        return valores, valores_base

    def _variable_original(
        self,
        nombre_transformado: str
    ) -> str:
        """
        Convierte nombres como:

        num__Claim_Amount
        cat__Claim_Status_Approved

        en la variable original.
        """

        if nombre_transformado.startswith(
            "num__"
        ):
            return nombre_transformado.replace(
                "num__",
                "",
                1
            )

        nombre_limpio = nombre_transformado.replace(
            "cat__",
            "",
            1
        )

        # Ordenar por longitud evita confundir
        # nombres que tengan prefijos parecidos.
        categorias_ordenadas = sorted(
            self.variables_categoricas,
            key=len,
            reverse=True
        )

        for variable in categorias_ordenadas:

            prefijo = variable + "_"

            if nombre_limpio.startswith(prefijo):
                return variable

        return nombre_limpio

    def _agrupar_valores_shap(
        self,
        valores_shap_fila: np.ndarray
    ) -> dict[str, float]:
        """
        Agrupa las columnas One-Hot dentro de
        su variable categórica original.
        """

        agrupados = {}

        for nombre, impacto in zip(
            self.nombres_transformados,
            valores_shap_fila
        ):
            variable = self._variable_original(
                nombre
            )

            agrupados[variable] = (
                agrupados.get(variable, 0.0)
                + float(impacto)
            )

        return agrupados

    @staticmethod
    def _nivel_riesgo(
        probabilidad: float
    ) -> str:

        if probabilidad < 0.30:
            return "Bajo"

        if probabilidad < 0.50:
            return "Moderado"

        if probabilidad < 0.80:
            return "Alto"

        return "Crítico"

    # ========================================================
    # EXPLICACIÓN INDIVIDUAL
    # ========================================================

    def explicar_registro(
        self,
        registro: pd.DataFrame,
        top_n: int = 8
    ) -> dict:

        if not isinstance(
            registro,
            pd.DataFrame
        ):
            raise TypeError(
                "El registro debe ser un DataFrame."
            )

        if len(registro) != 1:
            raise ValueError(
                "La explicación individual necesita "
                "exactamente un registro."
            )

        probabilidad_fraude = float(
            self.pipeline.predict_proba(
                registro
            )[0, 1]
        )

        probabilidad_legitimo = float(
            1.0 - probabilidad_fraude
        )

        prediccion = int(
            probabilidad_fraude
            >= self.umbral
        )

        (
            registro_ingenieria,
            registro_transformado
        ) = self._transformar_registro(
            registro
        )

        valores_shap, valores_base = (
            self._obtener_valores_shap(
                registro_transformado
            )
        )

        impactos_agrupados = (
            self._agrupar_valores_shap(
                valores_shap[0]
            )
        )

        factores = []

        for variable, impacto in (
            impactos_agrupados.items()
        ):

            valor_variable = None

            if variable in (
                registro_ingenieria.columns
            ):
                valor_variable = (
                    registro_ingenieria.iloc[0][
                        variable
                    ]
                )

            factores.append({
                "variable": variable,
                "valor": self._convertir_valor_json(
                    valor_variable
                ),
                "impacto_shap": round(
                    float(impacto),
                    8
                ),
                "impacto_absoluto": round(
                    abs(float(impacto)),
                    8
                ),
                "direccion": (
                    "Aumenta el riesgo"
                    if impacto > 0
                    else (
                        "Reduce el riesgo"
                        if impacto < 0
                        else "Sin impacto"
                    )
                )
            })

        factores_ordenados = sorted(
            factores,
            key=lambda elemento:
                elemento["impacto_absoluto"],
            reverse=True
        )

        factores_aumentan = sorted(
            [
                factor
                for factor in factores
                if factor["impacto_shap"] > 0
            ],
            key=lambda elemento:
                elemento["impacto_shap"],
            reverse=True
        )[:top_n]

        factores_reducen = sorted(
            [
                factor
                for factor in factores
                if factor["impacto_shap"] < 0
            ],
            key=lambda elemento:
                elemento["impacto_shap"]
        )[:top_n]

        principales_aumentan = [
            factor["variable"]
            for factor in factores_aumentan[:3]
        ]

        principales_reducen = [
            factor["variable"]
            for factor in factores_reducen[:3]
        ]

        texto_aumentan = (
            ", ".join(principales_aumentan)
            if principales_aumentan
            else "ninguna variable destacada"
        )

        texto_reducen = (
            ", ".join(principales_reducen)
            if principales_reducen
            else "ninguna variable destacada"
        )

        prediccion_texto = (
            "Fraude"
            if prediccion == 1
            else "Legítimo"
        )

        resumen = (
            f"El modelo clasificó la reclamación como "
            f"{prediccion_texto}, con una probabilidad "
            f"de fraude de {probabilidad_fraude:.2%}. "
            f"Los factores que más aumentaron el riesgo "
            f"fueron: {texto_aumentan}. "
            f"Los factores que más redujeron el riesgo "
            f"fueron: {texto_reducen}."
        )

        return {
            "modelo": "LightGBM",
            "prediccion": prediccion,
            "prediccion_texto": prediccion_texto,
            "probabilidad_fraude": round(
                probabilidad_fraude,
                8
            ),
            "probabilidad_legitimo": round(
                probabilidad_legitimo,
                8
            ),
            "umbral": self.umbral,
            "nivel_riesgo": self._nivel_riesgo(
                probabilidad_fraude
            ),
            "valor_base_shap": (
                round(
                    float(valores_base[0]),
                    8
                )
                if len(valores_base) > 0
                else None
            ),
            "factores_aumentan_riesgo":
                factores_aumentan,
            "factores_reducen_riesgo":
                factores_reducen,
            "todos_los_factores":
                factores_ordenados,
            "resumen": resumen,
            "nota_xai": (
                "Los valores SHAP indican dirección "
                "e intensidad del impacto en la salida "
                "interna del modelo. No representan "
                "directamente puntos porcentuales."
            )
        }

    # ========================================================
    # GRÁFICO INDIVIDUAL
    # ========================================================

    def grafico_local_base64(
        self,
        registro: pd.DataFrame,
        top_n: int = 10
    ) -> str:

        resultado = self.explicar_registro(
            registro,
            top_n=top_n
        )

        factores = resultado[
            "todos_los_factores"
        ][:top_n]

        factores = sorted(
            factores,
            key=lambda elemento:
                elemento["impacto_shap"]
        )

        nombres = [
            factor["variable"]
            for factor in factores
        ]

        impactos = [
            factor["impacto_shap"]
            for factor in factores
        ]

        figura, eje = plt.subplots(
            figsize=(9, 6)
        )

        eje.barh(
            nombres,
            impactos
        )

        eje.axvline(
            x=0,
            linewidth=1
        )

        eje.set_xlabel(
            "Impacto SHAP"
        )

        eje.set_ylabel(
            "Variable"
        )

        eje.set_title(
            "Explicación individual de la reclamación"
        )

        figura.tight_layout()

        memoria = io.BytesIO()

        figura.savefig(
            memoria,
            format="png",
            dpi=130,
            bbox_inches="tight"
        )

        plt.close(figura)

        memoria.seek(0)

        imagen_base64 = base64.b64encode(
            memoria.read()
        ).decode("utf-8")

        return imagen_base64

    # ========================================================
    # IMPORTANCIA GLOBAL
    # ========================================================

    def importancia_global(
        self,
        datos: pd.DataFrame,
        max_muestras: int = 500,
        random_state: int = 42
    ) -> pd.DataFrame:

        if len(datos) > max_muestras:
            muestra = datos.sample(
                n=max_muestras,
                random_state=random_state
            )
        else:
            muestra = datos.copy()

        _, datos_transformados = (
            self._transformar_registro(
                muestra
            )
        )

        valores_shap, _ = (
            self._obtener_valores_shap(
                datos_transformados
            )
        )

        importancia_transformada = np.mean(
            np.abs(valores_shap),
            axis=0
        )

        importancia_agrupada = {}

        for nombre, importancia in zip(
            self.nombres_transformados,
            importancia_transformada
        ):
            variable = self._variable_original(
                nombre
            )

            importancia_agrupada[variable] = (
                importancia_agrupada.get(
                    variable,
                    0.0
                )
                + float(importancia)
            )

        tabla = pd.DataFrame({
            "Variable": list(
                importancia_agrupada.keys()
            ),
            "Importancia_SHAP": list(
                importancia_agrupada.values()
            )
        })

        tabla = tabla.sort_values(
            by="Importancia_SHAP",
            ascending=False
        ).reset_index(drop=True)

        total = tabla[
            "Importancia_SHAP"
        ].sum()

        if total > 0:
            tabla["Importancia_Porcentual"] = (
                tabla["Importancia_SHAP"]
                / total
                * 100
            )
        else:
            tabla["Importancia_Porcentual"] = 0.0

        return tabla

    def guardar_grafico_global(
        self,
        tabla_importancia: pd.DataFrame,
        ruta: str,
        top_n: int = 15
    ) -> str:

        tabla_grafico = (
            tabla_importancia
            .head(top_n)
            .sort_values(
                by="Importancia_SHAP",
                ascending=True
            )
        )

        figura, eje = plt.subplots(
            figsize=(9, 7)
        )

        eje.barh(
            tabla_grafico["Variable"],
            tabla_grafico["Importancia_SHAP"]
        )

        eje.set_xlabel(
            "Media del valor SHAP absoluto"
        )

        eje.set_ylabel(
            "Variable"
        )

        eje.set_title(
            "Importancia global - LightGBM"
        )

        figura.tight_layout()

        figura.savefig(
            ruta,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(figura)

        return ruta
