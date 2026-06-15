
import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin


class FeatureEngineeringFraude(
    BaseEstimator,
    TransformerMixin
):
    """
    Crea las variables utilizadas por el modelo
    de detección de fraude.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):

        datos = X.copy()

        # Convertir fecha
        fecha = pd.to_datetime(
            datos["Claim_Submission_Date"],
            errors="coerce"
        )

        # Variables derivadas de la fecha
        datos["Submission_Month"] = fecha.dt.month
        datos["Submission_Year"] = fecha.dt.year

        # Convertir importes a valores numéricos
        claim_amount = pd.to_numeric(
            datos["Claim_Amount"],
            errors="coerce"
        )

        approved_amount = pd.to_numeric(
            datos["Approved_Amount"],
            errors="coerce"
        )

        datos["Claim_Amount"] = claim_amount
        datos["Approved_Amount"] = approved_amount

        # Evitar división entre cero
        denominador = claim_amount.replace(
            0,
            np.nan
        )

        # Ingeniería de características
        datos["Approval_Ratio"] = (
            approved_amount / denominador
        )

        datos["Amount_Diff"] = (
            claim_amount - approved_amount
        )

        datos["Approval_Ratio"] = (
            datos["Approval_Ratio"]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
        )

        # Procedure_Code como variable categórica
        if "Procedure_Code" in datos.columns:

            datos["Procedure_Code"] = (
                datos["Procedure_Code"]
                .apply(
                    lambda valor:
                    str(valor)
                    if pd.notna(valor)
                    else np.nan
                )
            )

        # Eliminar identificadores y fecha original
        columnas_eliminar = [
            "Provider_ID",
            "Claim_ID",
            "Claim_Submission_Date"
        ]

        datos = datos.drop(
            columns=columnas_eliminar,
            errors="ignore"
        )

        return datos
