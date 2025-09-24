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
    }
    
    .confidence-high::before {
        background: linear-gradient(to bottom, var(--secondary-600), var(--secondary-700)) !important;
    }
    
    .confidence-medium {
        border-left: 4px solid var(--accent-500) !important;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%) !important;
        border-color: var(--accent-500) !important;
    }
    
    .confidence-medium::before {
        background: linear-gradient(to bottom, var(--accent-500), var(--accent-600)) !important;
    }
    
    .confidence-low {
        border-left: 4px solid var(--danger-500) !important;
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%) !important;
        border-color: var(--danger-500) !important;
    }
    
    .confidence-low::before {
        background: linear-gradient(to bottom, var(--danger-500), var(--danger-600)) !important;
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
def initialize_services():
    """Inicializa los servicios del sistema"""
    db = DatabaseManager()
    prediction_service = UnifiedPredictionService(db)
    analytics_engine = UnifiedAnalyticsEngine(db)
    return db, prediction_service, analytics_engine

def main():
    """Función principal de la aplicación"""
    
    # Inicializar servicios
    db, prediction_service, analytics_engine = initialize_services()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🎲 Quiniela Loteka - Sistema de Análisis Unificado</h1>
        <p>Predicciones inteligentes basadas en análisis estadístico avanzado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navegación principal
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard Overview", 
        "🎯 Prediction Lab", 
        "📈 Data & Performance"
    ])
    
    with tab1:
        render_dashboard_overview(analytics_engine)
    
    with tab2:
        render_prediction_lab(prediction_service, analytics_engine)
    
    with tab3:
        render_data_performance(analytics_engine)

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
            "Números Faltantes",
            len(overview['missing_numbers']),
            delta=f"{100 - overview['general_stats']['coverage_percentage']:.1f}% sin aparecer"
        )
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Top 10 Números Más Frecuentes")
        
        if overview['hot_numbers']:
            hot_df = pd.DataFrame(overview['hot_numbers'])
            
            fig = px.bar(
                hot_df, 
                x='number', 
                y='count',
                title="Números Más Frecuentes",
                color='count',
                color_continuous_scale='Reds'
            )
            fig.update_layout(
                xaxis_title="Número",
                yaxis_title="Frecuencia",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(
                hot_df.rename(columns={
                    'number': 'Número',
                    'count': 'Apariciones',
                    'percentage': 'Porcentaje'
                }),
                hide_index=True,
                use_container_width=True
            )
    
    with col2:
        st.subheader("❄️ Top 10 Números Menos Frecuentes")
        
        if overview['cold_numbers']:
            cold_df = pd.DataFrame(overview['cold_numbers'])
            
            fig = px.bar(
                cold_df, 
                x='number', 
                y='count',
                title="Números Menos Frecuentes",
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title="Número",
                yaxis_title="Frecuencia",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(
                cold_df.rename(columns={
                    'number': 'Número',
                    'count': 'Apariciones',
                    'percentage': 'Porcentaje'
                }),
                hide_index=True,
                use_container_width=True
            )
    
    # Distribución por rangos
    st.subheader("📊 Distribución por Rangos")
    
    if overview['range_distribution']:
        ranges_data = []
        for range_name, data in overview['range_distribution'].items():
            ranges_data.append({
                'Rango': range_name,
                'Cantidad': data['count'],
                'Porcentaje': data['percentage']
            })
        
        ranges_df = pd.DataFrame(ranges_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                ranges_df,
                values='Cantidad',
                names='Rango',
                title="Distribución por Rangos"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(ranges_df, hide_index=True, use_container_width=True)
    
    # Últimos sorteos
    st.subheader("🆕 Últimos Sorteos")
    
    if overview['latest_draws']:
        for draw in overview['latest_draws']:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**{draw['date']}**")
                with col2:
                    numbers_str = " - ".join([f"**{num:02d}**" for num in draw['numbers']])
                    st.markdown(f"🎯 {numbers_str}")
                st.divider()

def render_prediction_lab(prediction_service, analytics_engine):
    """Renderiza el laboratorio de predicciones"""
    
    st.header("🎯 Laboratorio de Predicciones")
    
    # Configuración de predicciones
    st.subheader("⚙️ Configuración de Predicción")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Obtener estrategias disponibles
        strategies = prediction_service.get_available_strategies()
        strategy_options = {key: config['name'] for key, config in strategies.items()}
        
        selected_strategy = st.selectbox(
            "Estrategia de Predicción:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x]
        )
    
    with col2:
        period_days = st.selectbox(
            "Período de Datos:",
            [180, 365, 730, 1825],
            index=1,  # 365 días por defecto
            format_func=lambda x: f"{x} días ({x//365:.1f} años)" if x >= 365 else f"{x} días"
        )
    
    with col3:
        num_predictions = st.slider(
            "Número de Predicciones:",
            min_value=5,
            max_value=20,
            value=10
        )
    
    with col4:
        confidence_threshold = st.slider(
            "Umbral de Confianza:",
            min_value=0.1,
            max_value=0.8,
            value=0.3,
            step=0.1,
            format="%.1f"
        )
    
    # Descripción de la estrategia seleccionada
    if selected_strategy in strategies:
        strategy_config = strategies[selected_strategy]
        st.info(f"📋 **{strategy_config['name']}**: {strategy_config['description']}")
    
    # Botón para generar predicciones
    if st.button("🚀 Generar Predicciones", type="primary", use_container_width=True):
        
        with st.spinner("Generando predicciones inteligentes..."):
            result = prediction_service.generate_predictions(
                strategy=selected_strategy,
                days=period_days,
                num_predictions=num_predictions,
                confidence_threshold=confidence_threshold
            )
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
            return
        
        # Mostrar predicciones
        st.subheader("🎯 Predicciones Generadas")
        
        if result['predictions']:
            # Estadísticas de las predicciones
            stats = result['statistics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Predicciones", stats['total_predictions'])
            with col2:
                st.metric("Score Promedio", stats['score_stats']['average'])
            with col3:
                st.metric("Confianza Promedio", f"{stats['confidence_stats']['average']:.1%}")
            with col4:
                st.metric("Alta Confianza", stats['confidence_distribution']['alta'])
            
            # Lista de predicciones
            st.subheader("📋 Lista de Predicciones")
            
            for pred in result['predictions']:
                confidence_class = (
                    "confidence-high" if pred['confidence'] >= 0.8 else
                    "confidence-medium" if pred['confidence'] >= 0.6 else
                    "confidence-low"
                )
                
                with st.container():
                    st.markdown(f"""
                    <div class="metric-card {confidence_class}">
                        <h4>#{pred['rank']} - Número {pred['number']:02d}</h4>
                        <p><strong>Score:</strong> {pred['score']} | 
                           <strong>Confianza:</strong> {pred['confidence']:.1%} ({pred['confidence_level']})</p>
                        <p><strong>Componentes:</strong> {', '.join(pred['active_components'])}</p>
                        <p><strong>Análisis:</strong> {pred['reasoning']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Análisis de componentes
            st.subheader("🔍 Análisis de Componentes")
            
            if 'component_contributions' in result:
                components_data = []
                for component, data in result['component_contributions'].items():
                    components_data.append({
                        'Componente': component.title(),
                        'Peso': f"{data['weight']:.1%}",
                        'Números Encontrados': data['numbers_found'],
                        'En Predicciones': data['numbers_in_predictions'],
                        'Efectividad': f"{data['effectiveness']:.1%}"
                    })
                
                components_df = pd.DataFrame(components_data)
                st.dataframe(components_df, hide_index=True, use_container_width=True)
            
            # Opción para guardar predicciones
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Guardar Predicciones"):
                    filename = f"predicciones_{selected_strategy}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                    st.success(f"✅ Predicciones guardadas en: {filename}")
            
            with col2:
                # Análisis individual de números
                selected_number = st.selectbox(
                    "Analizar número específico:",
                    options=[pred['number'] for pred in result['predictions']],
                    format_func=lambda x: f"Número {x:02d}"
                )
                
                if st.button("🔍 Analizar Número"):
                    with st.spinner("Analizando número..."):
                        number_analysis = analytics_engine.get_number_analysis(selected_number, period_days)
                    
                    if 'error' not in number_analysis:
                        st.subheader(f"📊 Análisis del Número {selected_number:02d}")
                        
                        freq_analysis = number_analysis['frequency_analysis']
                        timing_analysis = number_analysis['timing_analysis']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Apariciones",
                                freq_analysis['appearances'],
                                delta=f"{freq_analysis['frequency_percentage']:.1f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "Última Aparición",
                                timing_analysis['last_appearance'] or "N/A"
                            )
                        
                        with col3:
                            st.metric(
                                "Días Desde Última",
                                timing_analysis['days_since_last'] or "N/A"
                            )
                        
                        # Estado de predicción
                        status = timing_analysis['prediction_status']
                        status_emoji = {
                            'overdue': '🔥',
                            'recent': '❄️',
                            'normal': '📊'
                        }
                        
                        status_text = {
                            'overdue': 'Número atrasado - alta probabilidad',
                            'recent': 'Apareció recientemente - baja probabilidad',
                            'normal': 'En rango normal de aparición'
                        }
                        
                        st.info(f"{status_emoji.get(status, '📊')} {status_text.get(status, 'Estado normal')}")
        
        else:
            st.warning("⚠️ No se generaron predicciones con el umbral de confianza especificado. Intenta reducir el umbral.")

def render_data_performance(analytics_engine):
    """Renderiza la sección de datos y rendimiento"""
    
    st.header("📈 Datos y Rendimiento del Sistema")
    
    # Métricas de rendimiento
    with st.spinner("Cargando métricas de rendimiento..."):
        performance = analytics_engine.get_performance_metrics(days=90)
    
    if 'error' in performance:
        st.error(f"❌ {performance['error']}")
        return
    
    # Resumen de datos
    st.subheader("📊 Resumen de Datos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Sorteos",
            performance['data_summary']['total_draws']
        )
    
    with col2:
        st.metric(
            "Números Únicos",
            performance['data_summary']['unique_numbers']
        )
    
    with col3:
        st.metric(
            "Días con Datos",
            performance['data_summary']['unique_dates']
        )
    
    with col4:
        st.metric(
            "Promedio Diario",
            performance['data_summary']['average_draws_per_day']
        )
    
    # Calidad de datos
    st.subheader("🔍 Calidad de Datos")
    
    quality = performance['data_quality']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Completitud",
            f"{quality['completeness']}%",
            delta="Cobertura de números"
        )
        
        st.metric(
            "Densidad de Datos",
            f"{quality['data_density']}%",
            delta="Días con datos"
        )
    
    with col2:
        consistency_color = "normal" if quality['consistency'] == 'good' else "inverse"
        st.metric(
            "Consistencia",
            quality['consistency'].title(),
            delta=f"{quality['coverage_days']} de {performance['period']['days']} días",
            delta_color=consistency_color
        )
    
    # Actividad reciente
    st.subheader("🕐 Actividad Reciente")
    
    recent = performance['recent_activity']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Últimos 7 Días",
            recent['last_7_days'],
            delta=f"{recent['daily_average']} por día"
        )
    
    with col2:
        st.metric(
            "Última Actualización",
            recent['last_update'] or "N/A"
        )
    
    with col3:
        cache_status = performance['cache_status']
        total_cache = sum(cache_status.values())
        st.metric(
            "Cache del Sistema",
            total_cache,
            delta="entradas activas"
        )
    
    # Insights de patrones
    st.subheader("🎯 Insights de Patrones")
    
    with st.spinner("Analizando patrones..."):
        patterns = analytics_engine.get_pattern_insights(days=180)
    
    if 'error' not in patterns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔢 Análisis de Dígitos")
            
            # Dígitos de unidades favoritos
            fav_units = patterns['digit_patterns']['favorite_units']
            units_df = pd.DataFrame(fav_units, columns=['Dígito', 'Frecuencia'])
            
            fig = px.bar(
                units_df.head(5),
                x='Dígito',
                y='Frecuencia',
                title="Top 5 Dígitos de Unidades"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Análisis de Paridad")
            
            parity = patterns['parity_analysis']
            
            parity_df = pd.DataFrame([
                {'Tipo': 'Pares', 'Cantidad': parity['even_count'], 'Porcentaje': parity['even_percentage']},
                {'Tipo': 'Impares', 'Cantidad': parity['odd_count'], 'Porcentaje': parity['odd_percentage']}
            ])
            
            fig = px.pie(
                parity_df,
                values='Cantidad',
                names='Tipo',
                title="Distribución Par/Impar"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Resumen de insights
        if patterns['summary']:
            st.subheader("💡 Insights Clave")
            for insight in patterns['summary']:
                st.info(f"🔍 {insight}")
        
        # Números faltantes
        missing = patterns['missing_numbers']
        if missing['numbers']:
            st.subheader("❄️ Números Sin Aparecer")
            st.warning(f"⚠️ {missing['count']} números ({missing['percentage']}%) no han aparecido en los últimos 180 días")
            
            # Mostrar números faltantes en formato compacto
            missing_chunks = [missing['numbers'][i:i+10] for i in range(0, len(missing['numbers']), 10)]
            for chunk in missing_chunks:
                numbers_str = " - ".join([f"{num:02d}" for num in chunk])
                st.code(numbers_str)
    
    # Controles del sistema
    st.subheader("🔧 Controles del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpiar Cache", help="Limpia el cache del sistema para refrescar datos"):
            analytics_engine.clear_cache()
            st.success("✅ Cache limpiado")
    
    with col2:
        if st.button("🔄 Recargar Servicios", help="Reinicia los servicios del sistema"):
            st.cache_resource.clear()
            st.success("✅ Servicios recargados")
            st.rerun()
    
    with col3:
        if st.button("📥 Exportar Datos", help="Exporta datos del sistema"):
            export_data = {
                'performance': performance,
                'patterns': patterns if 'error' not in patterns else {},
                'export_date': datetime.now().isoformat()
            }
            
            filename = f"system_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            st.success(f"✅ Datos exportados a: {filename}")

if __name__ == "__main__":
    main()