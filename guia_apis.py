import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# --------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# --------------------------------------------
st.set_page_config(
    page_title="Guía SQLite & Plotly - API Usuarios",
    page_icon="🌐",
    layout="wide"
)

# --------------------------------------------
# ESTILOS PERSONALIZADOS
# --------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        color: #2C3E50;
    }
    .stButton>button {
        background-color: #2C3E50;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #34495E;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------
# CONSUMO DE API Y GUARDADO EN BASE DE DATOS
# --------------------------------------------
DB_NAME = 'usuarios_api.db'
API_URL = 'https://jsonplaceholder.typicode.com/users'

try:
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    users = response.json()
except Exception as e:
    st.error(f"❌ Error al consumir la API: {e}")
    st.stop()

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# Crear tabla
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    email TEXT,
    phone TEXT,
    website TEXT
)
""")

# Insertar datos
for u in users:
    cur.execute("""
        INSERT OR REPLACE INTO users (id, name, username, email, phone, website)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        u.get('id'), u.get('name'), u.get('username'),
        u.get('email'), u.get('phone'), u.get('website')
    ))
conn.commit()

# Leer datos
df = pd.read_sql_query('SELECT * FROM users', conn)
conn.close()

# --------------------------------------------
# COLUMNAS CALCULADAS
# --------------------------------------------
df['name_length'] = df['name'].astype(str).apply(len)
df['email_domain'] = df['email'].astype(str).apply(
    lambda x: x.split('@')[-1].lower() if '@' in x else None
)

# Columnas nuevas para Scatter y Bubble Chart
df['username_length'] = df['username'].astype(str).apply(len)
df['company_name_length'] = df['name'].astype(str).apply(len)  # temporal para Bubble Chart

# --------------------------------------------
# TABS PRINCIPALES
# --------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Inicio", "👥 Usuarios", "📈 Gráficos", "ℹ️ Acerca de"])

# --------------------------------------------
# TAB 1 - INICIO
# --------------------------------------------
with tab1:
    st.title("🌐 Guía Práctica: API + SQLite + Plotly + Streamlit")
    st.markdown("""
    Esta aplicación demuestra cómo consumir datos de una **API REST pública**, almacenarlos en **SQLite**,
    analizarlos con **pandas** y visualizarlos con **Plotly** en una interfaz hecha con **Streamlit**.
    """)
    st.success("✅ Datos cargados correctamente desde la API JSONPlaceholder.")
    st.dataframe(df, use_container_width=True)

# --------------------------------------------
# TAB 2 - USUARIOS
# --------------------------------------------
with tab2:
    st.header("👥 Análisis de Usuarios")
    st.write("Aquí puedes observar información procesada sobre los usuarios obtenidos de la API.")
    
    st.subheader("📋 Tabla procesada")
    st.dataframe(df[['id', 'name', 'name_length', 'email', 'email_domain']], use_container_width=True)

    # Exportar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Descargar datos en CSV",
        data=csv,
        file_name='usuarios_api.csv',
        mime='text/csv'
    )

