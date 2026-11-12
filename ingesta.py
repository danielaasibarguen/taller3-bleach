"""
Taller 3 — Ingesta de datos crudos (RAW) de la Bleach API a MongoDB.

Autora: Daniela Alejandra Salazar
Curso:  Bases de Datos para Ciencia de Datos

Flujo:
  1. Pide a la API la lista de nombres de cada categoría
     (shinigami, humans, quincy, arrancar).
  2. Por cada nombre pide el detalle completo del personaje.
  3. Guarda el JSON tal cual llega en MongoDB:
        base de datos  -> taller3_db
        colección      -> raw_data
     usando el "id" que entrega la API como _id del documento.
     Se usa replace_one(..., upsert=True), así que si el script se
     ejecuta varias veces NO se duplican los registros.

Uso:
    python ingesta.py
"""

import os
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# --- Configuración -----------------------------------------------------------
BASE_URL = os.getenv("BLEACH_API_URL", "https://bleach-api-8v2r.onrender.com")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "taller3_db"
COLLECTION_NAME = "raw_data"

CATEGORIAS = ["shinigami", "humans", "quincy", "arrancar"]
TIMEOUT = 90          # segundos; el servidor gratuito de Render "despierta" lento
REINTENTOS = 3
PAUSA = 0.2           # pausa entre peticiones para no saturar la API


def get_json(url: str):
    """GET con reintentos. Devuelve el JSON de la respuesta."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"   ! Error en {url} (intento {intento}/{REINTENTOS}): {e}")
            time.sleep(3 * intento)
    raise RuntimeError(f"No se pudo obtener {url}")


def listar_nombres(categoria: str) -> list[str]:
    """Devuelve la lista de nombres de personajes de una categoría."""
    data = get_json(f"{BASE_URL}/characters/{categoria}")
    return data.get(categoria, [])


def detalle_personaje(categoria: str, nombre: str):
    """
    Busca el detalle de un personaje. La API busca por el id en minúsculas
    con guiones bajos (ej: 'Byakuya Kuchiki' -> 'byakuya_kuchiki') y puede
    devolver varias coincidencias, así que nos quedamos con la que tenga
    exactamente el mismo nombre.
    """
    consulta = nombre.lower().replace(" ", "_")
    data = get_json(f"{BASE_URL}/characters/{categoria}/{quote(consulta)}")
    resultados = data.get("results", [])
    if not resultados:
        return None
    for doc in resultados:
        if doc.get("name", {}).get("english") == nombre:
            return doc
    return resultados[0]


def main():
    print(f"Conectando a MongoDB en {MONGO_URI} ...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # falla rápido si Mongo no está corriendo
    coleccion = client[DB_NAME][COLLECTION_NAME]

    print(f"Consultando la API: {BASE_URL}")
    print("(La primera petición puede tardar ~1 minuto mientras el servidor despierta)\n")
    get_json(f"{BASE_URL}/")

    total, fallidos = 0, []
    for categoria in CATEGORIAS:
        nombres = listar_nombres(categoria)
        print(f"[{categoria}] {len(nombres)} personajes encontrados")

        for nombre in nombres:
            doc = detalle_personaje(categoria, nombre)
            if doc is None:
                fallidos.append(f"{categoria}/{nombre}")
                continue

            # El JSON se guarda tal cual llega de la API.
            # Solo se agregan: _id (el id de la API, para evitar duplicados)
            # y dos metadatos de ingesta con prefijo "_" para distinguirlos.
            doc["_id"] = doc["id"]
            doc["_categoria_api"] = categoria
            doc["_fecha_ingesta"] = datetime.now(timezone.utc)

            coleccion.replace_one({"_id": doc["_id"]}, doc, upsert=True)
            total += 1
            time.sleep(PAUSA)

    print(f"\nPersonajes procesados en esta ejecución: {total}")
    if fallidos:
        print(f"No se encontró el detalle de {len(fallidos)}: {fallidos}")
    print(f"Documentos en {DB_NAME}.{COLLECTION_NAME}: {coleccion.count_documents({})}")
    client.close()


if __name__ == "__main__":
    main()
