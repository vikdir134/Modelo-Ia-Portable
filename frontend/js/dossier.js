"use strict";

/*
    Renderizador del dossier SMA.
    Este archivo convierte la respuesta del backend en una presentación visual.
*/


function crearElemento(
    etiqueta,
    clase,
    texto
) {
    const elemento = document.createElement(etiqueta);

    if (clase) {
        elemento.className = clase;
    }

    if (texto !== undefined && texto !== null) {
        elemento.textContent = texto;
    }

    return elemento;
}


function valorSeguro(valor) {
    if (
        valor === null
        || valor === undefined
        || valor === ""
    ) {
        return "No disponible";
    }

    return String(valor);
}


function traducirValorSeguro(valor) {
    if (typeof traducirValor === "function") {
        return traducirValor(valor);
    }

    return valorSeguro(valor);
}


function traducirVariableSegura(variable) {
    if (typeof traducirVariable === "function") {
        return traducirVariable(variable);
    }

    return valorSeguro(variable);
}


function parsearNumero(valor) {
    if (typeof valor === "number") {
        return valor;
    }

    if (!valor) {
        return 0;
    }

    const limpio = String(valor)
        .replaceAll(",", "")
        .replaceAll("USD", "")
        .replaceAll("%", "")
        .trim();

    const numero = Number(limpio);

    return Number.isFinite(numero)
        ? numero
        : 0;
}


function obtenerClaseRiesgo(probabilidad) {
    if (probabilidad >= 75) {
        return "riesgo-critico";
    }

    if (probabilidad >= 50) {
        return "riesgo-alto";
    }

    if (probabilidad >= 25) {
        return "riesgo-medio";
    }

    return "riesgo-bajo";
}


function crearBadge(texto, clase) {
    return crearElemento(
        "span",
        `badge ${clase || ""}`,
        texto
    );
}


function obtenerClaseGenero(genero) {
    const texto = String(genero || "").toLowerCase();

    if (
        texto.includes("female")
        || texto.includes("femenino")
    ) {
        return "badge-femenino";
    }

    if (
        texto.includes("male")
        || texto.includes("masculino")
    ) {
        return "badge-masculino";
    }

    return "badge-neutral";
}


function obtenerGrupoEdad(edad) {
    const numero = Number(edad);

    if (numero < 18) {
        return {
            texto: "Paciente pediátrico",
            clase: "badge-pediatrico"
        };
    }

    if (numero >= 65) {
        return {
            texto: "Adulto mayor",
            clase: "badge-adulto-mayor"
        };
    }

    return {
        texto: "Paciente adulto",
        clase: "badge-adulto"
    };
}


function crearFilaDato(nombre, valor) {
    const fila = crearElemento(
        "div",
        "dato-fila"
    );

    fila.appendChild(
        crearElemento(
            "span",
            null,
            nombre
        )
    );

    fila.appendChild(
        crearElemento(
            "strong",
            null,
            valorSeguro(valor)
        )
    );

    return fila;
}


/* ===========================
   SLIDE 1: PORTADA DE RIESGO
=========================== */

