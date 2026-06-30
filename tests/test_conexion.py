import os
import requests
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno para las pruebas
load_dotenv()

def test_api_online():
    """Prueba que la API RESTful de FastAPI responda correctamente."""
    print("\n[TEST] Verificando estado de la API RESTful...")
    url_api = "http://127.0.0.1:8000/api/economico"
    
    try:
        respuesta = requests.get(url_api, timeout=3)
        # Una aserción exitosa valida que el código de respuesta sea 200 OK
        assert respuesta.status_code == 200, f"Código de estado inesperado: {respuesta.status_code}"
        print("API RESTful: ONLINE (Status 200)")
    except AssertionError as ae:
        print(f"API RESTful: ERROR DE VALIDACIÓN -> {ae}")
        raise ae
    except Exception as e:
        print(f"API RESTful: ERROR DE CONEXIÓN -> El servidor no responde: {e}")
        raise e

def test_postgresql_docker_conexion():
    """Prueba la conexión directa a la base de datos relacional dentro de Docker."""
    print("[TEST] Verificando conexión a PostgreSQL en Docker...")
    
    usuario = os.getenv("DB_USER", "postgres")
    clave = os.getenv("DB_PASSWORD", "12345678")
    host = os.getenv("DB_HOST", "localhost")
    puerto = os.getenv("DB_PORT", "5433")
    base_datos = os.getenv("DB_NAME", "banco_db")
    
    DATABASE_URL = f"postgresql+pg8000://{usuario}:{clave}@{host}:{puerto}/{base_datos}"
    
    try:
        engine = create_engine(DATABASE_URL)
        # Intentamos abrir y cerrar una conexión real
        conexion = engine.connect()
        conexion.close()
        print("Docker PostgreSQL: CONEXIÓN INTEGRAL EXITOSA")
    except Exception as e:
        print(f"Docker PostgreSQL: FALLÓ LA CONEXIÓN -> Verifica el contenedor: {e}")
        raise e

if __name__ == "__main__":
    print("===================================================================")
    print("      EJECUTANDO EVALUACIÓN DE TESTING AUTOMATIZADO (DUOC UC)      ")
    print("===================================================================")
    
    try:
        test_api_online()
        test_postgresql_docker_conexion()
        print("\n ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100% LOGRO)!")
    except Exception:
        print("\n PRUEBAS FALLIDAS: Revisa los contenedores o servicios activos.")