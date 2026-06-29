import os
import pandas as pd
import requests
from sqlalchemy import create_engine, event

# 1️⃣ CONFIGURACIÓN DE RUTAS Y ENTRADAS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = "http://127.0.0.1:8000/api/economico"
CSV_PATH = os.path.join(BASE_DIR, "data", "bank-additional-full.csv") 

# URL de conexión a Docker (PostgreSQL)
DATABASE_URL = "postgresql+pg8000://postgres:12345678@localhost:5433/banco_db"

def ejecutar_etl():
    print("🚀 Iniciando el proceso ETL...")
    print("\n📥 [ETAPA: EXTRAER] Leyendo orígenes de datos...")
    
    # --- LEER CSV ---
    try:
        # Usamos latin-1 por si el archivo plano tiene caracteres europeos
        df_clientes = pd.read_csv(CSV_PATH, sep=';', encoding='latin-1')
        print(f"  ✅ CSV '{os.path.basename(CSV_PATH)}' cargado correctamente ({df_clientes.shape[0]} filas).")
    except Exception as e:
        print(f"  ❌ Error al leer el CSV: {e}")
        return

    # --- LEER API ---
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            # Forzamos latin-1 para absorber bytes conflictivos antes de que Pandas los procese
            response.encoding = 'latin-1' 
            df_economico = pd.DataFrame(response.json())
            print(f"  ✅ Datos de la API extraídos correctamente ({df_economico.shape[0]} filas).")
        else:
            print(f"  ❌ La API respondió con código de error: {response.status_code}")
            return
    except Exception as e:
        print(f"  ❌ Error al conectar con la API: {e}")
        return


    print("\n⚙️ [ETAPA: TRANSFORMAR] Normalizando y limpiando estructuras...")
    
    # 1. Eliminación de duplicados en ambos DataFrames
    df_clientes = df_clientes.drop_duplicates()
    df_economico = df_economico.drop_duplicates()

    # 2. Limpieza exhaustiva en nombres de columnas (Evitamos errores de metadatos en SQL)
    df_clientes.columns = df_clientes.columns.str.encode('latin-1', errors='ignore').str.decode('utf-8', errors='ignore')
    df_economico.columns = df_economico.columns.str.encode('latin-1', errors='ignore').str.decode('utf-8', errors='ignore')
    
    # Reemplazo directo de vocales con tildes comunes en los títulos por si la API mandó algo con acento
    reemplazos_letras = {'ó': 'o', 'á': 'a', 'é': 'e', 'í': 'i', 'ú': 'u', 'ñ': 'n', 'Ó': 'O'}
    for df in [df_clientes, df_economico]:
        for col in df.columns:
            nueva_col = col
            for k, v in reemplazos_letras.items():
                nueva_col = nueva_col.replace(k, v)
            if nueva_col != col:
                df.rename(columns={col: nueva_col}, inplace=True)
    
    # 3. Casteo seguro de textos internos a UTF-8 válido (Arregla el Warning de Pandas 2.0+)
    for col in df_clientes.select_dtypes(include=['object', 'string']).columns:
        df_clientes[col] = df_clientes[col].astype(str).str.encode('utf-8', errors='ignore').str.decode('utf-8')
        
    for col in df_economico.select_dtypes(include=['object', 'string']).columns:
        df_economico[col] = df_economico[col].astype(str).str.encode('utf-8', errors='ignore').str.decode('utf-8')

    print("  ✅ Transformación completada con éxito.")


    print("\n📤 [ETAPA: CARGAR] Inyectando datos en PostgreSQL (Docker)...")
    try:
        # Creamos el motor usando el driver pg8000 en el puerto correcto 5433
        engine = create_engine(DATABASE_URL)

        # Guardar DataFrame 1 (Clientes del CSV)
        df_clientes.to_sql('clientes', engine, if_exists='replace', index=False)
        print("  ✅ Tabla 'clientes' guardada con éxito en Docker.")
        
        # Guardar DataFrame 2 (Indicadores de la API)
        df_economico.to_sql('datos_economicos', engine, if_exists='replace', index=False)
        print("  ✅ Tabla 'datos_economicos' guardada con éxito en Docker.")
        
        print("\n🏆 ¡Proceso ETL finalizado con éxito total! Todo quedó en Postgres.")
    except Exception as e:
        print(f"  ❌ Error fatal al cargar en la base de datos: {e}")
if __name__ == "__main__":
    ejecutar_etl()