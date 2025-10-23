let csvCargado = false;
const API_BASE_URL = "http://20.36.132.212:8000"; // URL del backend desplegado

// -----------------------------------------------------------------
// 🟢 REFERENCIAS A ELEMENTOS DEL DOM
// -----------------------------------------------------------------
const mensajeInput = document.getElementById("mensaje");
const consultarBtn = document.getElementById("consultar");
const fileInput = document.getElementById("csvFile");
const cargarCSVBtn = document.getElementById("cargarCSV");
const chatBody = document.getElementById("chatBody");
const csvUploadContainer = document.getElementById("csvUploadContainer");

// Menú Configuración Desktop
const modoOscuroBtn = document.getElementById("modoOscuro");
const limpiarChatBtn = document.getElementById("limpiarChat");
const cambiarArchivoBtn = document.getElementById("cambiarArchivo");
const nombreArchivoCargado = document.getElementById("nombreArchivoCargado");
const csvDivider = document.getElementById("csvDivider");

// Menú Configuración Mobile
const modoOscuroBtnMobile = document.getElementById("modoOscuroMobile");
const limpiarChatBtnMobile = document.getElementById("limpiarChatMobile");
const cambiarArchivoBtnMobile = document.getElementById("cambiarArchivoMobile");
const nombreArchivoCargadoMobile = document.getElementById("nombreArchivoCargadoMobile");
const csvDividerMobile = document.getElementById("csvDividerMobile");

// Botones nuevos del sidebar
const generarInformePDFSidebar = document.getElementById("generarInformePDFSidebar");

// -----------------------------------------------------------------
// 🟢 INICIALIZACIÓN
// -----------------------------------------------------------------
mensajeInput.disabled = true;
consultarBtn.disabled = true;

// -----------------------------------------------------------------
// 🟢 FUNCIONES PRINCIPALES
// -----------------------------------------------------------------

function mostrarModal(mensaje, esError = false) {
    const modalBody = document.getElementById("modalBody");
    modalBody.innerHTML = mensaje;
    modalBody.style.color = esError ? "#dc3545" : "";
    const modal = new bootstrap.Modal(document.getElementById("modalNotificacion"));
    modal.show();
}

function limpiarMensaje(mensaje) {
    if (!mensaje) return "";
    let limpio = mensaje.trim();
    limpio = limpio.replace(/\n\s*\n/g, '\n');
    const div = document.createElement('div');
    div.textContent = limpio;
    limpio = div.innerHTML;
    limpio = limpio.replace(/\n/g, '<br>');
    return limpio;
}

function agregarMensaje(texto, esUsuario = false) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("d-flex", "mb-2");
    wrapper.classList.add(esUsuario ? "justify-content-end" : "justify-content-start");

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("p-2", "rounded-3", "shadow-sm");
    if (esUsuario) {
        msgDiv.classList.add("user-msg", "bg-primary", "text-white");
        msgDiv.textContent = texto;
    } else {
        msgDiv.classList.add("bot-msg", "bg-light");
        msgDiv.innerHTML = limpiarMensaje(texto);
    }

    wrapper.appendChild(msgDiv);
    chatBody.appendChild(wrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function mostrarIndicadorEscritura() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("d-flex", "justify-content-start", "mb-2");
    wrapper.id = "indicador-escritura";

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("p-2", "rounded-3", "shadow-sm", "bot-msg", "bg-light");
    msgDiv.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Escribiendo...</span></div> Pensando...';

    wrapper.appendChild(msgDiv);
    chatBody.appendChild(wrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function eliminarIndicadorEscritura() {
    const indicador = document.getElementById("indicador-escritura");
    if (indicador) indicador.remove();
}

function esInforme(mensaje) {
    const mensajeLower = mensaje.toLowerCase();
    const palabrasGeneracion = ['generame', 'genera me', 'genera', 'dame', 'crea', 'hazme'];
    const palabrasInforme = ['informe', 'reporte', 'resumen ejecutivo', 'análisis'];
    const tieneGeneracion = palabrasGeneracion.some(palabra => mensajeLower.includes(palabra));
    const tieneInforme = palabrasInforme.some(palabra => mensajeLower.includes(palabra));
    return tieneGeneracion && tieneInforme;
}

async function enviarMensaje() {
    if (!csvCargado) {
        mostrarModal("⚠️ Por favor, carga un archivo CSV primero.", true);
        return;
    }

    const input = mensajeInput.value.trim();
    if (!input) {
        mostrarModal("⚠️ Escribe un mensaje antes de enviar.", true);
        return;
    }

    mensajeInput.disabled = true;
    consultarBtn.disabled = true;

    agregarMensaje(input, true);
    mensajeInput.value = "";
    mostrarIndicadorEscritura();

    try {
        let respuesta;

        if (esInforme(input)) {
            const response = await fetch(`${API_BASE_URL}/generar-informe/`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });

            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);

            const data = await response.json();
            respuesta = data.informe || "No se pudo generar el informe.";
        } else {
            const formData = new FormData();
            formData.append("mensaje", input);

            const response = await fetch(`${API_BASE_URL}/chatbot/`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);

            const data = await response.json();
            respuesta = data.respuesta || "No se obtuvo respuesta del servidor.";
        }

        eliminarIndicadorEscritura();
        agregarMensaje(respuesta);

    } catch (error) {
        console.error(error);
        eliminarIndicadorEscritura();
        agregarMensaje(`❌ Error: ${error.message}`);
    } finally {
        mensajeInput.disabled = false;
        consultarBtn.disabled = false;
        mensajeInput.focus();
    }
}

