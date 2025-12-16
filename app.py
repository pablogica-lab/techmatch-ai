import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="TechMatch AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "LIMPIEZA QUIRÚRGICA" ---
# Quitamos los márgenes gigantes de Streamlit para que parezca una App compacta
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Reducir espacio en blanco arriba */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }

        /* Slider Verde */
        div[data-baseweb="slider"] div[class*="thumb"] {
            background-color: #00FF9D !important;
            border-color: #00FF9D !important;
        }
        div[data-baseweb="slider"] div[class*="tick-bar"] {
            background-color: #00FF9D !important;
        }
        div[data-baseweb="slider"] div[class*="bar-fill"] {
            background-color: #00FF9D !important;
        }

        /* Métricas más compactas */
        div[data-testid="stMetric"] {
            background-color: #161920;
            border: 1px solid #262a33;
            border-radius: 8px;
            padding: 10px;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
            color: #00FF9D !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATOS ---
def obtener_precio_minimo(rango_texto):
    try:
        if isinstance(rango_texto, str):
            primer_valor = rango_texto.split('-')[0].strip()
            return float(primer_valor)
        return 0.0
    except:
        return 0.0

def cargar_datos():
    conn = sqlite3.connect("techmatch_db.sqlite")
    df = pd.read_sql_query("SELECT * FROM precios_competencia ORDER BY fecha DESC", conn)
    conn.close()
    df['precio_base'] = df['rango_precios_detectado'].apply(obtener_precio_minimo)
    return df

# --- 4. INTERFAZ ---

# Header Compacto
c1, c2 = st.columns([0.5, 10])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/1925/1925047.png", width=45)
with c2:
    st.markdown("<h2 style='margin:0; padding:0;'>TechMatch <span style='color:#00FF9D'>AI</span></h2>", unsafe_allow_html=True)
    st.caption("v1.2 | Market Intelligence System")

st.markdown("---")

try:
    df = cargar_datos()

    if df.empty:
        st.error("⚠️ Sin datos.")
    else:
        # --- SIDEBAR ---
        with st.sidebar:
            st.markdown("### 🎛️ Filtros")
            presupuesto = st.slider("Presupuesto Máximo (€)", 0, 1000, 100, 10)
            
            competidores_top = df['competidor'].unique()
            seleccion = st.multiselect("Competidores", competidores_top, default=competidores_top)
            
            st.write("---")
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()

        # Lógica
        df_filtrado = df[df['precio_base'] <= presupuesto]
        df_filtrado = df_filtrado[df_filtrado['competidor'].isin(seleccion)]
        df_filtrado = df_filtrado.sort_values(by='precio_base')

        # --- KPI ROW (Compacta) ---
        if not df_filtrado.empty:
            k1, k2, k3, k4 = st.columns(4)
            best_price = df_filtrado.iloc[0]['precio_base']
            best_name = df_filtrado.iloc[0]['competidor']
            
            k1.metric("Opciones", f"{len(df_filtrado)}")
            k2.metric("Mejor Precio", f"{best_price} €")
            k3.metric("Ganador", best_name)
            k4.metric("Total DB", f"{len(df)}")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SISTEMA DE PESTAÑAS (TABS) ---
            # Esto es lo que le da el toque "App" profesional
            tab1, tab2, tab3 = st.tabs(["📊 ANÁLISIS VISUAL", "📋 BASE DE DATOS", "📥 EXPORTAR"])

            with tab1:
                # GRÁFICO MEJORADO (Barras más finas y elegantes)
                chart = alt.Chart(df_filtrado).mark_bar(
                    color='#00FF9D',
                    cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3,
                    size=40  # <--- Barras más finas, menos toscas
                ).encode(
                    x=alt.X('competidor', title=None, axis=alt.Axis(labelAngle=0, labelColor='white')),
                    y=alt.Y('precio_base', title='Precio (€)', axis=alt.Axis(labelColor='white', gridColor='#333')),
                    tooltip=['competidor', 'precio_base']
                ).properties(
                    height=350,
                    background='transparent'
                ).configure_view(strokeWidth=0)
                
                st.altair_chart(chart, use_container_width=True)
                
                st.info(f"💡 **Insight:** {best_name} es actualmente la opción líder por precio.")

            with tab2:
                # Tabla limpia
                st.dataframe(
                    df_filtrado[['competidor', 'precio_base', 'url_origen']],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "competidor": "Plataforma",
                        "precio_base": st.column_config.NumberColumn("Precio", format="%d €"),
                        "url_origen": st.column_config.LinkColumn("Enlace Oficial")
                    }
                )

            with tab3:
                st.write("Zona de descargas (Próximamente)")
                st.download_button(
                    label="📥 Descargar Informe CSV",
                    data=df_filtrado.to_csv().encode('utf-8'),
                    file_name='reporte_techmatch.csv',
                    mime='text/csv',
                )

        else:
            st.warning(f"No hay herramientas por menos de {presupuesto}€")

except Exception as e:
    st.error(f"Error: {e}")