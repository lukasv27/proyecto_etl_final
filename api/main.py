from fastapi import FastAPI, HTTPException
import json
import os

app = FastAPI(
    title="API de Indicadores Económicos - Proyecto ETL",
    description="Esta API expone los datos socioeconómicos de los clientes bancarios",
    version="1.0.0"
)

# Ruta para encontrar el JSON que se creó en la misma carpeta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "datos_api.json")

def cargar_datos():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/")
def inicio():
    return {"mensaje": "API del Banco funcionando correctamente. Ve a /docs para ver la documentación."}

# Endpoint que usará tu proceso ETL para llevarse todos los datos económicos
@app.get("/api/economico")
def obtener_todos_los_datos():
    datos = cargar_datos()
    if not datos:
        raise HTTPException(status_code=404, detail="No se encontraron datos económicos")
    return datos