function toggleModoOscuro() {
    document.body.classList.toggle("dark-mode");
}

function limpiarElChat() {
    chatBody.innerHTML = "";
    const bienvenida = document.createElement("div");
    bienvenida.classList.add("alert", "alert-secondary", "p-2", "mb-2");
    bienvenida.innerHTML = `
        ¡Hola! 👋 Soy tu asistente virtual.<br><br>
        Puedes preguntarme sobre los datos del CSV, por ejemplo:<br>
        <b>"¿Cómo está la seguridad en Pereira?"</b><br>
        <b>"¿Cuáles son las categorías más críticas?"</b><br><br>
        También puedes pedirme:<br>
        <b>"Genera un informe ejecutivo"</b>
    `;
    chatBody.appendChild(bienvenida);
}

function actualizarEstadoCSV(fileName) {
    csvCargado = true;
    mensajeInput.disabled = false;
    consultarBtn.disabled = false;
    csvUploadContainer.style.display = "none";

    nombreArchivoCargado.textContent = fileName;
    cambiarArchivoBtn.style.display = "block";
    csvDivider.style.display = "block";

    nombreArchivoCargadoMobile.textContent = fileName;
    cambiarArchivoBtnMobile.style.display = "block";
    csvDividerMobile.style.display = "block";

    limpiarElChat();
    mostrarModal(`✅ CSV "${fileName}" cargado exitosamente. Ya puedes hacer preguntas.`);
}

function resetearCSV() {
    csvUploadContainer.style.display = "block";
    cambiarArchivoBtn.style.display = "none";
    csvDivider.style.display = "none";
    nombreArchivoCargado.textContent = "";

    cambiarArchivoBtnMobile.style.display = "none";
    csvDividerMobile.style.display = "none";
    nombreArchivoCargadoMobile.textContent = "";

    csvCargado = false;
    mensajeInput.disabled = true;
    consultarBtn.disabled = true;
    fileInput.value = null;
    chatBody.innerHTML = "";

    mostrarModal("📂 Por favor, carga un nuevo archivo CSV.");
}

async function cargarCSV() {
    if (!fileInput.files.length) return mostrarModal("⚠️ Selecciona un archivo CSV primero.", true);

    const file = fileInput.files[0];
    const fileName = file.name;
    if (!fileName.toLowerCase().endsWith('.csv')) return mostrarModal("⚠️ Selecciona un CSV válido (.csv)", true);

    cargarCSVBtn.disabled = true;
    cargarCSVBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...';

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE_URL}/procesar-csv/`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);

        await response.json();
        actualizarEstadoCSV(fileName);
    } catch (error) {
        console.error(error);
        mostrarModal(`❌ Error: ${error.message}`, true);
    } finally {
        cargarCSVBtn.disabled = false;
        cargarCSVBtn.textContent = "Cargar CSV";
    }
}

// -----------------------------------------------------------------
// 🟢 NUEVA FUNCIÓN: GENERAR INFORME PDF
// -----------------------------------------------------------------
async function generarInformePDF() {
    if (!csvCargado) return mostrarModal("⚠️ Por favor, carga un CSV primero.", true);

    mostrarIndicadorEscritura();

    try {
        const response = await fetch(`${API_BASE_URL}/generar-informe/`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        const data = await response.json();
        const informe = data.informe || "No se pudo generar el informe.";

        eliminarIndicadorEscritura();
        limpiarElChat();

        // ✅ Generar PDF usando jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        const lineas = informe.split("\n");
        let y = 10;
        lineas.forEach(linea => {
            const textoDividido = doc.splitTextToSize(linea, 180); // ancho máximo 180 mm
            doc.text(textoDividido, 10, y);
            y += textoDividido.length * 10; // ajustar salto de línea
        });
        doc.save("informe.pdf");

        mostrarModal("✅ Informe PDF generado y descargado correctamente.");
    } catch (error) {
        console.error(error);
        eliminarIndicadorEscritura();
        mostrarModal(`❌ Error al generar el PDF: ${error.message}`, true);
    }
}

// 🔹 Botón PDF sidebar
if (generarInformePDFSidebar) {
    generarInformePDFSidebar.addEventListener("click", generarInformePDF);
}


// -----------------------------------------------------------------
// 🟢 EVENT LISTENERS
// -----------------------------------------------------------------
consultarBtn.addEventListener("click", enviarMensaje);
mensajeInput.addEventListener("keypress", e => { if (e.key === "Enter") { e.preventDefault(); enviarMensaje(); } });

cargarCSVBtn.addEventListener("click", cargarCSV);
cambiarArchivoBtn.addEventListener("click", resetearCSV);
cambiarArchivoBtnMobile.addEventListener("click", resetearCSV);

modoOscuroBtn.addEventListener("click", toggleModoOscuro);
modoOscuroBtnMobile.addEventListener("click", toggleModoOscuro);

limpiarChatBtn.addEventListener("click", limpiarElChat);
limpiarChatBtnMobile.addEventListener("click", limpiarElChat);