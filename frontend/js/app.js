"use strict";

const formulario = document.getElementById("formularioFraude");
const botonAnalizar = document.getElementById("botonAnalizar");
const botonLimpiar = document.getElementById("botonLimpiar");
const botonDetalleTecnico = document.getElementById("botonDetalleTecnico");

const mensajeFormulario = document.getElementById("mensajeFormulario");
const estadoBackend = document.getElementById("estadoBackend");
const seccionDossier = document.getElementById("seccionDossier");
const detalleTecnico = document.getElementById("detalleTecnico");

const camposCatalogos = [
    "Patient_Gender",
    "Diagnosis_Code",
    "Procedure_Code",
    "Insurance_Type",
    "Provider_Specialty",
    "Patient_State",
    "Claim_Status",
    "Visit_Type"
];


function obtenerFechaLocal() {
    const fecha = new Date();

    const anio = fecha.getFullYear();

    const mes = String(
        fecha.getMonth() + 1
    ).padStart(2, "0");

    const dia = String(
        fecha.getDate()
    ).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;
}


function establecerFechaInicial() {
    document.getElementById(
        "Claim_Submission_Date"
    ).value = obtenerFechaLocal();
}


function llenarSelector(id, opciones) {
    const selector = document.getElementById(id);

    selector.innerHTML = "";

    if (!Array.isArray(opciones) || opciones.length === 0) {
        const opcion = document.createElement("option");

        opcion.value = "";
        opcion.textContent = "No hay opciones disponibles";
        opcion.disabled = true;
        opcion.selected = true;

        selector.appendChild(opcion);

        return;
    }

    opciones.forEach((valor, indice) => {
        const opcion = document.createElement("option");

        /*
            IMPORTANTE:
            value mantiene el dato original para el modelo.
            textContent muestra el dato traducido al usuario.
        */
        opcion.value = String(valor);
        opcion.textContent = traducirValor(valor);

        if (indice === 0) {
            opcion.selected = true;
        }

        selector.appendChild(opcion);
    });
}

async function verificarBackend() {
    try {
        const datos = await obtenerEstadoBackend();

        estadoBackend.textContent =
            `Backend activo · ${datos.modelo || "LightGBM"}`;

        estadoBackend.className =
            "estado estado-ok";

        return true;

    } catch (error) {
        estadoBackend.textContent =
            "Backend no disponible";

        estadoBackend.className =
            "estado estado-error";

        mensajeFormulario.textContent =
            "No se pudo conectar con el backend.";

        mensajeFormulario.className =
            "error";

        console.error(error);

        return false;
    }
}


async function cargarCatalogos() {
    const datos = await obtenerCatalogos();

    const categorias = datos.categorias || {};

    camposCatalogos.forEach((campo) => {
        llenarSelector(
            campo,
            categorias[campo] || []
        );
    });
}


function construirPayload() {
    return {
        Patient_Age: Number(
            document.getElementById("Patient_Age").value
        ),

        Patient_Gender:
            document.getElementById("Patient_Gender").value,

        Diagnosis_Code:
            document.getElementById("Diagnosis_Code").value,

        Procedure_Code:
            document.getElementById("Procedure_Code").value,

        Claim_Amount: Number(
            document.getElementById("Claim_Amount").value
        ),

        Approved_Amount: Number(
            document.getElementById("Approved_Amount").value
        ),

        Insurance_Type:
            document.getElementById("Insurance_Type").value,

        Provider_Specialty:
            document.getElementById("Provider_Specialty").value,

        Patient_State:
            document.getElementById("Patient_State").value,

        Claim_Submission_Date:
            document.getElementById("Claim_Submission_Date").value,

        Days_Between_Service_and_Claim: Number(
            document
                .getElementById("Days_Between_Service_and_Claim")
                .value
        ),

        Number_of_Claims_Per_Provider_Monthly: Number(
            document
                .getElementById("Number_of_Claims_Per_Provider_Monthly")
                .value
        ),

        Claim_Status:
            document.getElementById("Claim_Status").value,

        Length_of_Stay: Number(
            document.getElementById("Length_of_Stay").value
        ),

        Chronic_Condition_Flag: Number(
            document.getElementById("Chronic_Condition_Flag").value
        ),

        Prior_Visits_12m: Number(
            document.getElementById("Prior_Visits_12m").value
        ),

        Visit_Type:
            document.getElementById("Visit_Type").value
    };
}


async function manejarAnalisis(evento) {
    evento.preventDefault();

    if (!formulario.checkValidity()) {
        formulario.reportValidity();
        return;
    }

    botonAnalizar.disabled = true;
    botonAnalizar.textContent = "Analizando con IA...";

    mensajeFormulario.textContent =
        "Ejecutando agentes SMA: preprocesamiento, LightGBM, SHAP y auditoría...";

    mensajeFormulario.className = "cargando";

    try {
        const payload = construirPayload();

        const dossier = await analizarDossier(
            payload
        );

        renderizarDossier(dossier);

        renderizarDetalleTecnico(dossier);

        seccionDossier.classList.remove("oculto");

        detalleTecnico.classList.add("oculto");

        mensajeFormulario.textContent =
            `Dossier generado correctamente. Narrativas: ${dossier.narrativa_generada_por || "Local"}.`;
            mensajeFormulario.className = "exito";

        seccionDossier.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        mensajeFormulario.textContent =
            error.message;

        mensajeFormulario.className =
            "error";

        console.error(error);

    } finally {
        botonAnalizar.disabled = false;
        botonAnalizar.textContent = "Generar dossier";
    }
}


function limpiarFormulario() {
    formulario.reset();

    establecerFechaInicial();

    seccionDossier.classList.add("oculto");
    detalleTecnico.classList.add("oculto");

    document.getElementById(
        "contenedorDossier"
    ).innerHTML = "";

    mensajeFormulario.textContent = "";
    mensajeFormulario.className = "";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function alternarDetalleTecnico() {
    detalleTecnico.classList.toggle("oculto");

    if (detalleTecnico.classList.contains("oculto")) {
        botonDetalleTecnico.textContent =
            "Ver detalle técnico XAI";
    } else {
        botonDetalleTecnico.textContent =
            "Ocultar detalle técnico XAI";
    }
}


async function iniciarAplicacion() {
    establecerFechaInicial();

    const backendActivo =
        await verificarBackend();

    if (!backendActivo) {
        return;
    }

    try {
        await cargarCatalogos();
    } catch (error) {
        mensajeFormulario.textContent =
            "No se pudieron cargar los catálogos del modelo.";

        mensajeFormulario.className =
            "error";

        console.error(error);
    }
}


formulario.addEventListener(
    "submit",
    manejarAnalisis
);

botonLimpiar.addEventListener(
    "click",
    limpiarFormulario
);

botonDetalleTecnico.addEventListener(
    "click",
    alternarDetalleTecnico
);

iniciarAplicacion();