import os
import __main__
import joblib

from fraude_features import FeatureEngineeringFraude


# Permite cargar modelos guardados cuando la clase
# FeatureEngineeringFraude estaba definida en el notebook.
__main__.FeatureEngineeringFraude = FeatureEngineeringFraude


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

RUTA_ORIGINAL = os.path.join(
    BASE_DIR,
    "artefactos_lightgbm",
    "modelo_fraude_lightgbm.joblib"
)

RUTA_PORTABLE = os.path.join(
    BASE_DIR,
    "artefactos_lightgbm",
    "modelo_fraude_lightgbm_portable.joblib"
)


if not os.path.exists(RUTA_ORIGINAL):
    raise FileNotFoundError(
        f"No se encontró el modelo original:\n{RUTA_ORIGINAL}"
    )


print("Cargando modelo original...")

modelo = joblib.load(RUTA_ORIGINAL)

print("Modelo cargado:", type(modelo).__name__)


# Reemplazar el transformer por la clase importable
if hasattr(modelo, "named_steps"):

    if "feature_engineering" not in modelo.named_steps:
        raise RuntimeError(
            "El pipeline no contiene el paso feature_engineering."
        )

    modelo.set_params(
        feature_engineering=FeatureEngineeringFraude()
    )

else:
    raise RuntimeError(
        "El archivo cargado no parece ser un Pipeline."
    )


print("Guardando versión portable...")

joblib.dump(
    modelo,
    RUTA_PORTABLE,
    compress=3
)


# Verificación final
modelo_verificacion = joblib.load(
    RUTA_PORTABLE
)

print("\nConversión completada correctamente.")
print("Modelo portable guardado en:")
print(RUTA_PORTABLE)

print("\nPasos encontrados:")

for nombre, objeto in modelo_verificacion.named_steps.items():
    print(f"- {nombre}: {type(objeto).__name__}")