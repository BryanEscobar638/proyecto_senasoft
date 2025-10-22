from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import unicodedata
import requests

# ================== CONFIGURACIÓN IBM WATSON ==================
API_KEY = "3ZyGd0q5Z571DeRDXb5ZmQOAjt2b5LbF9nPET_AEjQKs"
DEPLOYMENT_URL = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/4a3682fc-6bb8-42dc-8c35-a10b4a039a0c/ai_service?version=2021-05-01"

# Obtener token
def obtener_token():
    token_response = requests.post(
        'https://iam.cloud.ibm.com/identity/token',
        data={"apikey": API_KEY, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return token_response.json()["access_token"]

mltoken = obtener_token()
headers_ibm = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}


# ================== FASTAPI ==================
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

df = pd.read_csv("dataset_comunidades_senasoft.csv")
df.columns = df.columns.str.lower().str.replace(' ', '_')
df.columns = df.columns.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

def normalizar_texto(texto):
    if isinstance(texto, str):
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto.lower())
            if unicodedata.category(c) != 'Mn'
        ).strip()
    return texto

for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(normalizar_texto)

df = df.drop(columns=["nombre", "genero"], errors="ignore")
df = df.dropna(subset=['comentario'])
df['edad'] = df['edad'].fillna(48)
df['ciudad'] = df['ciudad'].fillna('desconocida')

categoria_palabras = {
    "salud": ["salud", "medicos", "hospital", "agua potable"],
    "seguridad": ["seguridad", "calles oscuras", "peligrosas", "policial", "policia"],
    "educacion": ["escuela", "educacion", "biblioteca", "internet", "centro cultural"],
    "medio ambiente": ["basura", "contaminacion", "rio", "medio ambiente"]
}

for cat in categoria_palabras:
    categoria_palabras[cat] = [normalizar_texto(p) for p in categoria_palabras[cat]]

# ================== ENDPOINTS ==================
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/consulta")
async def consulta(mensaje: str = Query(...)):
    texto = normalizar_texto(mensaje)

    respuestas_rapidas = {
        "hola": "¡Hola! 👋 ¿Cómo estás?",
        "buenos dias": "¡Buenos días!",
        "buenas tardes": "¡Buenas tardes!",
        "buenas noches": "¡Buenas noches!",
        "gracias": "¡De nada!",
        "adios": "¡Hasta luego!"
    }

    for palabra, respuesta in respuestas_rapidas.items():
        if palabra in texto:
            return {"mensaje": respuesta}

    ciudades_validas = [normalizar_texto(c) for c in [
        "Barranquilla", "Bogotá", "Bucaramanga", "Cali", "Cartagena",
        "Cúcuta", "Manizales", "Medellín", "Pereira", "Santa Marta"
    ]]
    categorias_validas = list(categoria_palabras.keys())

    ciudad = next((c for c in ciudades_validas if c in texto), None)
    if not ciudad:
        return {"mensaje": "No te entiendo, ¿puedes volverlo a intentar? 🤔"}

    categoria = next((cat for cat in categorias_validas 
                      if any(palabra in texto for palabra in categoria_palabras[cat])), None)
    if not categoria:
        return {"mensaje": "No te entiendo, ¿puedes volverlo a intentar? 🤔"}

    count = df[
        (df['ciudad'] == ciudad) &
        (df['comentario'].apply(lambda x: any(palabra in x for palabra in categoria_palabras[categoria])))
    ].shape[0]

    # ================== Enviar a IBM ==================
    prompt = (
        f"Genera una respuesta breve y profesional sobre la situación de {categoria} en {ciudad.capitalize()}, "
        f"teniendo en cuenta que {count} personas han reportado problemas en ese tema."
    )

    payload = {"messages": [{"role": "user", "content": prompt}]}
    response = requests.post(DEPLOYMENT_URL, json=payload, headers=headers_ibm)

    try:
        data = response.json()
        return {"mensaje": data}
    except Exception:
        return {"mensaje": f"{count} usuarios reportaron problemas en la {categoria} de {ciudad.capitalize()}."}
