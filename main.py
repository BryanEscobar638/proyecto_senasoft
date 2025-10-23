import os
import json
import pandas as pd
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

# ===== CONFIGURACIÓN GEMINI =====
GEMINI_API_KEY = "AIzaSyDIthgBtbQ_q9ls8450_8l4AkFMAQgDL4g"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"

# Columnas críticas que siempre queremos mantener
CRITICAL_COLUMNS = ["comentario", "categoria", "nivel_urgencia", "ciudad"]

# Carpeta donde se guardarán los contextos
os.makedirs("data", exist_ok=True)


# ===== CLASES =====
class GeminiClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def enviar_prompt(self, prompt):
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "temperature": 0.2,
            "maxOutputTokens": 800
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Gemini devuelve el texto en data['candidates'][0]['content']
            return data.get("candidates", [{}])[0].get("content", "")
        except Exception as e:
            print("⚠️ Error al llamar a Gemini:", e)
            return None


class CSVProcessor:
    def __init__(self, gemini_client):
        self.gemini = gemini_client
        self.df = None

    def cargar_csv(self, archivo: UploadFile):
        df = pd.read_csv(archivo.file)
        df = df.drop_duplicates().fillna("")
        self.df = df

    def normalizar_columnas(self):
        sinonimos = {
            "comentario": ["comentario", "observacion", "observación", "mensaje", "nota", "descripcion"],
            "categoria": ["categoria", "tipo", "clasificacion", "grupo"],
            "ciudad": ["ciudad", "municipio", "localidad", "barrio", "region"],
            "nivel_urgencia": ["nivel_urgencia", "urgencia", "prioridad", "nivel", "gravedad"]
        }
        reemplazos = {v.lower(): k for k, vals in sinonimos.items() for v in vals}

        nuevas_columnas = []
        for col in self.df.columns:
            col_lower = col.lower().strip().replace(" ", "_")
            nuevas_columnas.append(reemplazos.get(col_lower, col_lower))
        self.df.columns = nuevas_columnas

    def detectar_columnas_sensibles(self):
        resumen = {col: self.df[col].head(5).tolist() for col in self.df.columns}
        prompt = f"""
        Estos son los nombres de columnas y algunos valores del dataset:
        {resumen}

        Indica qué columnas podrían ser sensibles para la privacidad o no útiles para análisis.
        Devuelve solo los nombres de las columnas, separados por coma.
        """
        response = self.gemini.enviar_prompt(prompt)
        if not response:
            return []

        columnas_a_dropear = [c.strip() for c in response.split(",") if c.strip() in self.df.columns]
        return columnas_a_dropear

    def proteger_columnas_criticas(self, columnas):
        return [c for c in columnas if c not in CRITICAL_COLUMNS]

    def generar_resumenes(self):
        resumen = {"total_registros": len(self.df)}

        # Distribuciones básicas
        for col in ["categoria", "ciudad", "nivel_urgencia"]:
            if col in self.df.columns:
                conteo = self.df[col].value_counts().to_dict()
                total = sum(conteo.values())
                porcentajes = {k: round((v / total) * 100, 2) for k, v in conteo.items()}
                resumen[f"por_{col}"] = {
                    "conteo": conteo,
                    "porcentaje": porcentajes
                }

        # Combinaciones comunes
        combinaciones = [
            ("categoria", "ciudad"),
            ("ciudad", "categoria"),
            ("categoria", "nivel_urgencia"),
            ("ciudad", "nivel_urgencia")
        ]
        for cols in combinaciones:
            if all(col in self.df.columns for col in cols):
                key = "_y_".join(cols)
                conteo = self.df.groupby(list(cols)).size().to_dict()
                resumen[f"por_{key}"] = conteo

        # Jerarquía ciudad -> categoría -> urgencia
        if all(col in self.df.columns for col in ["ciudad", "categoria", "nivel_urgencia"]):
            estructura = {}
            for _, fila in self.df.iterrows():
                ciudad = fila["ciudad"]
                categoria = fila["categoria"]
                urgencia = fila["nivel_urgencia"]

                estructura.setdefault(ciudad, {}).setdefault(categoria, {}).setdefault(urgencia, 0)
                estructura[ciudad][categoria][urgencia] += 1
            resumen["ciudad_categoria_urgencia"] = estructura

        # Informes textuales automáticos
        informes = []
        if "ciudad" in self.df.columns and "categoria" in self.df.columns:
            ciudades = self.df["ciudad"].unique()
            for ciudad in ciudades:
                subset = self.df[self.df["ciudad"] == ciudad]
                resumen_ciudad = subset["categoria"].value_counts().to_dict()
                top_categoria = max(resumen_ciudad, key=resumen_ciudad.get)
                informes.append(
                    f"En {ciudad}, la categoría con más reportes es '{top_categoria}' con {resumen_ciudad[top_categoria]} casos."
                )
        resumen["resumen_textual"] = informes

        return resumen

    def procesar(self, archivo: UploadFile):
        self.cargar_csv(archivo)
        self.normalizar_columnas()

        columnas_a_dropear = self.detectar_columnas_sensibles()
        columnas_a_dropear = self.proteger_columnas_criticas(columnas_a_dropear)

        if columnas_a_dropear:
            self.df = self.df.drop(columns=columnas_a_dropear)

        columnas_finales = [c for c in CRITICAL_COLUMNS if c in self.df.columns] + \
                           [c for c in self.df.columns if c not in CRITICAL_COLUMNS]
        self.df = self.df[columnas_finales]

        resumen = self.generar_resumenes()

        self.df.to_csv("data/contexto.csv", index=False)
        with open("data/resumen.json", "w", encoding="utf-8") as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)

        return self.df, resumen


