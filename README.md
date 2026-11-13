# Taller 3 — APIs Públicas, MongoDB y EDA: personajes de *Bleach*

**Autora:** Daniela Alejandra Salazar
**Curso:** Bases de Datos para Ciencia de Datos — Docente: Miguel Ramos García

Proyecto que simula un flujo real de Ciencia de Datos:

1. **Extracción:** se consume una API pública con información de los personajes del anime/manga *Bleach*.
2. **Almacenamiento RAW:** el JSON se guarda sin transformar en MongoDB (`taller3_db.raw_data`).
3. **Transformación y análisis (EDA):** en un Jupyter Notebook se seleccionan variables clave, se limpian y se generan insights estadísticos y gráficos.

## API utilizada

**Bleach API** — <https://bleach-api-8v2r.onrender.com>

- Pública, gratuita y **sin API key**.
- Datos tomados de la [Bleach Fandom Wiki](https://bleach.fandom.com).
- Organiza a los personajes en 4 categorías: `shinigami`, `humans`, `quincy` y `arrancar` (**221 personajes** en total).

| Endpoint | Qué devuelve |
|---|---|
| `GET /characters/{categoria}` | Lista de nombres de la categoría |
| `GET /characters/{categoria}/{nombre}` | Detalle completo del personaje (búsqueda por id en minúsculas, ej. `byakuya_kuchiki`) |

> El servidor está en el plan gratuito de Render: si lleva tiempo sin uso, la **primera petición puede tardar ~1 minuto** mientras "despierta". El script ya contempla esto.

## Estructura del repositorio

```text
.
├── ingesta.py          # Extracción desde la API y carga RAW a MongoDB
├── analisis.ipynb      # EDA: selección de variables, limpieza, insights y gráficos
├── requirements.txt    # Librerías necesarias
├── .env.example        # Variables de entorno de ejemplo
├── .gitignore
└── README.md
```

## Requisitos previos

- Python 3.10+
- MongoDB Community Server corriendo en local (`mongodb://localhost:27017`) **o** un clúster de MongoDB Atlas
- MongoDB Compass (opcional, para ver la colección)

## Cómo ejecutarlo

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/taller3-bleach.git
cd taller3-bleach

# 2. Crear y activar un entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Configurar la conexión a MongoDB
#    Copia .env.example como .env y cambia MONGO_URI si usas Atlas.

# 5. Descargar los datos y guardarlos en MongoDB
python ingesta.py

# 6. Abrir el notebook y ejecutar todas las celdas
jupyter notebook analisis.ipynb
```

## Ingesta (`ingesta.py`)

- Recorre las 4 categorías, pide la lista de nombres y luego el detalle de cada personaje (**221 documentos**, más de los 100 requeridos).
- Se conecta a MongoDB, usa la base de datos **`taller3_db`** y la colección **`raw_data`**.
- Inserta el **JSON completo tal como llega de la API, sin modificarlo**. Como `_id` del documento se usa el `id` que entrega la API (ej. `"byakuya_kuchiki"`).
- Usa `replace_one(..., upsert=True)`: si el script se ejecuta varias veces, **no se duplican documentos**.

## Análisis (`analisis.ipynb`)

**Variables seleccionadas (10):** `nombre`, `categoria`, `raza`, `genero`, `altura_cm`, `peso_kg`, `capitulo_debut`, `num_citas`, `num_imagenes`, `tiene_bankai`.

**Limpieza:** se eliminan 6 páginas grupales que no son personajes individuales, se convierten textos como `"180 cm (5'11\")"` a números, y se traducen categorías y géneros al español. Quedan 215 personajes.

**Insights calculados:**
1. Número de personajes por categoría.
2. Distribución por género.
3. Estatura promedio, personaje más alto y más bajo, y estatura promedio por categoría.
4. Personajes con más imágenes y más citas en la wiki.
5. Porcentaje de Shinigami con bankai revelado.

**Gráficos:**
1. Torta: proporción de personajes por género.
2. Barras: estatura promedio por categoría.
3. Histograma: capítulo del manga en que debuta cada personaje, por categoría.

## Principales hallazgos

- Los **Shinigami** son casi la mitad de los personajes (99 de 215).
- Hay unos **2,5 personajes masculinos por cada femenino**.
- Los **Arrancar** son los más altos en promedio (~182 cm) y los **Humanos** los más bajos (~163 cm).
- **Ichigo Kurosaki** tiene casi el doble de imágenes en la wiki que cualquier otro personaje.
- Solo **22 de 99 Shinigami (22 %)** tienen un bankai con nombre revelado.
- Los datos reflejan los arcos de la historia: Humanos al inicio, Arrancar a mitad del manga y Quincy en el arco final.
