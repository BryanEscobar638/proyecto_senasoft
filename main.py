from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import unicodedata
import requests
import json

# ================== CONFIGURACIÓN ==================
GEMINI_API_KEY = "AIzaSyDbyg3DgpbQs9rFiSrzvO2tn_FNT2Vbd1U"  # Reemplaza con tu clave real
GEMINI_MODEL = "gemini-2.5-flash"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================== CARGA Y LIMPIEZA DE DATOS ==================
df = pd.read_csv("dataset_comunidades_senasoft.csv")

# Normalizar columnas
df.columns = df.columns.str.lower().str.replace(' ', '_')
df.columns = df.columns.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# Función para normalizar texto (quita tildes, pasa a minúsculas)
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
df = df.dropna(subset=['comentario'])
df['edad'].fillna(48, inplace=True)
df['ciudad'].fillna('desconocida', inplace=True)

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
def generar_respuesta_gemini(task_description: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Genera una respuesta en formato de dos líneas.\n"
                                f"Línea 1: Resume en una frase.\n"
                                f"Línea 2: Clasificación con una sola palabra: Trabajo, Estudio, Personal, Urgente, Ocio.\n"
                                f"No uses negritas ni texto adicional. Tarea: {task_description}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "candidateCount": 1,
            "maxOutputTokens": 1024
        }
    }
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"},
                                 data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        texto_generado = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return texto_generado or "⚠️ Sin texto disponible"
    except requests.RequestException as e:
        return f"❌ Error generando resumen: {str(e)}"

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

    # Contar reportes en dataset
    count = df[
        (df['ciudad'] == ciudad) &
        (df['comentario'].apply(lambda x: any(palabra in x for palabra in categoria_palabras[categoria])))
    ].shape[0]

    mensaje_dataset = f"{count} usuarios reportaron problemas en la {categoria} de {ciudad.capitalize()}."

    # Generar mensaje con Gemini usando el texto del usuario
    mensaje_gemini = generar_respuesta_gemini(mensaje)

    print("Mensaje recibido:", mensaje)
    print("Texto normalizado:", texto)
    print("Ciudad detectada:", ciudad)
    print("Categoría detectada:", categoria)

    return {
        "mensaje_dataset": mensaje_dataset,
        "mensaje_gemini": mensaje_gemini
    }
