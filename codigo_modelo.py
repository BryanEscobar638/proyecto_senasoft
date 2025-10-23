import os
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from xai_sdk import Client
from xai_sdk.chat import user, system

# ===== CONFIGURACIÓN GROK =====
XAI_API_KEY = "xai-Jf9hsD3TI0NfakD5bPSClKpBowH4vRRlSiVLIRivPzElnMmFFfoKDmTZhMQQLDWu24dthAos4FSYlBpT"
GROK_MODEL = "grok-4"

# Columnas críticas
CRITICAL_COLUMNS = ["comentario", "categoria", "nivel_urgencia", "ciudad"]

# Carpeta para guardar contextos
os.makedirs("data", exist_ok=True)


# ===== CLIENTE GROK =====
class GrokClient:
    """Cliente para xAI SDK (Grok)."""

    def __init__(self, api_key: str, model: str = GROK_MODEL):
        self.client = Client(api_key=api_key, timeout=3600)
        self.model = model

    def enviar_prompt(self, prompt: str) -> str:
        try:
            chat = self.client.chat.create(model=self.model)
            chat.append(system("Eres un experto en análisis de datos."))
            chat.append(user(prompt))
            response = chat.sample()
            return response.content
        except Exception as e:
            print("[GrokClient] Exception:", e)
            return None


# ===== CLASE PARA PROCESAR CSV =====
class CSVProcessor:
    def __init__(self, client):
        self.grok = client
        self.df = None

    def cargar_csv(self, archivo: UploadFile):
        df = pd.read_csv(archivo.file)
        df = df.drop_duplicates().fillna("")
        self.df = df

    def normalizar_columnas(self):
        """Normaliza nombres de columnas con más variantes."""
        sinonimos = {
            "comentario": [
                "comentario",
                "observacion",
                "observación",
                "mensaje",
                "nota",
                "descripcion",
                "descripción",
                "detalle",
                "detalles",
            ],
            "categoria": [
                "categoria",
                "categoría",
                "tipo",
                "clasificacion",
                "clasificación",
                "grupo",
                "categoría del problema",
                "categoria del problema",
                "tipo de problema",
                "clase",
            ],
            "ciudad": [
                "ciudad",
                "municipio",
                "localidad",
                "barrio",
                "region",
                "región",
                "ubicación",
                "ubicacion",
            ],
            "nivel_urgencia": [
                "nivel_urgencia",
                "nivel de urgencia",
                "urgencia",
                "prioridad",
                "nivel",
                "gravedad",
                "criticidad",
                "importancia",
            ],
        }

        def limpiar_nombre(nombre):
            """Limpia y estandariza el nombre de una columna."""
            nombre = nombre.lower()
            nombre = nombre.replace(" del ", " ")
            nombre = nombre.replace(" de ", " ")
            nombre = nombre.replace(" la ", " ")
            nombre = nombre.replace(" las ", " ")
            nombre = nombre.replace(" los ", " ")
            return nombre.strip()

        # Crear mapa de reemplazos
        reemplazos = {}
        for columna_final, alternativas in sinonimos.items():
            for alt in alternativas:
                reemplazos[limpiar_nombre(alt)] = columna_final

        # Normalizar nombres de columnas
        nuevas_columnas = []
        for col in self.df.columns:
            nombre_limpio = limpiar_nombre(col)
            # Si no encuentra coincidencia, mantiene el nombre original limpio
            nuevas_columnas.append(reemplazos.get(nombre_limpio, nombre_limpio))

        self.df.columns = nuevas_columnas

        # Verificar columnas críticas
        columnas_encontradas = set(self.df.columns)
        columnas_faltantes = [
            col for col in CRITICAL_COLUMNS if col not in columnas_encontradas
        ]
        if columnas_faltantes:
            print(f"⚠️ Columnas críticas no encontradas: {columnas_faltantes}")
            print(f"🔍 Columnas disponibles: {list(self.df.columns)}")

    def detectar_columnas_sensibles(self):
        resumen = {col: self.df[col].head(5).tolist() for col in self.df.columns}
        prompt = f"""
        Estos son los nombres de columnas y algunos valores del dataset:
        {resumen}
        Identifica cuáles columnas podrían contener información sensible o privada
        (como datos personales, información financiera, salud, etc.) y enuméralas separadas por comas.
        """
        response = self.grok.enviar_prompt(prompt)
        if not response:
            return []
        columnas_a_dropear = [
            c.strip() for c in response.split(",") if c.strip() in self.df.columns
        ]
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
                resumen[f"por_{col}"] = {
                    "conteo": conteo,
                    "porcentaje": {
                        k: round((v / total) * 100, 2) for k, v in conteo.items()
                    },
                }

        # Análisis detallado de categorías por ciudad
        if "ciudad" in self.df.columns and "categoria" in self.df.columns:
            categorias_por_ciudad = {}

            # Obtener todas las categorías únicas
            todas_categorias = sorted(self.df["categoria"].unique())

            for ciudad in sorted(self.df["ciudad"].unique()):
                datos_ciudad = self.df[self.df["ciudad"] == ciudad]

                # Conteo de cada categoría en esta ciudad
                conteo_categorias = datos_ciudad["categoria"].value_counts().to_dict()

                # Asegurar que todas las categorías estén representadas
                categorias_completas = {
                    cat: conteo_categorias.get(cat, 0) for cat in todas_categorias
                }

                # Calcular porcentajes
                total_ciudad = len(datos_ciudad)
                porcentajes = {
                    cat: (
                        round((count / total_ciudad) * 100, 2)
                        if total_ciudad > 0
                        else 0
                    )
                    for cat, count in categorias_completas.items()
                }

                # Si hay nivel de urgencia, agregar distribución
                if "nivel_urgencia" in self.df.columns:
                    urgencias_por_categoria = {}
                    for cat in todas_categorias:
                        datos_cat = datos_ciudad[datos_ciudad["categoria"] == cat]
                        if not datos_cat.empty:
                            urgencias = (
                                datos_cat["nivel_urgencia"].value_counts().to_dict()
                            )
                            urgencias_por_categoria[cat] = urgencias

                categorias_por_ciudad[ciudad] = {
                    "total_registros": total_ciudad,
                    "categorias": {
                        categoria: {
                            "cantidad": count,
                            "porcentaje": porcentajes[categoria],
                            "urgencias": (
                                urgencias_por_categoria.get(categoria, {})
                                if "nivel_urgencia" in self.df.columns
                                else {}
                            ),
                        }
                        for categoria, count in categorias_completas.items()
                    },
                }

            resumen["distribucion_categorias_por_ciudad"] = categorias_por_ciudad

            # Agregar resumen textual específico de distribución
            informes = []
            for ciudad, datos in categorias_por_ciudad.items():
                cats_ordenadas = sorted(
                    datos["categorias"].items(),
                    key=lambda x: x[1]["cantidad"],
                    reverse=True,
                )
                top_cats = cats_ordenadas[:3]
                informe = f"En {ciudad} ({datos['total_registros']} registros):"
                for cat, info in top_cats:
                    if info["cantidad"] > 0:
                        informe += f"\n- {cat}: {info['cantidad']} casos ({info['porcentaje']}%)"
                informes.append(informe)

            resumen["resumen_textual"] = informes

        return resumen

    def procesar(self, archivo: UploadFile):
        self.cargar_csv(archivo)
        self.normalizar_columnas()
        columnas_a_dropear = self.detectar_columnas_sensibles()
        columnas_a_dropear = self.proteger_columnas_criticas(columnas_a_dropear)
        if columnas_a_dropear:
            self.df = self.df.drop(columns=columnas_a_dropear)
        columnas_finales = [c for c in CRITICAL_COLUMNS if c in self.df.columns] + [
            c for c in self.df.columns if c not in CRITICAL_COLUMNS
        ]
        self.df = self.df[columnas_finales]
        resumen = self.generar_resumenes()

        with open("data/resumen.json", "w", encoding="utf-8") as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        return self.df, resumen


