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

  // 🧍‍♂️ Burbuja del usuario
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
    console.log("🔍 Respuesta completa del backend:", data);

    // 🎯 Detectar correctamente el texto de la respuesta
    let respuestaTexto = "No se recibió respuesta del servidor.";

    // Caso 1: Watsonx.ai (modelo fundacional)
    if (data.results?.[0]?.generated_text) {
      respuestaTexto = data.results[0].generated_text;
    }
    // Caso 2: Watson Assistant clásico
    else if (data.output?.generic?.[0]?.text) {
      respuestaTexto = data.output.generic[0].text;
    }
    // Caso 3: watsonx.ai con estructura tipo "choices"
    else if (data.mensaje?.choices?.[0]?.message?.content) {
      respuestaTexto = data.mensaje.choices[0].message.content;
    }
    // Caso 4: backend personalizado que devuelve { mensaje: "..." }
    else if (typeof data.mensaje === "string") {
      respuestaTexto = data.mensaje;
    }
    // Caso 5: texto directo
    else if (typeof data === "string") {
      respuestaTexto = data;
    } 
    // Caso 6: fallback (ver todo el objeto)
    else {
      respuestaTexto = JSON.stringify(data, null, 2);
    }

    // 🤖 Burbuja del bot
    const botWrapper = document.createElement("div");
    botWrapper.classList.add("d-flex", "justify-content-start", "mb-2");

    const botMsg = document.createElement("div");
    botMsg.classList.add("p-2", "rounded-3", "shadow-sm", "bot-msg", "bg-light");
    botMsg.textContent = respuestaTexto;

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

// 📩 Click en el botón
document.getElementById("consultar").addEventListener("click", enviarMensaje);

// ⌨️ Enter en el input
document.getElementById("mensaje").addEventListener("keypress", function(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    enviarMensaje();
  }
});

// 🌙 Modo oscuro
document.getElementById("modoOscuro").addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
});

// 🧹 Limpiar chat
document.getElementById("limpiarChat").addEventListener("click", () => {
  const chatBody = document.getElementById("chatBody");
  chatBody.innerHTML = "";
});
