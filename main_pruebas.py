import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

# =========== Rellenar los valores nulos ========
df['edad'].fillna(48, inplace=True)
df['ciudad'].fillna('desconocida', inplace=True)
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

# ======= se cambia las ciudades a numeros ==================================
data = {
    'Ciudad': ['Barranquilla', 'Bogotá', 'Bucaramanga', 'Cali', 'Cartagena', 'Cúcuta', 'Manizales', 'Medellín', 'Pereira', 'Santa Marta'],
    'cantidad': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
df = pd.DataFrame(data)
# Crea un diccionario que asigna un número único a cada ciudad
ciudad_numero = {ciudad: numero for numero, ciudad in enumerate(df['ciudad'].unique(), start=1)}
# Reemplaza las ciudades por sus números correspondientes
df['ciudad'] = df['ciudad'].map(ciudad_numero)
print(df)

# # =================== revisar categorias iguales ======================
# categorias_contadas = df.groupby('Categoría del problema').size().reset_index(name='cantidad')
# print(categorias_contadas)

# ===== Revisar la cantidad de problemas por categoria en cada ciudad con grafica =========
comentarios_por_ciudad_categoria = df.groupby(['ciudad', 'categoria_del_problema']).size().reset_index(name='cantidad')
# Imprime la cantidad de comentarios para cada ciudad y categoría
for index, row in comentarios_por_ciudad_categoria.iterrows():
    ciudad = row['ciudad']
    categoría = row['categoria_del_problema']
    cantidad = row['cantidad']
    # print(f"Ciudad: {ciudad}, Categoría: {categoría}, Cantidad de comentarios: {cantidad}")
# Crear la gráfica de barras
plt.figure(figsize=(10, 6))
sns.barplot(
    data=comentarios_por_ciudad_categoria,
    x='ciudad',
    y='cantidad',
    hue='categoria_del_problema'
)
# Título y etiquetas
plt.title('Cantidad de comentarios por ciudad y categoría')
plt.xlabel('Ciudad')
plt.ylabel('Cantidad de comentarios')
# Muestra la leyenda y mejora la estética
plt.legend(title='Categoría del problema')
plt.xticks(rotation=45)
plt.tight_layout()
# Mostrar gráfica
plt.show()

print(df.head())