# ===== FASTAPI =====
app = FastAPI(title="Procesador CSV Inteligente con Grok")



@app.post("/procesar-csv/")
async def procesar_csv_endpoint(file: UploadFile = File(...)):
    client = GrokClient(api_key=XAI_API_KEY)
    processor = CSVProcessor(client)
    df_final, resumen = processor.procesar(file)
    return JSONResponse(
        content={
            "resumen": resumen,
            "ejemplo_datos": df_final.head(10).to_dict(orient="records"),
        }
    )


@app.post("/chatbot/")
async def chatbot_endpoint(mensaje: str = Form(...)):
    if not os.path.exists("data/resumen.json"):
        return JSONResponse(
            content={"error": "No hay datos procesados aún."}, status_code=400
        )
    with open("data/resumen.json", "r", encoding="utf-8") as f:
        resumen = json.load(f)
    client = GrokClient(api_key=XAI_API_KEY)
    prompt = f"""Analiza este resumen de dataset y responde a la pregunta:
    {json.dumps(resumen, ensure_ascii=False, indent=2)}
    
    Pregunta: {mensaje}
    
    Usa solo la información disponible. Se preciso pero recomienda deciciones a tomar para tratar las problematicas que afectan
    da informacion de cuales zonas, categorias o aspectos son los mas criticos y se deberian priorizar."""

    respuesta = client.enviar_prompt(prompt)
    return JSONResponse(content={"respuesta": respuesta})


@app.get("/generar-informe/")
async def generar_informe_endpoint():
    if not os.path.exists("data/resumen.json"):
        return JSONResponse(
            content={"error": "No hay datos procesados aún."}, status_code=400
        )
    with open("data/resumen.json", "r", encoding="utf-8") as f:
        resumen = json.load(f)
    client = GrokClient(api_key=XAI_API_KEY)
    prompt = f"""Genera un informe ejecutivo basado en estos datos:
    {json.dumps(resumen, ensure_ascii=False, indent=2)}
    
    Enfócate en:
    1. Tendencias clave por categoría y ciudad
    2. Problemas urgentes
    3. Patrones notables
    
    Usa viñetas para mayor claridad."""

    informe = client.enviar_prompt(prompt)
    return JSONResponse(content={"informe": informe})


# ===== MAIN LOCAL =====
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)