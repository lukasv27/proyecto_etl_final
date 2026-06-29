import pandas as pd
import os

# Rutas automáticas basadas en la estructura del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DATA_PATH = os.path.join(BASE_DIR, "data", "bank-additional-full.csv")

print("🔄 Leyendo el dataset original en /data/...")
df = pd.read_csv(ORIGINAL_DATA_PATH, sep=";")

# Creamos un ID único para amarrar los datos después
df.insert(0, 'id_cliente', range(1, len(df) + 1))

print("💾 Creando Fuente 1: CSV Estático en /data/ (Demografía)...")
df_csv = df[['id_cliente', 'age', 'job', 'marital', 'education', 'default', 'housing', 'loan']]
df_csv.to_csv(os.path.join(BASE_DIR, "data", "clientes_demografia.csv"), index=False)

print("🗄️ Creando Fuente 2: Para SQL en /data/ (Campañas)...")
df_sql = df[['id_cliente', 'duration', 'campaign', 'pdays', 'previous', 'poutcome', 'y']]
df_sql.to_csv(os.path.join(BASE_DIR, "data", "campanas_transaccional.csv"), index=False)

print("🌐 Creando Fuente 3: Para la API en /api/ (Económico)...")
df_api = df[['id_cliente', 'emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed']]
df_api.to_json(os.path.join(BASE_DIR, "api", "datos_api.json"), orient="records", indent=4)

print("✅ ¡Dataset dividido con éxito!")