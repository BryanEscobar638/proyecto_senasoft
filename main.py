from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import unicodedata

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================== CARGA Y LIMPIEZA DE DATOS ==================
df = pd.read_csv("dataset_comunidades_senasoft.csv")

# Normalizar columnas
df.columns = df.columns.str.lower().str.replace(' ', '_')
df.columns = df.columns.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# Función para normalizar texto (quitar tildes y minúsculas)
def normalizar_texto(texto):
    if isinstance(texto, str):
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto.lower())
            if unicodedata.category(c) != 'Mn'
        ).strip()
    return texto

# Aplicar normalización a todas las columnas de texto
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(normalizar_texto)

# Limpiar datos
df = df.drop(columns=["nombre", "genero"], errors="ignore")
df = df.dropna(subset=['comentario'])
df['edad'].fillna(48, inplace=True)
df['ciudad'].fillna('desconocida', inplace=True)

# Diccionario para detectar palabras clave de categorías
categoria_palabras = {
    "salud": ["salud", "medicos", "hospital", "agua potable"],
    "seguridad": ["seguridad", "calles oscuras", "peligrosas", "policial", "policia"],
    "educacion": ["escuela", "educacion", "biblioteca", "internet", "centro cultural"],
    "medio ambiente": ["basura", "contaminacion", "rio", "medio ambiente"]
}

# Normalizar categorías
for cat in categoria_palabras:
    categoria_palabras[cat] = [normalizar_texto(p) for p in categoria_palabras[cat]]

# ================== ENDPOINT ==================
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

    # Contar reportes: ciudad exacta y alguna palabra clave de la categoría en comentario
    count = df[
        (df['ciudad'] == ciudad) &
        (df['comentario'].apply(lambda x: any(palabra in x for palabra in categoria_palabras[categoria])))
    ].shape[0]

    return {"mensaje": f"{count} usuarios reportaron problemas en la {categoria} de {ciudad.capitalize()}."}
