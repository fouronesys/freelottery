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

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
        margin-bottom: 1rem;
    }
    
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    
    .confidence-high { border-left: 4px solid #28a745; }
    .confidence-medium { border-left: 4px solid #ffc107; }
    .confidence-low { border-left: 4px solid #dc3545; }
    
    .nav-button {
        background: #2d5aa0;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.2rem;
        cursor: pointer;
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
            st.experimental_rerun()
    
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