function renderPortada(slide) {
    const probabilidad = parsearNumero(
        slide.datos.probabilidad
    );

    const claseRiesgo = obtenerClaseRiesgo(
        probabilidad
    );

    const origenNarrativa =
        window.ORIGEN_NARRATIVA_DOSSIER || "Local";

    const card = crearElemento(
        "article",
        `slide slide-portada ${claseRiesgo}`
    );

    card.style.setProperty(
        "--porcentaje-riesgo",
        `${Math.min(probabilidad, 100)}%`
    );

    card.appendChild(
        crearElemento(
            "p",
            "slide-codigo",
            "[SMA.ALERTA]"
        )
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    const badges = crearElemento(
        "div",
        "badges-dossier"
    );

    badges.appendChild(
        crearBadge(
            "Modelo: LightGBM",
            "badge-modelo"
        )
    );

    badges.appendChild(
        crearBadge(
            "Explicabilidad: SHAP",
            "badge-xai"
        )
    );

    badges.appendChild(
        crearBadge(
            `Narrativa: ${origenNarrativa}`,
            "badge-gemini"
        )
    );

    badges.appendChild(
        crearBadge(
            "Decisión final: Auditor humano",
            "badge-humano"
        )
    );

    card.appendChild(badges);

    const riesgo = crearElemento(
        "div",
        "riesgo-box"
    );

    riesgo.appendChild(
        crearElemento(
            "span",
            "riesgo-label",
            "Probabilidad de posible fraude"
        )
    );

    riesgo.appendChild(
        crearElemento(
            "strong",
            "riesgo-valor",
            slide.datos.probabilidad
        )
    );

    const barra = crearElemento(
        "div",
        "medidor-riesgo"
    );

    barra.appendChild(
        crearElemento(
            "div",
            "medidor-riesgo-fill"
        )
    );

    riesgo.appendChild(barra);

    riesgo.appendChild(
        crearElemento(
            "span",
            "riesgo-nivel",
            `Nivel estimado: ${slide.datos.nivel_riesgo}`
        )
    );

    card.appendChild(riesgo);

    return card;
}


/* ===========================
   SLIDE 2: DATOS CLÍNICOS
=========================== */

function renderDatosClinicos(slide) {
    const card = crearElemento(
        "article",
        "slide"
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    const edad = slide.datos.edad;

    const genero = traducirValorSeguro(
        slide.datos.genero
    );

    const tipoVisita = traducirValorSeguro(
        slide.datos.tipo_visita
    );

    const grupoEdad = obtenerGrupoEdad(
        edad
    );

    const badges = crearElemento(
        "div",
        "badges-dossier"
    );

    badges.appendChild(
        crearBadge(
            genero,
            obtenerClaseGenero(genero)
        )
    );

    badges.appendChild(
        crearBadge(
            grupoEdad.texto,
            grupoEdad.clase
        )
    );

    badges.appendChild(
        crearBadge(
            tipoVisita,
            "badge-visita"
        )
    );

    card.appendChild(badges);

    const grid = crearElemento(
        "div",
        "datos-grid"
    );

    grid.appendChild(
        crearFilaDato(
            "Edad",
            edad
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Género",
            genero
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Diagnóstico",
            slide.datos.diagnostico
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Procedimiento",
            slide.datos.procedimiento
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Tipo de visita",
            tipoVisita
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Estancia",
            `${valorSeguro(slide.datos.estancia)} días`
        )
    );

    grid.appendChild(
        crearFilaDato(
            "Volumen del proveedor",
            `${valorSeguro(slide.datos.proveedor_mensual)} reclamaciones/mes`
        )
    );

    card.appendChild(grid);

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    return card;
}


/* ===========================
   SLIDE 3: COMPARACIÓN FINANCIERA
=========================== */

function renderComparacionFinanciera(slide) {
    const card = crearElemento(
        "article",
        "slide slide-financiera"
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    const montoReclamado = parsearNumero(
        slide.datos.monto_reclamado
    );

    const montoAprobado = parsearNumero(
        slide.datos.monto_aprobado
    );

    const maximo = Math.max(
        montoReclamado,
        montoAprobado,
        1
    );

    const porcentajeAprobado =
        montoReclamado > 0
            ? montoAprobado / montoReclamado * 100
            : 0;

    const claseRatio =
        porcentajeAprobado < 30
            ? "ratio-bajo"
            : porcentajeAprobado < 70
                ? "ratio-medio"
                : "ratio-alto";

    const resumenRatio = crearElemento(
        "div",
        `ratio-financiero ${claseRatio}`
    );

    resumenRatio.innerHTML = `
        <span>Proporción aprobada</span>
        <strong>${porcentajeAprobado.toFixed(2)}%</strong>
        <small>
            Este indicador compara el monto aprobado contra el monto reclamado.
            Una proporción baja puede representar una discrepancia financiera
            que requiere revisión.
        </small>
    `;

    card.appendChild(resumenRatio);

    const barras = crearElemento(
        "div",
        "barras-financieras"
    );

    barras.appendChild(
        crearBarraFinanciera(
            "Monto aprobado",
            slide.datos.monto_aprobado,
            montoAprobado / maximo * 100,
            "barra-aprobado"
        )
    );

    barras.appendChild(
        crearBarraFinanciera(
            "Monto reclamado",
            slide.datos.monto_reclamado,
            montoReclamado / maximo * 100,
            "barra-reclamado"
        )
    );

    card.appendChild(barras);

    const resumen = crearElemento(
        "div",
        "alerta-suave"
    );

    resumen.textContent =
        `Diferencia estimada: ${slide.datos.diferencia}`;

    card.appendChild(resumen);

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    return card;
}


function crearBarraFinanciera(
    nombre,
    valor,
    ancho,
    clase
) {
    const fila = crearElemento(
        "div",
        "barra-financiera"
    );

    fila.appendChild(
        crearElemento(
            "span",
            null,
            nombre
        )
    );

    const barra = crearElemento(
        "div",
        "barra-bg"
    );

    const relleno = crearElemento(
        "div",
        `barra-fill ${clase || ""}`
    );

    relleno.style.width =
        `${Math.max(4, Math.min(ancho, 100))}%`;

    barra.appendChild(relleno);

    fila.appendChild(barra);

    fila.appendChild(
        crearElemento(
            "strong",
            null,
            valor
        )
    );

    return fila;
}


/* ===========================
   SLIDE 4: FACTORES SHAP
=========================== */

function renderFactoresShap(slide) {
    const card = crearElemento(
        "article",
        "slide"
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    const nota = crearElemento(
        "div",
        "alerta-suave"
    );

    nota.textContent =
        "Los valores SHAP no son porcentajes. Indican cuánto empuja cada variable la salida interna del modelo hacia mayor o menor riesgo.";

    card.appendChild(nota);

    const contenedor = crearElemento(
        "div",
        "factores-grid"
    );

    const aumentan =
        slide.datos.factores_aumentan || [];

    if (aumentan.length === 0) {
        contenedor.appendChild(
            crearElemento(
                "p",
                "slide-narrativa",
                "No se identificaron factores positivos destacados."
            )
        );
    } else {
        aumentan.forEach((factor) => {
            contenedor.appendChild(
                crearFactorCard(factor)
            );
        });
    }

    card.appendChild(contenedor);

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    return card;
}


function crearFactorCard(factor) {
    const impacto = Number(
        factor.impacto_shap || 0
    );

    const direccion =
        impacto >= 0
            ? "factor-aumenta"
            : "factor-reduce";

    const card = crearElemento(
        "div",
        `factor-card ${direccion}`
    );

    card.appendChild(
        crearElemento(
            "span",
            "factor-variable",
            traducirVariableSegura(
                factor.variable || "Variable"
            )
        )
    );

    card.appendChild(
        crearElemento(
            "strong",
            "factor-impacto",
            impacto.toFixed(4)
        )
    );

    card.appendChild(
        crearElemento(
            "p",
            null,
            `Valor observado: ${traducirValorSeguro(factor.valor)}`
        )
    );

    card.appendChild(
        crearElemento(
            "small",
            "factor-explicacion",
            impacto >= 0
                ? "Este factor empuja la salida del modelo hacia mayor riesgo."
                : "Este factor reduce la salida del modelo hacia menor riesgo."
        )
    );

    return card;
}


/* ===========================
   SLIDE 5: RIESGO INTEGRADO
=========================== */

function renderRiesgoIntegrado(slide) {
    const card = crearElemento(
        "article",
        "slide"
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    const columnas = crearElemento(
        "div",
        "dos-paneles"
    );

    const conocido = crearElemento(
        "div",
        "mini-panel"
    );

    conocido.appendChild(
        crearElemento(
            "h4",
            null,
            "Lo que el sistema identificó"
        )
    );

    conocido.appendChild(
        crearElemento(
            "p",
            null,
            `Nivel de riesgo estimado: ${slide.datos.nivel_riesgo}`
        )
    );

    conocido.appendChild(
        crearElemento(
            "p",
            null,
            slide.datos.resumen_xai
                || "Sin resumen XAI disponible."
        )
    );

    const desconocido = crearElemento(
        "div",
        "mini-panel mini-panel-dashed"
    );

    desconocido.appendChild(
        crearElemento(
            "h4",
            null,
            "Límites de interpretación"
        )
    );

    if (
        slide.datos.campos_faltantes
        && slide.datos.campos_faltantes.length > 0
    ) {
        slide.datos.campos_faltantes.forEach((campo) => {
            desconocido.appendChild(
                crearElemento(
                    "p",
                    null,
                    `Campo faltante: ${campo}`
                )
            );
        });
    } else {
        desconocido.appendChild(
            crearElemento(
                "p",
                null,
                "No se identificaron campos faltantes en la entrada."
            )
        );
    }

    desconocido.appendChild(
        crearElemento(
            "p",
            null,
            "El resultado debe ser interpretado como apoyo a la auditoría, no como una confirmación automática de fraude."
        )
    );

    columnas.appendChild(conocido);
    columnas.appendChild(desconocido);

    card.appendChild(columnas);

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    return card;
}


/* ===========================
   SLIDE 6: RECOMENDACIÓN
=========================== */

function renderRecomendacion(slide) {
    const card = crearElemento(
        "article",
        "slide slide-recomendacion"
    );

    card.appendChild(
        crearElemento(
            "h3",
            null,
            slide.titulo
        )
    );

    const recomendacion = crearElemento(
        "div",
        "recomendacion-box"
    );

    recomendacion.textContent =
        slide.datos.recomendacion;

    card.appendChild(recomendacion);

    const lista = crearElemento(
        "ul",
        "checklist"
    );

    const checklist =
        slide.datos.checklist || [];

    checklist.forEach((item) => {
        const li = crearElemento(
            "li",
            null,
            item
        );

        lista.appendChild(li);
    });

    card.appendChild(lista);

    card.appendChild(
        crearElemento(
            "p",
            "slide-narrativa",
            slide.narrativa
        )
    );

    return card;
}


/* ===========================
   CONTROLADOR DE SLIDES
=========================== */

function renderSlide(slide) {
    switch (slide.tipo) {
        case "portada_riesgo":
            return renderPortada(slide);

        case "datos_clinicos":
            return renderDatosClinicos(slide);

        case "comparacion_financiera":
            return renderComparacionFinanciera(slide);

        case "factores_shap":
            return renderFactoresShap(slide);

        case "riesgo_integrado":
            return renderRiesgoIntegrado(slide);

        case "recomendacion":
            return renderRecomendacion(slide);

        default: {
            const card = crearElemento(
                "article",
                "slide"
            );

            card.appendChild(
                crearElemento(
                    "h3",
                    null,
                    slide.titulo || "Análisis"
                )
            );

            card.appendChild(
                crearElemento(
                    "p",
                    "slide-narrativa",
                    slide.narrativa || ""
                )
            );

            return card;
        }
    }
}


/* ===========================
   RENDER PRINCIPAL DEL DOSSIER
=========================== */

function renderizarDossier(dossier) {
    window.ORIGEN_NARRATIVA_DOSSIER =
        dossier.narrativa_generada_por || "Local";

    const origen = document.getElementById(
        "origenNarrativa"
    );

    if (origen) {
        origen.textContent =
            `Narrativas generadas por: ${window.ORIGEN_NARRATIVA_DOSSIER}`;
    }

    const contenedor = document.getElementById(
        "contenedorDossier"
    );

    contenedor.innerHTML = "";

    const slides = dossier.slides || [];

    slides.forEach((slide, indice) => {
        const slideRenderizada = renderSlide(slide);

        const numero = crearElemento(
            "div",
            "numero-slide",
            String(indice + 1).padStart(2, "0")
        );

        slideRenderizada.prepend(numero);

        contenedor.appendChild(
            slideRenderizada
        );
    });
}


/* ===========================
   DETALLE TÉCNICO
=========================== */

function renderizarDetalleTecnico(dossier) {
    const resultadoXai =
        dossier.detalle_tecnico?.resultado_xai || {};

    renderizarFactoresDetalle(
        "factoresAumentan",
        resultadoXai.factores_aumentan_riesgo || []
    );

    renderizarFactoresDetalle(
        "factoresReducen",
        resultadoXai.factores_reducen_riesgo || []
    );

    const imagen = document.getElementById(
        "imagenShap"
    );

    if (resultadoXai.grafico_shap_base64) {
        imagen.src =
            `data:image/png;base64,${resultadoXai.grafico_shap_base64}`;

        imagen.style.display = "block";
    } else {
        imagen.removeAttribute("src");
        imagen.style.display = "none";
    }

    document.getElementById("textoInforme").value =
        dossier.informe_auditoria_markdown || "";
}


function renderizarFactoresDetalle(id, factores) {
    const contenedor = document.getElementById(id);

    contenedor.innerHTML = "";

    if (!factores.length) {
        contenedor.textContent =
            "No se identificaron factores destacados.";

        return;
    }

    factores.forEach((factor) => {
        contenedor.appendChild(
            crearFactorCard(factor)
        );
    });
}