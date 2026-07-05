"use strict";

const TRADUCCIONES_VALORES = {
    Female: "Femenino",
    Male: "Masculino",

    Emergency: "Emergencia",
    Inpatient: "Hospitalización",
    Outpatient: "Consulta externa",

    Approved: "Aprobada",
    Pending: "Pendiente",
    Rejected: "Rechazada",

    Medicaid: "Medicaid",
    Medicare: "Medicare",
    Private: "Seguro privado",
    "Self-Pay": "Pago particular",

    Cardiology: "Cardiología",
    "General Practice": "Medicina general",
    "Internal Medicine": "Medicina interna",
    Neurology: "Neurología",
    Orthopedics: "Ortopedia",
    Pulmonology: "Neumología",

    PA: "Pensilvania (PA)",
    CA: "California (CA)",
    FL: "Florida (FL)",
    GA: "Georgia (GA)",
    IL: "Illinois (IL)",
    NY: "Nueva York (NY)",
    OH: "Ohio (OH)",
    TX: "Texas (TX)"
};


const TRADUCCIONES_VARIABLES = {
    Patient_Age: "Edad del paciente",
    Patient_Gender: "Género del paciente",
    Diagnosis_Code: "Código de diagnóstico",
    Procedure_Code: "Código de procedimiento",
    Claim_Amount: "Monto reclamado",
    Approved_Amount: "Monto aprobado",
    Insurance_Type: "Tipo de seguro",
    Provider_Specialty: "Especialidad del proveedor",
    Patient_State: "Estado del paciente",
    Claim_Status: "Estado de la reclamación",
    Visit_Type: "Tipo de visita",
    Length_of_Stay: "Duración de estancia",
    Chronic_Condition_Flag: "Condición crónica",
    Prior_Visits_12m: "Visitas previas en 12 meses",
    Days_Between_Service_and_Claim: "Días entre servicio y reclamación",
    Number_of_Claims_Per_Provider_Monthly: "Reclamaciones mensuales del proveedor",
    Submission_Month: "Mes de presentación",
    Submission_Year: "Año de presentación",
    Approval_Ratio: "Proporción aprobada",
    Amount_Diff: "Diferencia entre monto reclamado y aprobado"
};


function traducirValor(valor) {
    if (
        valor === null
        || valor === undefined
        || valor === ""
    ) {
        return "No disponible";
    }

    return TRADUCCIONES_VALORES[String(valor)] || String(valor);
}


function traducirVariable(variable) {
    if (
        variable === null
        || variable === undefined
        || variable === ""
    ) {
        return "Variable no disponible";
    }

    return TRADUCCIONES_VARIABLES[String(variable)] || String(variable);
}