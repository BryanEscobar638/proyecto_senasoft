import pandas as pd

df = pd.read_csv("dataset_comunidades_senasoft.csv")

# ======= Normalizar los nombres de las columnas =============
df.columns = df.columns.str.lower().str.replace(' ', '_')
df.columns = df.columns.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# ============ Eliminar columnas que no sirven ===============
df = df.drop(columns=["nombre", "genero"])
# ======= Eliminar filas con comentarios vacios ================
df = df.dropna(subset=['comentario'])

# # ================= revisar dataframe ======================
# print(df.head())
# print(df.isnull().sum())

# # =================== revisar edades =========================
# promedio = df["edad"].max()
# print(promedio)

# # =================== revisar cantidad de genero iguales ======================
# df_sin_nulos = df.dropna(subset=['edad'])
# edades_contadas = df_sin_nulos.groupby('edad').size().reset_index(name='cantidad')
# print(edades_contadas.min())

# # =================== revisar cantidad de genero iguales ======================
# df_sin_nulos = df.dropna(subset=['genero'])
# genero_contados = df_sin_nulos.groupby('genero').size().reset_index(name='cantidad')
# print(genero_contados)

# # =================== revisar cantidad de ciudades iguales ======================
# ciudades_contadas = df.groupby('ciudad').size().reset_index(name='cantidad')
# print(ciudades_contadas)

# # =================== revisar cantidad de comentarios iguales =========================
# comentarios_contados = df.groupby('comentario').size().reset_index(name='cantidad')
# print(comentarios_contados)

# # =================== revisar categorias iguales ======================
# categorias_contadas = df.groupby('categoria_del_problema').size().reset_index(name='cantidad')
# print(categorias_contadas)

# # ============== revisar filas iguales ====================
# filas_duplicadas = df.loc[:, df.columns != "ID"].duplicated().sum()
# print(filas_duplicadas)

# ========= RECATEGORIZAR CATEGORIAS EN BASE A COMENTARIOS ===============
comentario_categoria = {
    "falta agua potable en varias casas.": "Salud",
    "faltan médicos en el centro de salud.": "Salud",
    "hay problemas con la recolección de basura.": "Medio ambiente",
    "la contaminación del río está aumentando.": "Medio ambiente",
    "las basuras no se recogen a tiempo.": "Medio ambiente",
    "las calles están muy oscuras y peligrosas.": "Seguridad",
    "necesitamos más acceso a internet en la zona.": "Educación",
    "no hay suficientes escuelas públicas.": "Educación",
    "no tenemos centros culturales ni bibliotecas.": "Educación",
    "queremos más presencia policial.": "Seguridad"
}
df['categoria_del_problema'] = df['comentario'].map(comentario_categoria)
# print(df)

# # =================== revisar categorias iguales ======================
# categorias_contadas = df.groupby('Categoría del problema').size().reset_index(name='cantidad')
# print(categorias_contadas)

# =========== Rellenar los valores nulos ========
df['edad'].fillna(48, inplace=True)
df['ciudad'].fillna('desconocida', inplace=True)
print(df.isnull().sum())


