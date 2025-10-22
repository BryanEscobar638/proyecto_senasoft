document.getElementById("consultar").addEventListener("click", async () => {
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
  userMsg.classList.add("p-2", "bg-primary", "text-white", "rounded-3", "shadow-sm");
  userMsg.textContent = input;

  userWrapper.appendChild(userMsg);
  chatBody.appendChild(userWrapper);

  // Limpiar input
  document.getElementById("mensaje").value = "";
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    // Llamada al backend que generará la respuesta con Gemini
    const res = await fetch(`/consulta?mensaje=${encodeURIComponent(input)}`);
    if (!res.ok) throw new Error(`Error del servidor (${res.status})`);
    const data = await res.json();

    // Burbuja del bot
    const botWrapper = document.createElement("div");
    botWrapper.classList.add("d-flex", "justify-content-start", "mb-2");

    const botMsg = document.createElement("div");
    botMsg.classList.add("p-2", "bg-light", "border", "rounded-3", "shadow-sm");

    if (data.gemini) {
      // Si el backend devuelve la respuesta generada por Gemini
      botMsg.textContent = data.gemini;
    } else if (data.mensaje) {
      // Si solo devuelve mensaje de dataset
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
});