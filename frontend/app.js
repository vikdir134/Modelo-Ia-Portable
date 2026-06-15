"use strict";

/* ============================================================
   REFERENCIAS PRINCIPALES
============================================================ */

const formulario = document.getElementById("formularioFraude");
const botonAnalizar = document.getElementById("botonAnalizar");
const botonLimpiar = document.getElementById("botonLimpiar");
const botonImportancia = document.getElementById("botonImportancia");

const mensajeFormulario = document.getElementById(
    "mensajeFormulario"
);

const seccionResultados = document.getElementById(
    "seccionResultados"
);

const estadoBackend = document.getElementById(
    "estadoBackend"
);


/* ============================================================
   VARIABLES CATEGÓRICAS
============================================================ */

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


/* ============================================================
   VALORES INICIALES
============================================================ */

function generarClaimId() {
    const fecha = Date.now();
    const aleatorio = Math.floor(
        Math.random() * 10000
    );

    return `CLAIM_APP_${fecha}_${aleatorio}`;
}


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


function establecerValoresIniciales() {
    document.getElementById(
        "Claim_ID"
    ).value = generarClaimId();

    document.getElementById(
        "Claim_Submission_Date"
    ).value = obtenerFechaLocal();
}


/* ============================================================
   RESPUESTAS DEL BACKEND
============================================================ */

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
                mensaje = JSON.stringify(
                    datos.detail
                );
            }
        }

        throw new Error(mensaje);
    }

    return datos;
}


/* ============================================================
   VERIFICAR BACKEND
============================================================ */

async function verificarBackend() {
    try {
        const respuesta = await fetch(
            "/health"
        );

        const datos = await leerRespuesta(
            respuesta
        );

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

        console.error(
            "Error verificando backend:",
            error
        );

        return false;
    }
}


/* ============================================================
   CATÁLOGOS DEL MODELO
============================================================ */

function llenarSelector(id, opciones) {
    const selector = document.getElementById(id);

    selector.innerHTML = "";

    if (!Array.isArray(opciones) || opciones.length === 0) {
        const opcionVacia = document.createElement(
            "option"
        );

        opcionVacia.value = "";
        opcionVacia.textContent =
            "No hay opciones disponibles";

        opcionVacia.disabled = true;
        opcionVacia.selected = true;

        selector.appendChild(opcionVacia);

        return;
    }

    opciones.forEach((valor, indice) => {
        const opcion = document.createElement(
            "option"
        );

        opcion.value = String(valor);
        opcion.textContent = String(valor);

        if (indice === 0) {
            opcion.selected = true;
        }

        selector.appendChild(opcion);
    });
}


async function cargarCatalogos() {
    try {
        const respuesta = await fetch(
            "/catalogos"
        );

        const datos = await leerRespuesta(
            respuesta
        );

        const categorias =
            datos.categorias || {};

        camposCatalogos.forEach((campo) => {
            llenarSelector(
                campo,
                categorias[campo] || []
            );
        });

    } catch (error) {
        mensajeFormulario.textContent =
            "No se pudieron cargar las categorías del modelo.";

        mensajeFormulario.className =
            "error";

        console.error(
            "Error cargando catálogos:",
            error
        );
    }
}


/* ============================================================
   CREAR JSON PARA FASTAPI
============================================================ */

function construirPayload() {
    return {
        Provider_ID: document
            .getElementById("Provider_ID")
            .value
            .trim(),

        Claim_ID: document
            .getElementById("Claim_ID")
            .value
            .trim(),

        Patient_Age: Number(
            document.getElementById(
                "Patient_Age"
            ).value
        ),

        Patient_Gender: document
            .getElementById(
                "Patient_Gender"
            ).value,

        Diagnosis_Code: document
            .getElementById(
                "Diagnosis_Code"
            ).value,

        Procedure_Code: document
            .getElementById(
                "Procedure_Code"
            ).value,

        Claim_Amount: Number(
            document.getElementById(
                "Claim_Amount"
            ).value
        ),

        Approved_Amount: Number(
            document.getElementById(
                "Approved_Amount"
            ).value
        ),

        Insurance_Type: document
            .getElementById(
                "Insurance_Type"
            ).value,

        Provider_Specialty: document
            .getElementById(
                "Provider_Specialty"
            ).value,

        Patient_State: document
            .getElementById(
                "Patient_State"
            ).value,

        Claim_Submission_Date: document
            .getElementById(
                "Claim_Submission_Date"
            ).value,

        Days_Between_Service_and_Claim: Number(
            document.getElementById(
                "Days_Between_Service_and_Claim"
            ).value
        ),

        Number_of_Claims_Per_Provider_Monthly: Number(
            document.getElementById(
                "Number_of_Claims_Per_Provider_Monthly"
            ).value
        ),

        Claim_Status: document
            .getElementById(
                "Claim_Status"
            ).value,

        Length_of_Stay: Number(
            document.getElementById(
                "Length_of_Stay"
            ).value
        ),

        Chronic_Condition_Flag: Number(
            document.getElementById(
                "Chronic_Condition_Flag"
            ).value
        ),

        Prior_Visits_12m: Number(
            document.getElementById(
                "Prior_Visits_12m"
            ).value
        ),

        Visit_Type: document
            .getElementById(
                "Visit_Type"
            ).value
    };
}


