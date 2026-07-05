"use strict";

async function leerRespuesta(respuesta) {
    let datos = null;

    try {
        datos = await respuesta.json();
    } catch {
        datos = null;
    }

    if (!respuesta.ok) {
        let mensaje = `Error HTTP ${respuesta.status}`;

        if (datos && datos.detail) {
            if (typeof datos.detail === "string") {
                mensaje = datos.detail;
            } else {
                mensaje = JSON.stringify(datos.detail);
            }
        }

        throw new Error(mensaje);
    }

    return datos;
}


async function apiGet(ruta) {
    const respuesta = await fetch(
        `${window.API_BASE_URL}${ruta}`
    );

    return leerRespuesta(respuesta);
}


async function apiPost(ruta, payload) {
    const respuesta = await fetch(
        `${window.API_BASE_URL}${ruta}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }
    );

    return leerRespuesta(respuesta);
}


async function obtenerEstadoBackend() {
    return apiGet("/api/health");
}


async function obtenerCatalogos() {
    return apiGet("/api/catalogos");
}


async function analizarDossier(payload) {
    return apiPost(
        "/api/analisis/dossier",
        payload
    );
}