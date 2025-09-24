#!/usr/bin/env python3
"""
Sistema Unificado de Análisis de Quiniela Loteka
Interfaz simplificada con 3 secciones principales
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Importar los nuevos servicios unificados
from unified_prediction_service import UnifiedPredictionService
from unified_analytics_engine import UnifiedAnalyticsEngine
from database import DatabaseManager

# Configuración de página
st.set_page_config(
    page_title="Quiniela Loteka - Sistema Unificado",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para interfaz moderna y mejor contraste
st.markdown("""
<style>
    /* Variables CSS para paleta de colores moderna */
    :root {
        --primary-600: #4F46E5;
        --primary-700: #4338CA;
        --primary-50: #EEF2FF;
        --primary-100: #E0E7FF;
        --primary-200: #C7D2FE;
        --secondary-600: #059669;
        --secondary-700: #047857;
        --accent-500: #F59E0B;
        --accent-600: #D97706;
        --danger-500: #EF4444;
        --danger-600: #DC2626;
        --neutral-50: #FAFAFA;
        --neutral-100: #F5F5F5;
        --neutral-200: #E5E5E5;
        --neutral-300: #D1D5DB;
        --neutral-700: #374151;
        --neutral-800: #1F2937;
        --neutral-900: #111827;
        --glass-bg: rgba(255, 255, 255, 0.1);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    /* Fuentes y tipografía moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Header principal con diseño moderno */
    .main-header {
        background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 3rem;
        text-align: center;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        opacity: 0.3;
        pointer-events: none;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
        margin: 0;
    }
    
    /* Tarjetas de métricas modernizadas */
    .metric-card {
        background: white;
        padding: 1.75rem;
        border-radius: 16px;
        border: 1px solid var(--neutral-200);
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, var(--primary-600), var(--primary-700));
        border-radius: 0 2px 2px 0;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-200);
    }
    
    /* Tarjetas de predicción con efecto glass */
    .prediction-card {
        background: linear-gradient(135deg, var(--primary-600), #6366F1, var(--primary-700));
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-lg);
        position: relative;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .prediction-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        opacity: 0.3;
        pointer-events: none;
        border-radius: inherit;
    }
    
    .prediction-card h4 {
        font-weight: 600;
        margin-bottom: 0.75rem;
        font-size: 1.25rem;
    }
    
    .prediction-card p {
        margin-bottom: 0.5rem;
        opacity: 0.95;
        line-height: 1.6;
    }
    
    /* Indicadores de confianza mejorados */
    .confidence-high {
        border-left: 4px solid var(--secondary-600) !important;
        background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%) !important;
        border-color: var(--secondary-600) !important;
        color: #065F46 !important;
    }
    
    .confidence-high::before {
        background: linear-gradient(to bottom, var(--secondary-600), var(--secondary-700)) !important;
    }
    
    .confidence-medium {
        border-left: 4px solid var(--accent-500) !important;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%) !important;
        border-color: var(--accent-500) !important;
        color: #92400E !important;
    }
    
    .confidence-medium::before {
        background: linear-gradient(to bottom, var(--accent-500), var(--accent-600)) !important;
    }
    
    .confidence-low {
        border-left: 4px solid var(--danger-500) !important;
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%) !important;
        border-color: var(--danger-500) !important;
        color: #991B1B !important;
    }
    
    .confidence-low::before {
        background: linear-gradient(to bottom, var(--danger-500), var(--danger-600)) !important;
    }

    /* Estilos específicos para modo oscuro */
    @media (prefers-color-scheme: dark) {
        .confidence-high {
            background: linear-gradient(135deg, #064E3B 0%, #065F46 100%) !important;
            color: #A7F3D0 !important;
            border-left-color: #10B981 !important;
        }
        
        .confidence-medium {
            background: linear-gradient(135deg, #92400E 0%, #B45309 100%) !important;
            color: #FDE68A !important;
            border-left-color: #F59E0B !important;
        }
        
        .confidence-low {
            background: linear-gradient(135deg, #991B1B 0%, #B91C1C 100%) !important;
            color: #FECACA !important;
            border-left-color: #EF4444 !important;
        }
    }

    /* Detectar modo oscuro de Streamlit específicamente */
    [data-theme="dark"] .confidence-high,
    .stApp[data-theme="dark"] .confidence-high {
        background: linear-gradient(135deg, #064E3B 0%, #065F46 100%) !important;
        color: #A7F3D0 !important;
        border-left-color: #10B981 !important;
    }
    
    [data-theme="dark"] .confidence-medium,
    .stApp[data-theme="dark"] .confidence-medium {
        background: linear-gradient(135deg, #92400E 0%, #B45309 100%) !important;
        color: #FDE68A !important;
        border-left-color: #F59E0B !important;
    }
    
    [data-theme="dark"] .confidence-low,
    .stApp[data-theme="dark"] .confidence-low {
        background: linear-gradient(135deg, #991B1B 0%, #B91C1C 100%) !important;
        color: #FECACA !important;
        border-left-color: #EF4444 !important;
    }
    
    /* Botones modernos con efectos */
    .nav-button, .stButton > button {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-700)) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 12px !important;
        margin: 0.25rem !important;
        cursor: pointer !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    .nav-button:hover, .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(135deg, var(--primary-700), #4338CA) !important;
    }
    
    .nav-button:active, .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    /* Tabs modernos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: var(--neutral-50);
        padding: 0.5rem;
        border-radius: 16px;
        border: 1px solid var(--neutral-200);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: var(--neutral-700);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--primary-600) !important;
        box-shadow: var(--shadow-sm);
    }
    
    /* Inputs y selectores */
    .stSelectbox > div > div, .stSlider > div > div {
        border-radius: 12px !important;
        border-color: var(--neutral-200) !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary-600) !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
    }
    
    /* Métricas de Streamlit */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid var(--neutral-200);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    /* Alertas y notificaciones */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid var(--neutral-200) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%) !important;
        border-color: var(--secondary-600) !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%) !important;
        border-color: var(--accent-500) !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%) !important;
        border-color: var(--danger-500) !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%) !important;
        border-color: var(--primary-600) !important;
    }
    
    /* DataFrames modernos */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    /* Spinner personalizado */
    .stSpinner > div {
        border-color: var(--primary-600) !important;
    }
    
    /* Scrollbars personalizados */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--neutral-100);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--neutral-300);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-600);
    }
    
    /* Animaciones para componentes interactivos */
    .stButton > button, .metric-card, .prediction-card, .stTabs [data-baseweb="tab"], [data-testid="metric-container"] {
        transition: box-shadow 0.3s ease, transform 0.3s ease;
    }
    
    /* Media queries para responsive */
    @media (max-width: 768px) {
        .main-header {
            padding: 2rem 1rem;
            border-radius: 16px;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-card, .prediction-card {
            padding: 1.25rem;
            border-radius: 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_database():
    """Inicializa solo la base de datos"""
    return DatabaseManager()

@st.cache_resource
def initialize_prediction_service(_db):
    """Inicializa el servicio de predicciones de manera diferida"""
    return UnifiedPredictionService(_db)

@st.cache_resource  
def initialize_analytics_engine(_db):
    """Inicializa el motor de análisis de manera diferida"""
    return UnifiedAnalyticsEngine(_db)

def main():
    """Función principal de la aplicación"""
    
    # Header principal - renderizar INMEDIATAMENTE para evitar "Please wait..."
    st.markdown("""
    <div class="main-header">
        <h1>🎲 Quiniela Loteka - Sistema de Análisis Unificado</h1>
        <p>Predicciones inteligentes basadas en análisis estadístico avanzado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navegación principal - crear tabs inmediatamente
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard Overview", 
        "🎯 Prediction Lab", 
        "🔍 Pattern Analysis",
        "📈 Data & Performance"
    ])
    
    # Inicializar solo la base de datos inmediatamente (operación mínima)
    if 'db_initialized' not in st.session_state:
        try:
            st.session_state.db = initialize_database()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"❌ Error al conectar con la base de datos: {e}")
            st.stop()
    
    db = st.session_state.db
    
    with tab1:
        # Vista inicial ligera - no cargar nada pesado automáticamente
        st.header("📊 Bienvenido al Sistema de Análisis")
        
        st.markdown("""
        ### 🎲 Sistema Unificado de Quiniela Loteka
        
        Este dashboard te permite analizar patrones históricos y generar predicciones inteligentes 
        para la Quiniela Loteka utilizando análisis estadístico avanzado.
        
        #### ¿Qué puedes hacer aquí?
        - 📈 **Análisis de Datos**: Visualiza tendencias y patrones históricos
        - 🎯 **Predicciones**: Genera recomendaciones basadas en múltiples estrategias  
        - 🔍 **Análisis de Patrones**: Descubre correlaciones y secuencias
        - 📊 **Rendimiento**: Monitorea la efectividad del sistema
        """)
        
        st.divider()
        
        # Botón para cargar el resumen completo  
        if st.button("🚀 Cargar Resumen Completo del Sistema", type="primary", use_container_width=True):
            # Inicializar analytics engine solo cuando el usuario lo solicite
            if 'analytics_engine' not in st.session_state:
                with st.spinner("🔄 Inicializando motor de análisis..."):
                    try:
                        st.session_state.analytics_engine = initialize_analytics_engine(db)
                    except Exception as e:
                        st.error(f"❌ Error al inicializar análisis: {e}")
                        st.stop()
            
            # Marcar que debe mostrar el dashboard
            st.session_state.show_dashboard = True
            st.rerun()
        
        # Mostrar dashboard solo si se solicitó
        if st.session_state.get('show_dashboard', False):
            if 'analytics_engine' in st.session_state:
                render_dashboard_overview(st.session_state.analytics_engine)
            else:
                st.warning("⚠️ Motor de análisis no inicializado. Haz clic en el botón de arriba.")
    
    with tab2:
        # Inicializar servicios solo cuando se necesiten
        if 'prediction_service' not in st.session_state:
            with st.spinner("🔄 Inicializando servicio de predicciones..."):
                try:
                    st.session_state.prediction_service = initialize_prediction_service(db)
                except Exception as e:
                    st.error(f"❌ Error al inicializar predicciones: {e}")
                    st.stop()
        
        if 'analytics_engine' not in st.session_state:
            with st.spinner("🔄 Inicializando motor de análisis..."):
                try:
                    st.session_state.analytics_engine = initialize_analytics_engine(db)
                except Exception as e:
                    st.error(f"❌ Error al inicializar análisis: {e}")
                    st.stop()
        
        render_prediction_lab(st.session_state.prediction_service, st.session_state.analytics_engine)
    
    with tab3:
        # Inicializar servicios solo cuando se necesiten
        if 'prediction_service' not in st.session_state:
            with st.spinner("🔄 Inicializando servicio de predicciones..."):
                try:
                    st.session_state.prediction_service = initialize_prediction_service(db)
                except Exception as e:
                    st.error(f"❌ Error al inicializar predicciones: {e}")
                    st.stop()
        
        if 'analytics_engine' not in st.session_state:
            with st.spinner("🔄 Inicializando motor de análisis..."):
                try:
                    st.session_state.analytics_engine = initialize_analytics_engine(db)
                except Exception as e:
                    st.error(f"❌ Error al inicializar análisis: {e}")
                    st.stop()
        
        render_pattern_analysis(st.session_state.prediction_service, st.session_state.analytics_engine)
    
    with tab4:
        # Inicializar analytics engine solo cuando se necesite
        if 'analytics_engine' not in st.session_state:
            with st.spinner("🔄 Inicializando motor de análisis..."):
                try:
                    st.session_state.analytics_engine = initialize_analytics_engine(db)
                except Exception as e:
                    st.error(f"❌ Error al inicializar análisis: {e}")
                    st.stop()
        
        render_data_performance(st.session_state.analytics_engine)

def render_dashboard_overview(analytics_engine):
    """Renderiza el dashboard principal con resumen general"""
    
    st.header("📊 Resumen General del Sistema")
    
    # Selector de período
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Período de Análisis")
    with col2:
        period_days = st.selectbox(
            "Seleccionar período:",
            [30, 90, 180, 365, 730],
            index=2,  # 180 días por defecto
            format_func=lambda x: f"{x} días ({x//30} meses)" if x < 365 else f"{x} días ({x//365} años)"
        )
    
    # Obtener datos del dashboard
    with st.spinner("Cargando resumen del sistema..."):
        overview = analytics_engine.get_dashboard_overview(days=period_days)
    
    if 'error' in overview:
        st.error(f"❌ {overview['error']}")
        return
    
    # Métricas principales
    st.subheader("📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Sorteos",
            overview['general_stats']['total_draws'],
            delta=f"{overview['recent_activity']['last_30_days']} últimos 30 días"
        )
    
    with col2:
        st.metric(
            "Números Únicos",
            overview['general_stats']['unique_numbers'],
            delta=f"{overview['general_stats']['coverage_percentage']}% cobertura"
        )
    
    with col3:
        st.metric(
            "Promedio Diario",
            overview['general_stats']['draws_per_day'],
            delta=f"{overview['recent_activity']['daily_average']} últimos 30 días"
        )
    
    with col4:
        st.metric(
            "N
