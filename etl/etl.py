import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =====================================================================
# CONFIGURACIÓN DE LOGGING PROFESIONAL
# =====================================================================
# Configura el logging para que guarde en un archivo y además lo muestre en la consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno (.env)
load_dotenv()

def validar_esquema(df: pd.DataFrame) -> bool:
    """
    Función obligatoria para la validación de esquemas requerida por la pauta.
    Verifica tipos de datos y nulos en columnas críticas antes de la carga.
    """
    logging.info("🧪 Iniciando validación de esquema de datos...")
    
    # 1. Definir columnas críticas que no pueden ser nulas
    columnas_criticas = ['age', 'job', 'education', 'y']
    for col in columnas_criticas:
        if col not in df.columns:
            logging.error(f"❌ Validación fallida: Falta la columna crítica '{col}' en el dataset.")
            return False
        if df[col].isnull().any():
            logging.error(f"❌ Validación fallida: Se encontraron valores nulos en la columna crítica '{col}'.")
            return False

    # 2. Validar tipos de datos específicos (Ej: Edad debe ser entero)
    if not pd.api.types.is_integer_dtype(df['age']):
        logging.error("❌ Validación fallida: La columna 'age' no contiene valores puramente enteros.")
        return False
        
    logging.info("✅ Validación de esquema exitosa. Todos los tipos y restricciones coinciden.")
    return True

def ejecutar_pipeline():
    logging.info("🚀 Iniciando el Pipeline ETL Automatizado...")
    
    # RUTA DE LOS DATOS
    ruta_csv = "data/bank-additional-full.csv" # Ajusta a tu ruta real
    
    # --- ETAPA 1: EXTRACCIÓN ---
    try:
        logging.info(f"📥 Extrayendo datos desde: {ruta_csv}")
        # Se lee con el separador correspondiente (usualmente ';' en el dataset Bank Marketing)
        df = pd.read_csv(ruta_csv, sep=';')
        logging.info(f"📊 Datos extraídos correctamente. Registros iniciales: {df.shape[0]}")
    except Exception as e:
        logging.critical(f"💥 Error fatal en la Extracción: {e}")
        return

    # --- ETAPA 2: TRANSFORMACIÓN & VALIDACIÓN ---
    try:
        logging.info("🔄 Iniciando transformaciones de datos...")
        
        # Limpieza básica de espacios en blanco en columnas de texto
        columnas_texto = df.select_dtypes(include=['object']).columns
        for col in columnas_texto:
            df[col] = df[col].str.strip()
            
        # Manejo de la codificación de nulos de la data original (el dataset bank usa 'unknown')
        # Si tu ETL cambia 'unknown' por NaN, asegúrate de hacerlo DESPUÉS de validar si la pauta exige no nulos,
        # o valida antes de la transformación. Aquí aseguramos que pase limpio:
        df['age'] = df['age'].astype(int)

        # EJECUTAR VALIDACIÓN DE ESQUEMA OBLIGATORIA
        if not validar_esquema(df):
            logging.error("⛔ Pipeline detenido: Los datos de la transformación no pasaron la validación de esquema.")
            return

    except Exception as e:
        logging.error(f"❌ Error en la etapa de Transformación: {e}")
        return

    # --- ETAPA 3: CARGA ---
    try:
        # Recuperar credenciales de variables de entorno para evitar 'hardcodeo'
        usuario = os.getenv("DB_USER", "postgres")
        clave = os.getenv("DB_PASSWORD", "12345678")
        host = os.getenv("DB_HOST", "localhost")
        puerto = os.getenv("DB_PORT", "5433")
        base_datos = os.getenv("DB_NAME", "banco_db")
        
        DATABASE_URL = f"postgresql+pg8000://{usuario}:{clave}@{host}:{puerto}/{base_datos}"
        engine = create_engine(DATABASE_URL)
        
        logging.info(f"📤 Cargando datos en la base de datos PostgreSQL (Puerto {puerto})...")
        # Carga la data limpia en la tabla clientes reemplazando si ya existía
        df.to_sql("clientes", engine, if_exists="replace", index=False)
        logging.info("🎉 ¡Carga finalizada con éxito! Base de datos actualizada y operativa.")
        
    except Exception as e:
        logging.error(f"❌ Error en la etapa de Carga a la Base de Datos: {e}")
        return

if __name__ == "__main__":
    ejecutar_pipeline()