/* ============================================================
   FORMATEAR VALORES
============================================================ */

function formatoValor(valor) {
    if (
        valor === null
        || valor === undefined
        || valor === ""
    ) {
        return "No disponible";
    }

    if (typeof valor === "number") {
        if (Number.isInteger(valor)) {
            return String(valor);
        }

        return valor.toFixed(4);
    }

    return String(valor);
}


/* ============================================================
   MOSTRAR FACTORES SHAP
============================================================ */

function mostrarFactores(
    idTabla,
    factores
) {
    const cuerpoTabla = document.getElementById(
        idTabla
    );

    cuerpoTabla.innerHTML = "";

    if (
        !Array.isArray(factores)
        || factores.length === 0
    ) {
        const fila = document.createElement(
            "tr"
        );

        const celda = document.createElement(
            "td"
        );

        celda.colSpan = 3;

        celda.textContent =
            "No se identificaron factores destacados.";

        fila.appendChild(celda);
        cuerpoTabla.appendChild(fila);

        return;
    }

    factores.forEach((factor) => {
        const fila = document.createElement(
            "tr"
        );

        const celdaVariable =
            document.createElement("td");

        const celdaValor =
            document.createElement("td");

        const celdaImpacto =
            document.createElement("td");

        celdaVariable.textContent =
            factor.variable || "No disponible";

        celdaValor.textContent =
            formatoValor(factor.valor);

        const impacto = Number(
            factor.impacto_shap
        );

        celdaImpacto.textContent =
            Number.isFinite(impacto)
                ? impacto.toFixed(6)
                : "No disponible";

        fila.appendChild(celdaVariable);
        fila.appendChild(celdaValor);
        fila.appendChild(celdaImpacto);

        cuerpoTabla.appendChild(fila);
    });
}


/* ============================================================
   NIVEL DE RIESGO
============================================================ */

function claseRiesgo(nivel) {
    const valor = String(
        nivel || ""
    )
        .toLowerCase()
        .normalize("NFD")
        .replace(
            /[\u0300-\u036f]/g,
            ""
        );

    if (valor === "bajo") {
        return "riesgo-bajo";
    }

    if (valor === "moderado") {
        return "riesgo-moderado";
    }

    if (valor === "alto") {
        return "riesgo-alto";
    }

    return "riesgo-critico";
}


/* ============================================================
   MOSTRAR RESULTADO COMPLETO
============================================================ */

