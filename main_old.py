from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import unicodedata
import requests
import os

# ================== CONFIGURACIÓN ==================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Variable de entorno
GEMINI_MODEL = "gemini-2.5-flash"
print("GEMINI_API_KEY =", GEMINI_API_KEY)

if not GEMINI_API_KEY:
    print("❌ La variable de entorno GEMINI_API_KEY no está definida. Gemini no funcionará.")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================== CARGA Y LIMPIEZA DE DATOS ==================
df = pd.read_csv("dataset_comunidades_senasoft.csv")

# Normalizar columnas
df.columns = df.columns.str.lower().str.replace(' ', '_')
df.columns = df.columns.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# Función para normalizar texto
def normalizar_texto(texto):
    if isinstance(texto, str):
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto.lower())
            if unicodedata.category(c) != 'Mn'
        ).strip()
    return texto

# Normalizar columnas de texto
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(normalizar_texto)

# Limpiar datos
df = df.drop(columns=["nombre", "genero"], errors="ignore")
df['edad'] = df['edad'].fillna(48)
df['ciudad'] = df['ciudad'].fillna('desconocida')

# Diccionario de palabras clave por categoría
categoria_palabras = {
    "salud": ["salud", "medicos", "hospital", "agua potable"],
    "seguridad": ["seguridad", "calles oscuras", "peligrosas", "policial", "policia"],
    "educacion": ["escuela", "educacion", "biblioteca", "internet", "centro cultural"],
    "medio ambiente": ["basura", "contaminacion", "rio", "medio ambiente"]
}

# Normalizar palabras clave
for cat in categoria_palabras:
    categoria_palabras[cat] = [normalizar_texto(p) for p in categoria_palabras[cat]]

# ================== FUNCIÓN PARA GEMINI ==================
def generar_respuesta_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "❌ Gemini no disponible (API key no definida)"
    """
    Llama a la API de Gemini y devuelve el texto generado.
    """
    url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "prompt": {
            "text": f"Usa la información del dataset y genera una respuesta clara sobre: {prompt}"
        },
        "temperature": 0.7,
        "maxOutputTokens": 500
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Acceder al texto generado
        return data.get("candidates", [{}])[0].get("content", [{}])[0].get("text", "⚠️ Sin respuesta de Gemini")
    except requests.exceptions.HTTPError as e:
        print("Error llamando a Gemini:", e)
        return f"❌ Error HTTP: {e.response.status_code}"
    except Exception as e:
        print("Error general llamando a Gemini:", e)
        return "❌ Error generando respuesta con Gemini"

# ================== ENDPOINTS ==================
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/consulta")
async def consulta(mensaje: str = Query(...)):
    texto = normalizar_texto(mensaje)

    # Listas válidas
    ciudades_validas = [normalizar_texto(c) for c in [
        "Barranquilla", "Bogotá", "Bucaramanga", "Cali", "Cartagena",
        "Cúcuta", "Manizales", "Medellín", "Pereira", "Santa Marta"
    ]]
    categorias_validas = list(categoria_palabras.keys())

    # Detectar ciudad
    ciudad = next((c for c in ciudades_validas if c in texto), None)
    if not ciudad:
        return JSONResponse({"error": "No se detectó ninguna ciudad válida en el mensaje."}, status_code=400)

    # Detectar categoría
    categoria = next((cat for cat in categorias_validas 
                      if any(palabra in texto for palabra in categoria_palabras[cat])), None)
    if not categoria:
        return JSONResponse({"error": "No se detectó ninguna categoría válida en el mensaje."}, status_code=400)

    # Asegurar que todos los comentarios sean strings
    df['comentario'] = df['comentario'].astype(str)

    # Contar reportes en dataset
    count = df[
        (df['ciudad'] == ciudad) &
        (df['comentario'].apply(lambda x: any(palabra in x for palabra in categoria_palabras[categoria])))
    ].shape[0]

    mensaje_dataset = f"{count} usuarios reportaron problemas en la {categoria} de {ciudad.capitalize()}."

    # Llamada segura a Gemini
    mensaje_gemini = generar_respuesta_gemini(texto)

    return {
        "mensaje_dataset": mensaje_dataset,
        "mensaje_gemini": mensaje_gemini
    }