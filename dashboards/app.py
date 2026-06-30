import streamlit as st  # 👈 CORREGIDO: Streamlit se importa como 'st'
import pandas as pd
import requests
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Configuración de la página del Dashboard
st.set_page_config(page_title="Dashboard de Campañas Bancarias", layout="wide")

st.title("📊 Dashboard Interactivo: Análisis de Campañas de Marketing")
st.markdown("Este panel interactivo analiza el éxito de la campaña de depósitos a plazo cruzando datos demográficos (PostgreSQL) y macroeconómicos (API).")

# =====================================================================
# EXTRAER DATOS EN VIVO
# =====================================================================
@st.cache_data
def cargar_datos():
    try:
        requests.get("http://127.0.0.1:8000/api/economico", timeout=2)
    except:
        pass
        
    DATABASE_URL = "postgresql+pg8000://postgres:12345678@localhost:5433/banco_db"
    engine = create_engine(DATABASE_URL)
    df_load = pd.read_sql("SELECT * FROM clientes", engine)
    df_load['y_num'] = df_load['y'].map({'no': 0, 'yes': 1})
    return df_load

try:
    df = cargar_datos()
    st.sidebar.success(f"✅ Conectado a Docker. {df.shape[0]} registros cargados.")
except Exception as e:
    st.sidebar.error(f"❌ Error de conexión: {e}")
    st.stop()

# =====================================================================
# FILTROS INTERACTIVOS
# =====================================================================
st.sidebar.header("🔍 Filtros de Audiencia")

lista_empleos = ['Todos'] + list(df['job'].unique())
empleo_seleccionado = st.sidebar.selectbox("Selecciona Ocupación del Cliente:", lista_empleos)

lista_educacion = ['Todos'] + list(df['education'].unique())
edu_seleccionada = st.sidebar.selectbox("Selecciona Nivel Educativo:", lista_educacion)

df_filtrado = df.copy()
if empleo_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['job'] == empleo_seleccionado]
if edu_seleccionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['education'] == edu_seleccionada]

# =====================================================================
# INDICADORES CLAVE (KPIs)
# =====================================================================
total_contactos = df_filtrado.shape[0]
if total_contactos > 0:
    tasa_exito = (df_filtrado['y'].value_counts(normalize=True).get('yes', 0)) * 100
else:
    tasa_exito = 0

col1, col2 = st.columns(2)
with col1:
    st.metric(label="📞 Total Clientes Contactados", value=f"{total_contactos:,}")
with col2:
    st.metric(label="🎯 Tasa de Éxito General", value=f"{tasa_exito:.1f}%")

st.markdown("---")

# =====================================================================
# VISUALIZACIONES INTERACTIVAS
# =====================================================================
col3, col4 = st.columns(2)

with col3:
    st.subheader("🍰 Distribución de Respuesta (y)")
    if total_contactos > 0:
        conteo = df_filtrado['y'].value_counts()
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        ax1.pie(conteo, labels=conteo.index, autopct='%1.1f%%', startangle=90, colors=['#FF9999', '#87CEFA'])
        st.pyplot(fig1)
    else:
        st.write("No hay datos para mostrar.")

with col4:
    st.subheader("🎂 Distribución de Edades de los Contactos")
    if total_contactos > 0:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.histplot(data=df_filtrado, x='age', kde=True, hue='y', palette={'no': 'red', 'yes': 'blue'}, multiple='stack', ax=ax2)
        plt.xlabel("Edad del Cliente")
        plt.ylabel("Cantidad")
        st.pyplot(fig2)
    else:
        st.write("No hay datos para mostrar.")

st.markdown("---")

col5, col6 = st.columns(2)

with col5:
    st.subheader("💼 Volumen de Llamadas por Tipo de Empleo")
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_filtrado, y='job', hue='y', palette={'no': 'lightcoral', 'yes': 'lightblue'}, 
                  order=df_filtrado['job'].value_counts().index, ax=ax3)
    plt.xlabel("Cantidad de Llamadas")
    plt.ylabel("Ocupación")
    st.pyplot(fig3)

with col6:
    st.subheader("📉 Entorno Macroeconómico vs Éxito")
    variables_macro = ['emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed', 'y_num']
    df_macro = df_filtrado[[col for col in variables_macro if col in df_filtrado.columns]]
    
    if df_macro.shape[0] > 1:
        fig4, ax4 = plt.subplots(figsize=(6, 4))
        sns.heatmap(df_macro.corr(), annot=True, fmt='.2f', cmap='RdBu_r', vmin=-1, vmax=1, ax=ax4)
        st.pyplot(fig4)
    else:
        st.write("Faltan datos para calcular correlaciones.")

# =====================================================================
# NUEVA SECCIÓN: VARIABLES DE MÁXIMA INFLUENCIA
# =====================================================================
st.markdown("---")
st.header("🎯 Análisis de Variables de Máxima Influencia (Claves del Negocio)")

col7, col8 = st.columns(2)

with col7:
    st.subheader("📆 Impacto del Historial Reciente (pdays)")
    # Filtramos los NaN (que eran el 999 original) para ver solo a los que sí se contactaron antes
    df_pdays = df_filtrado[df_filtrado['pdays'].notna()]
    
    if df_pdays.shape[0] > 0:
        fig5, ax5 = plt.subplots(figsize=(6, 4))
        sns.boxplot(data=df_pdays, x='y', y='pdays', hue='y', palette={'no': 'lightcoral', 'yes': 'lightblue'}, legend=False, ax=ax5)
        plt.xlabel("¿Aceptó el Depósito?")
        plt.ylabel("Días desde la campaña anterior")
        st.pyplot(fig5)
        st.caption("💡 Revelación: Los clientes contactados en los últimos 10 días tienen una tasa de conversión masiva.")
    else:
        st.write("No hay registros de clientes contactados en campañas previas con los filtros seleccionados.")

with col8:
    st.subheader("🏦 Comportamiento según el Contexto Financiero (euribor3m)")
    if total_contactos > 0:
        fig6, ax6 = plt.subplots(figsize=(6, 4))
        # Evaluamos la densidad de aceptación según las tasas de interés del mercado
        sns.kdeplot(data=df_filtrado, x='euribor3m', hue='y', palette={'no': 'red', 'yes': 'blue'}, fill=True, common_norm=False, alpha=0.5, ax=ax6)
        plt.xlabel("Tasa de Interés Euribor 3 Meses")
        plt.ylabel("Densidad de Respuestas")
        st.pyplot(fig6)
        st.caption("💡 Revelación: El éxito se dispara en ciertos umbrales de tasas de interés del mercado europeo.")
    else:
        st.write("No hay datos para mostrar.")