# ===== FASTAPI =====
app = FastAPI(title="Procesador CSV Inteligente con Gemini API")


@app.post("/procesar-csv/")
async def procesar_csv_endpoint(file: UploadFile = File(...)):
    gemini_client = GeminiClient(GEMINI_API_KEY, GEMINI_URL)
    processor = CSVProcessor(gemini_client)
    df_final, resumen = processor.procesar(file)

    return JSONResponse(content={
        "resumen": resumen,
        "ejemplo_datos": df_final.head(10).to_dict(orient="records")
    })


@app.post("/chatbot/")
async def chatbot_endpoint(mensaje: str = Form(...)):
    if not os.path.exists("data/resumen.json"):
        return JSONResponse(content={"error": "No hay datos procesados aún."}, status_code=400)

    with open("data/resumen.json", "r", encoding="utf-8") as f:
        resumen = json.load(f)

    prompt = f"""
    Actúa como un analista de datos experto.
    Responde la siguiente pregunta basándote únicamente en este resumen:
    {json.dumps(resumen, ensure_ascii=False, indent=2)}

    Pregunta del usuario:
    {mensaje}
    """
    gemini_client = GeminiClient(GEMINI_API_KEY, GEMINI_URL)
    respuesta = gemini_client.enviar_prompt(prompt)

    return JSONResponse(content={"respuesta": respuesta})


@app.get("/generar-informe/")
async def generar_informe_endpoint():
    if not os.path.exists("data/resumen.json"):
        return JSONResponse(content={"error": "No hay datos procesados aún."}, status_code=400)

    with open("data/resumen.json", "r", encoding="utf-8") as f:
        resumen = json.load(f)

    prompt = f"""
    Redacta un informe profesional basado en el siguiente resumen:
    {json.dumps(resumen, ensure_ascii=False, indent=2)}
    """
    gemini_client = GeminiClient(GEMINI_API_KEY, GEMINI_URL)
    informe = gemini_client.enviar_prompt(prompt)

    return JSONResponse(content={"informe": informe})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
