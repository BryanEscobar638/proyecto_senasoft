async function enviarMensaje() {
  const input = document.getElementById("mensaje").value.trim();
  const chatBody = document.getElementById("chatBody");

  if (!input) {
    const warning = document.createElement("div");
    warning.classList.add("alert", "alert-warning", "mt-2");
    warning.textContent = "Por favor, escribe un mensaje antes de enviar.";
    chatBody.appendChild(warning);
    chatBody.scrollTop = chatBody.scrollHeight;
    return;
  }

  // Burbuja del usuario
  const userWrapper = document.createElement("div");
  userWrapper.classList.add("d-flex", "justify-content-end", "mb-2");

  const userMsg = document.createElement("div");
  userMsg.classList.add("p-2", "rounded-3", "shadow-sm", "user-msg", "bg-primary", "text-white");
  userMsg.textContent = input;

  userWrapper.appendChild(userMsg);
  chatBody.appendChild(userWrapper);

  // Limpiar input
  document.getElementById("mensaje").value = "";
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    const res = await fetch(`/consulta?mensaje=${encodeURIComponent(input)}`);
    if (!res.ok) throw new Error(`Error del servidor (${res.status})`);
    const data = await res.json();

    // Burbuja del bot
    const botWrapper = document.createElement("div");
    botWrapper.classList.add("d-flex", "justify-content-start", "mb-2");

    const botMsg = document.createElement("div");
    botMsg.classList.add("p-2", "rounded-3", "shadow-sm", "bot-msg", "bg-light");
    botMsg.textContent = data.mensaje || "No se recibió respuesta del servidor.";

    if (data.mensaje) {
      botMsg.textContent = data.mensaje;
    } else if (data.error) {
      botMsg.classList.replace("bg-light", "bg-warning");
      botMsg.textContent = `⚠️ ${data.error}`;
    } else {
      botMsg.textContent = "No se recibió respuesta del servidor.";
    }

    botWrapper.appendChild(botMsg);
    chatBody.appendChild(botWrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
  } catch (error) {
    console.error("Error en la conexión:", error);
    const errorWrapper = document.createElement("div");
    errorWrapper.classList.add("d-flex", "justify-content-start", "mb-2");

    const errorMsg = document.createElement("div");
    errorMsg.classList.add("p-2", "bg-danger", "text-white", "rounded-3", "shadow-sm");
    errorMsg.textContent = "❌ Error al conectar con el servidor.";

    errorWrapper.appendChild(errorMsg);
    chatBody.appendChild(errorWrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
  }
}

// Click en el botón
document.getElementById("consultar").addEventListener("click", enviarMensaje);

// Detectar Enter en el input
document.getElementById("mensaje").addEventListener("keypress", function(e) {
  if (e.key === "Enter") {
    e.preventDefault(); // Evita que haga un salto de línea
    enviarMensaje();
  }
});

// modo oscuro
document.getElementById("modoOscuro").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

// Limpiar chat
document.getElementById("limpiarChat").addEventListener("click", () => {
  const chatBody = document.getElementById("chatBody");
  chatBody.innerHTML = "";
});
