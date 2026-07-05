from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    APP_NAME,
    APP_VERSION,
    API_PREFIX,
    obtener_origenes_cors
)

from app.routers.health_router import (
    router as health_router
)

from app.routers.catalogos_router import (
    router as catalogos_router
)

from app.routers.dossier_router import (
    router as dossier_router
)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Backend del Sistema Multiagente para detección, "
        "explicación y auditoría de posibles fraudes en "
        "reclamaciones médicas."
    )
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_origenes_cors(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def inicio():
    return {
        "sistema": APP_NAME,
        "version": APP_VERSION,
        "estado": f"{API_PREFIX}/health",
        "catalogos": f"{API_PREFIX}/catalogos",
        "dossier": f"{API_PREFIX}/analisis/dossier",
        "documentacion": "/docs"
    }


app.include_router(
    health_router,
    prefix=API_PREFIX
)

app.include_router(
    catalogos_router,
    prefix=API_PREFIX
)

app.include_router(
    dossier_router,
    prefix=API_PREFIX
)