# --------------------------------------------
# TAB 3 - GRÁFICOS
# --------------------------------------------
with tab3:
    st.header("📈 Visualización de Datos con Plotly")
    
    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Histograma de Longitud de Nombres")
            fig1 = px.histogram(df, x='name_length', nbins=10, 
                                title='Distribución de caracteres en los nombres')
            fig1.update_layout(xaxis_title='Cantidad de caracteres', yaxis_title='Frecuencia')
            st.plotly_chart(fig1, use_container_width=True)

            # 💾 Botón para exportar histograma
            html_bytes1 = fig1.to_html(include_plotlyjs='cdn').encode()
            st.download_button(
                label="💾 Descargar histograma HTML",
                data=html_bytes1,
                file_name="hist_name_length.html",
                mime="text/html",
                help="Exporta el gráfico del histograma como archivo HTML"
            )

        with col2:
            st.subheader("Usuarios por Dominio de Email")
            dom_counts = df['email_domain'].value_counts().reset_index()
            dom_counts.columns = ['email_domain', 'count']
            fig2 = px.bar(dom_counts, x='count', y='email_domain', orientation='h',
                          title='Usuarios por dominio de correo electrónico')
            fig2.update_layout(xaxis_title='Cantidad de usuarios', yaxis_title='Dominio')
            st.plotly_chart(fig2, use_container_width=True)

            # 💾 Botón para exportar gráfico de barras
            html_bytes2 = fig2.to_html(include_plotlyjs='cdn').encode()
            st.download_button(
                label="💾 Descargar gráfico de dominios HTML",
                data=html_bytes2,
                file_name="usuarios_por_dominio.html",
                mime="text/html",
                help="Exporta el gráfico de dominios como archivo HTML"
            )

        # Donut chart
        st.subheader("Distribución de dominios de email (Donut)")
        fig3 = px.pie(dom_counts, names='email_domain', values='count', hole=0.4)
        st.plotly_chart(fig3, use_container_width=True)

        # 💾 Botón para exportar donut
        html_bytes3 = fig3.to_html(include_plotlyjs='cdn').encode()
        st.download_button(
            label="💾 Descargar gráfico Donut HTML",
            data=html_bytes3,
            file_name="donut_email_domain.html",
            mime="text/html",
            help="Exporta el gráfico de tipo donut como archivo HTML"
        )

        # =============================================
        # NUEVAS GRÁFICAS AÑADIDAS
        # =============================================

        st.subheader("🌐 Gráfico de Dispersión (Scatter)")
        fig5 = px.scatter(
            df,
            x='username_length',
            y='name_length',
            title='Relación entre el username y longitud del nombre',
            color='name_length',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig5, use_container_width=True)

        html_bytes5 = fig5.to_html(include_plotlyjs='cdn').encode()
        st.download_button(
            label="💾 Descargar gráfico de dispersión HTML",
            data=html_bytes5,
            file_name="grafico_scatter.html",
            mime="text/html"
        )

        st.subheader("🫧 Gráfico de Burbujas (Bubble Chart)")
        fig6 = px.scatter(
            df,
            x='company_name_length',
            y='name_length',
            size='name_length',
            color='id',
            title='Burbujas por longitud de nombre y nombre de empresa',
            color_discrete_sequence=px.colors.qualitative.Bold,
            size_max=40
        )
        st.plotly_chart(fig6, use_container_width=True)

        html_bytes6 = fig6.to_html(include_plotlyjs='cdn').encode()
        st.download_button(
            label="💾 Descargar gráfico de burbujas HTML",
            data=html_bytes6,
            file_name="grafico_burbujas.html",
            mime="text/html"
        )

        # Tabla visual con Plotly
        st.subheader("Tabla Interactiva de Usuarios")
        fig4 = go.Figure(data=[go.Table(
            header=dict(values=list(df[['id','name','username','email','phone','website']].columns),
                        fill_color="#98bfe7", font=dict(color='white', size=12), align='left'),
            cells=dict(values=[df[c] for c in ['id','name','username','email','phone','website']],
                       align='left')
        )])
        fig4.update_layout(title='Usuarios (Tabla Interactiva)')
        st.plotly_chart(fig4, use_container_width=True)

        html_bytes4 = fig4.to_html(include_plotlyjs='cdn').encode()
        st.download_button(
            label="💾 Descargar tabla HTML",
            data=html_bytes4,
            file_name="tabla_usuarios.html",
            mime="text/html",
            help="Exporta la tabla interactiva como archivo HTML"
        )
    else:
        st.warning("⚠️ No hay datos disponibles para mostrar gráficos.")

# --------------------------------------------
# TAB 4 - ACERCA DE
# --------------------------------------------
with tab4:
    st.header("ℹ️ Acerca de la Aplicación")
    st.write("""
    Esta guía fue desarrollada como práctica educativa para aprender sobre:
    - **Consumo de APIs REST con Python (requests)**
    - **Bases de datos SQLite**
    - **Visualización de datos con Plotly**
    - **Desarrollo de interfaces con Streamlit**

    **Autor:** *Adriana Cornejo Ulloa*  
    **Institución:** Instituto Superior Universitario Tecnológico del Azuay  
    **Año:** 2025
    """)
    st.markdown("© 2025 Adriana Cornejo Ulloa. Todos los derechos reservados.")