function mostrarResultado(datos) {
    const probabilidad = Number(
        datos.probabilidad_fraude
    );

    if (!Number.isFinite(probabilidad)) {
        throw new Error(
            "El backend no devolvió una probabilidad válida."
        );
    }

    document.getElementById(
        "resultadoClasificacion"
    ).textContent =
        datos.prediccion_texto || "No disponible";

    document.getElementById(
        "resultadoProbabilidad"
    ).textContent =
        `${(probabilidad * 100).toFixed(2)} %`;

    document.getElementById(
        "resultadoRiesgo"
    ).textContent =
        datos.nivel_riesgo || "No disponible";

    document.getElementById(
        "resultadoUmbral"
    ).textContent =
        Number(datos.umbral ?? 0.5).toFixed(2);

    document.getElementById(
        "resultadoResumen"
    ).textContent =
        datos.resumen
        || "No se recibió una explicación.";

    const progreso = document.getElementById(
        "progresoRiesgo"
    );

    progreso.style.width =
        `${Math.min(
            Math.max(probabilidad * 100, 0),
            100
        )}%`;

    progreso.className = claseRiesgo(
        datos.nivel_riesgo
    );

    mostrarFactores(
        "tablaAumentan",
        datos.factores_aumentan_riesgo
    );

    mostrarFactores(
        "tablaReducen",
        datos.factores_reducen_riesgo
    );

    const imagen = document.getElementById(
        "imagenShap"
    );

    if (datos.grafico_shap_base64) {
        imagen.src =
            `data:image/png;base64,${datos.grafico_shap_base64}`;

        imagen.style.display = "block";
    } else {
        imagen.removeAttribute("src");
        imagen.style.display = "none";
    }

    /* Informe listo para NotebookLM */

    document.getElementById(
        "textoInforme"
    ).value =
        datos.informe_auditoria_markdown || "";

    /* Prompt con paquete, predicción y SHAP */

    document.getElementById(
        "textoPrompt"
    ).value =
        datos.prompt_super_agente || "";

    /* Instrucción para generar la PPT */

    document.getElementById(
        "textoNotebookLM"
    ).value =
        datos.prompt_presentacion_notebooklm || "";

    seccionResultados.classList.remove(
        "oculto"
    );

    seccionResultados.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


/* ============================================================
   ANALIZAR RECLAMACIÓN
============================================================ */

async function analizarReclamacion(evento) {
    evento.preventDefault();

    if (!formulario.checkValidity()) {
        formulario.reportValidity();
        return;
    }

    botonAnalizar.disabled = true;
    botonAnalizar.textContent =
        "Analizando...";

    mensajeFormulario.textContent =
        "Procesando reclamación con LightGBM, SHAP y el superagente...";

    mensajeFormulario.className = "";

    try {
        const payload = construirPayload();

        const respuesta = await fetch(
            "/analizar-completo",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify(
                    payload
                )
            }
        );

        const datos = await leerRespuesta(
            respuesta
        );

        mostrarResultado(datos);

        mensajeFormulario.textContent =
            "Análisis e informe generados correctamente.";

    } catch (error) {
        mensajeFormulario.textContent =
            error.message;

        mensajeFormulario.className =
            "error";

        console.error(
            "Error en el análisis:",
            error
        );

    } finally {
        botonAnalizar.disabled = false;

        botonAnalizar.textContent =
            "Analizar reclamación";
    }
}


/* ============================================================
   IMPORTANCIA GLOBAL
============================================================ */

async function cargarImportanciaGlobal() {
    const contenedor = document.getElementById(
        "importanciaGlobal"
    );

    contenedor.textContent =
        "Cargando importancia global...";

    try {
        const respuesta = await fetch(
            "/importancia-global"
        );

        const datos = await leerRespuesta(
            respuesta
        );

        const variables = (
            datos.variables || []
        ).slice(0, 15);

        contenedor.innerHTML = "";

        if (variables.length === 0) {
            contenedor.textContent =
                "No hay información disponible.";

            return;
        }

        const valores = variables.map(
            (elemento) =>
                Number(
                    elemento.Importancia_SHAP
                ) || 0
        );

        const maximo = Math.max(
            ...valores,
            0
        );

        variables.forEach((elemento) => {
            const fila = document.createElement(
                "div"
            );

            fila.className =
                "fila-importancia";

            const nombre = document.createElement(
                "div"
            );

            nombre.className =
                "nombre-importancia";

            nombre.textContent =
                elemento.Variable;

            nombre.title =
                elemento.Variable;

            const barraExterior =
                document.createElement("div");

            barraExterior.className =
                "barra-importancia";

            const barraInterior =
                document.createElement("div");

            const importancia = Number(
                elemento.Importancia_SHAP
            ) || 0;

            const porcentajeBarra =
                maximo > 0
                    ? importancia / maximo * 100
                    : 0;

            barraInterior.style.width =
                `${porcentajeBarra}%`;

            barraExterior.appendChild(
                barraInterior
            );

            const porcentaje = document.createElement(
                "div"
            );

            porcentaje.className =
                "valor-importancia";

            porcentaje.textContent =
                `${Number(
                    elemento.Importancia_Porcentual
                ).toFixed(2)} %`;

            fila.appendChild(nombre);
            fila.appendChild(barraExterior);
            fila.appendChild(porcentaje);

            contenedor.appendChild(fila);
        });

    } catch (error) {
        contenedor.innerHTML = "";

        const mensaje = document.createElement(
            "p"
        );

        mensaje.className = "error";
        mensaje.textContent = error.message;

        contenedor.appendChild(mensaje);

        console.error(
            "Error cargando importancia:",
            error
        );
    }
}


/* ============================================================
   MÉTRICAS DEL MODELO
============================================================ */

function crearTarjetaMetrica(
    nombre,
    valor
) {
    const tarjeta = document.createElement(
        "article"
    );

    tarjeta.className =
        "tarjeta-resultado";

    const etiqueta = document.createElement(
        "span"
    );

    etiqueta.textContent = nombre;

    const contenido = document.createElement(
        "strong"
    );

    if (
        typeof valor === "number"
        && valor >= 0
        && valor <= 1
    ) {
        contenido.textContent =
            `${(valor * 100).toFixed(2)} %`;
    } else {
        contenido.textContent =
            valor ?? "—";
    }

    tarjeta.appendChild(etiqueta);
    tarjeta.appendChild(contenido);

    return tarjeta;
}


