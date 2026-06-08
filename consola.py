"""
Ghostbusters Arcade - Dashboard de Estadísticas (Versión Simplificada)
Requiere: pip install mysql-connector-python pandas matplotlib streamlit
"""
import os
import streamlit as st
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

HOST     = os.getenv("DB_HOST")
PORT     = int(os.getenv("DB_PORT", 17254))
USUARIO  = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
BASE     = os.getenv("DB_NAME")
SSL_CA = os.getenv("SSL_CA_PATH", "ca.pem") 

@st.cache_data(ttl=60)
def obtener_datos():
    try:
        conexion = mysql.connector.connect(
            host=HOST, 
            port=PORT, 
            user=USUARIO, 
            password=PASSWORD,
            database=BASE, 
            ssl_ca=SSL_CA  
        )
        query = "SELECT * FROM partidas ORDER BY fecha_hora DESC"
        df = pd.read_sql(query, conexion)
        conexion.close()
        return df
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return pd.DataFrame()

# CARGA DE DATOS
df_datos = obtener_datos()

if df_datos.empty:
    st.warning("La base de datos está vacía.")
    st.stop()

st.set_page_config(page_title="Datos GhostBusters", layout="wide")

st.title("Datos Ghostbusters")
st.markdown("Gestión de puntuaciones y rendimiento de jugadores.")

# BARRA LATERAL
with st.sidebar:
    st.header("Ajustes")
    
    # Filtro por Jugador 
    jugadores_disponibles = ["Todos"] + df_datos["nombre_jugador"].unique().tolist()
    jugador_seleccionado = st.selectbox("Filtrar por Jugador", options=jugadores_disponibles)
    
    # Filtro por Nivel 
    nivel_min = int(df_datos["nivel_alcanzado"].min())
    nivel_max = int(df_datos["nivel_alcanzado"].max())
    rango_niveles = st.slider("Rango de Niveles", nivel_min, nivel_max, (nivel_min, nivel_max))

df_filtrado = df_datos.copy()

if jugador_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["nombre_jugador"] == jugador_seleccionado]

df_filtrado = df_filtrado[
    (df_filtrado["nivel_alcanzado"] >= rango_niveles[0]) & 
    (df_filtrado["nivel_alcanzado"] <= rango_niveles[1])
]

tab1, tab2 = st.tabs(["Gráficos Estadísticos", "Datos y Backups"])

with tab1:
    # Cuadros de resumen
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Partidas", len(df_filtrado))
    m2.metric("Récord Puntos", int(df_filtrado["puntuacion_final"].max()) if not df_filtrado.empty else 0)
    m3.metric("Fantasmas Atrapados", int(df_filtrado["fantasmas_atrapados"].sum()))
    m4.metric("Media Tiempo (s)", round(df_filtrado["tiempo_segundos"].mean(), 1) if not df_filtrado.empty else 0)
    
    st.markdown("---")
    
    if not df_filtrado.empty:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Mejores Puntuaciones")
            top_df = df_filtrado.sort_values("puntuacion_final", ascending=False).head(10)
            #top_df['ranking'] = [f"{i+1}. {nombre}" for i, nombre in enumerate(top_df['nombre_jugador'])]
            top_df['ranking'] = [f"{i+1:02d}. {nombre}" for i, nombre in enumerate(top_df['nombre_jugador'])]
            st.bar_chart(data=top_df.set_index("ranking")["puntuacion_final"], width='stretch')
            
        with col_g2:
            st.subheader("Partidas según Nivel")
            conteo = df_filtrado["nivel_alcanzado"].value_counts().sort_index()
            st.line_chart(conteo)
            
    st.markdown("---")
    st.subheader("Ranking de Jugadores (Estadísticas Globales)")
    
    if not df_filtrado.empty:
        df_ranking = df_filtrado.groupby("nombre_jugador").agg(
            Partidas_Jugadas=('nombre_jugador', 'count'),
            Puntuacion_Maxima=('puntuacion_final', 'max'),
            Fantasmas_Totales=('fantasmas_atrapados', 'sum'),
            Nivel_Mas_Alto=('nivel_alcanzado', 'max')
        ).reset_index()

        df_ranking = df_ranking.sort_values(by="Puntuacion_Maxima", ascending=False)
        
        df_ranking = df_ranking.rename(columns={"nombre_jugador": "Jugador"})
        
        st.dataframe(df_ranking, width='stretch', hide_index=True)

with tab2:
    st.subheader("Explorador de registros")
    
    nombre_buscado = st.text_input("Buscar jugador por nombre:").strip()
    df_tabla = df_filtrado.copy()
    
    if nombre_buscado != "":
        df_tabla = df_tabla[df_tabla["nombre_jugador"].str.contains(nombre_buscado)]

    st.dataframe(df_tabla, width='stretch', hide_index=True)

    st.markdown("---")
    st.subheader("Copia de seguridad")
    
    # SISTEMA DE BACKUP
    csv_data = df_datos.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Descargar BackUp",
        data=csv_data,
        file_name="backup_partidas_ghostbusters.csv",
        mime="text/csv"
    )