async function cargarMetricasModelo() {
    const contenedor = document.getElementById(
        "metricasModelo"
    );

    try {
        const respuesta = await fetch(
            "/modelo"
        );

        const datos = await leerRespuesta(
            respuesta
        );

        const metricas =
            datos.metricas_prueba || {};

        contenedor.innerHTML = "";

        const tarjetas = [
            ["Modelo", datos.modelo || "LightGBM"],
            ["Accuracy", metricas.accuracy],
            ["Precision", metricas.precision],
            ["Recall", metricas.recall],
            ["F1-Score", metricas.f1_score],
            ["ROC-AUC", metricas.roc_auc]
        ];

        tarjetas.forEach(
            ([nombre, valor]) => {
                contenedor.appendChild(
                    crearTarjetaMetrica(
                        nombre,
                        valor ?? "—"
                    )
                );
            }
        );

    } catch (error) {
        contenedor.innerHTML = "";

        const mensaje = document.createElement(
            "p"
        );

        mensaje.className = "error";
        mensaje.textContent = error.message;

        contenedor.appendChild(mensaje);

        console.error(
            "Error cargando métricas:",
            error
        );
    }
}


/* ============================================================
   COPIAR INFORME Y PROMPTS
============================================================ */

async function copiarContenido(
    idCampo,
    idBoton
) {
    const campo = document.getElementById(
        idCampo
    );

    const boton = document.getElementById(
        idBoton
    );

    const texto = campo.value;

    if (!texto.trim()) {
        boton.textContent =
            "Sin contenido";

        setTimeout(() => {
            boton.textContent = "Copiar";
        }, 1500);

        return;
    }

    const textoOriginal =
        boton.textContent;

    try {
        await navigator.clipboard.writeText(
            texto
        );

        boton.textContent = "Copiado";

    } catch {
        campo.focus();
        campo.select();

        document.execCommand("copy");

        boton.textContent = "Copiado";
    }

    setTimeout(() => {
        boton.textContent =
            textoOriginal;
    }, 1600);
}


/* ============================================================
   LIMPIAR FORMULARIO
============================================================ */

function limpiarFormulario() {
    formulario.reset();

    establecerValoresIniciales();

    seccionResultados.classList.add(
        "oculto"
    );

    mensajeFormulario.textContent = "";
    mensajeFormulario.className = "";

    document.getElementById(
        "textoInforme"
    ).value = "";

    document.getElementById(
        "textoPrompt"
    ).value = "";

    document.getElementById(
        "textoNotebookLM"
    ).value = "";

    document.getElementById(
        "tablaAumentan"
    ).innerHTML = "";

    document.getElementById(
        "tablaReducen"
    ).innerHTML = "";

    const imagen = document.getElementById(
        "imagenShap"
    );

    imagen.removeAttribute("src");
    imagen.style.display = "none";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* ============================================================
   EVENTOS
============================================================ */

formulario.addEventListener(
    "submit",
    analizarReclamacion
);

botonLimpiar.addEventListener(
    "click",
    limpiarFormulario
);

botonImportancia.addEventListener(
    "click",
    cargarImportanciaGlobal
);

document.getElementById(
    "botonCopiarInforme"
).addEventListener(
    "click",
    () => copiarContenido(
        "textoInforme",
        "botonCopiarInforme"
    )
);

document.getElementById(
    "botonCopiarPrompt"
).addEventListener(
    "click",
    () => copiarContenido(
        "textoPrompt",
        "botonCopiarPrompt"
    )
);

document.getElementById(
    "botonCopiarNotebookLM"
).addEventListener(
    "click",
    () => copiarContenido(
        "textoNotebookLM",
        "botonCopiarNotebookLM"
    )
);


/* ============================================================
   INICIAR APLICACIÓN
============================================================ */

async function iniciarAplicacion() {
    establecerValoresIniciales();

    const backendActivo =
        await verificarBackend();

    if (!backendActivo) {
        mensajeFormulario.textContent =
            "El backend no está activo. Ejecuta iniciar_sistema.bat.";

        mensajeFormulario.className =
            "error";

        return;
    }

    await cargarCatalogos();

    await Promise.all([
        cargarImportanciaGlobal(),
        cargarMetricasModelo()
    ]);
}


iniciarAplicacion();