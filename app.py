import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from database import DatabaseManager
from scraper import QuinielaScraperManager
from analyzer import StatisticalAnalyzer
from predictor import LotteryPredictor
from utils import format_currency, format_percentage

# Configuración de la página
st.set_page_config(
    page_title="Análisis Estadístico Quiniela Loteka",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialización de componentes
@st.cache_resource
def init_components():
    db = DatabaseManager()
    scraper = QuinielaScraperManager()
    analyzer = StatisticalAnalyzer(db)
    predictor = LotteryPredictor(analyzer)
    return db, scraper, analyzer, predictor

db, scraper, analyzer, predictor = init_components()

# Título principal
st.title("🎯 Sistema de Análisis Estadístico - Quiniela Loteka")
st.markdown("### Predicción de números basada en análisis de frecuencia histórica")

# Sidebar para controles
st.sidebar.header("⚙️ Configuración")

# Control de actualización de datos
if st.sidebar.button("🔄 Actualizar Datos Históricos", type="primary"):
    with st.spinner("Recopilando datos históricos..."):
        try:
            # Intentar obtener datos de los últimos 30 días
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            results = scraper.scrape_historical_data(start_date, end_date)
            
            if results:
                saved_count = 0
                for result in results:
                    if db.save_draw_result(result):
                        saved_count += 1
                
                st.sidebar.success(f"✅ {saved_count} nuevos sorteos guardados")
            else:
                st.sidebar.warning("⚠️ No se encontraron datos nuevos")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error al actualizar datos: {str(e)}")

# Configuración de análisis
st.sidebar.subheader("📊 Parámetros de Análisis")
days_to_analyze = st.sidebar.slider(
    "Días a analizar",
    min_value=30,
    max_value=365,
    value=180,
    step=30,
    help="Número de días hacia atrás para el análisis estadístico"
)

prediction_method = st.sidebar.selectbox(
    "Método de Predicción",
    ["Frecuencia Histórica", "Tendencia Reciente", "Combinado"],
    help="Método utilizado para generar las predicciones"
)

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Dashboard Principal",
    "🔢 Análisis de Números",
    "🎯 Predicciones",
    "📊 Estadísticas Avanzadas"
])

with tab1:
    st.header("📈 Dashboard Principal")
    
    # Estadísticas generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_draws = db.get_total_draws()
    recent_draws = db.get_draws_count_last_days(30)
    
    with col1:
        st.metric(
            label="Total de Sorteos",
            value=total_draws,
            help="Número total de sorteos en la base de datos"
        )
    
    with col2:
        st.metric(
            label="Sorteos Últimos 30 días",
            value=recent_draws,
            help="Sorteos recopilados en el último mes"
        )
    
    with col3:
        if total_draws > 0:
            coverage_days = db.get_data_coverage_days()
            st.metric(
                label="Días de Cobertura",
                value=coverage_days,
                help="Días cubiertos por los datos históricos"
            )
        else:
            st.metric("Días de Cobertura", "0")
    
    with col4:
        last_update = db.get_last_update_date()
        if last_update:
            days_since = (datetime.now() - last_update).days
            st.metric(
                label="Última Actualización",
                value=f"Hace {days_since} días",
                help=f"Última vez que se actualizaron los datos: {last_update.strftime('%Y-%m-%d')}"
            )
        else:
            st.metric("Última Actualización", "Sin datos")
    
    if total_draws > 0:
        # Análisis de frecuencia básico
        st.subheader("🔥 Números Más Frecuentes (Últimos 30 días)")
        
        hot_numbers = analyzer.get_hot_numbers(days=30, limit=10)
        if hot_numbers:
            df_hot = pd.DataFrame(hot_numbers, columns=['Número', 'Frecuencia', 'Frecuencia Relativa'])
            
            fig = px.bar(
                df_hot,
                x='Número',
                y='Frecuencia',
                title="Top 10 Números Más Frecuentes",
                labels={'Frecuencia': 'Veces que ha salido'},
                color='Frecuencia',
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Números fríos
        st.subheader("🧊 Números Menos Frecuentes (Últimos 30 días)")
        
        cold_numbers = analyzer.get_cold_numbers(days=30, limit=10)
        if cold_numbers:
            df_cold = pd.DataFrame(cold_numbers, columns=['Número', 'Frecuencia', 'Frecuencia Relativa'])
            
            fig = px.bar(
                df_cold,
                x='Número',
                y='Frecuencia',
                title="Top 10 Números Menos Frecuentes",
                labels={'Frecuencia': 'Veces que ha salido'},
                color='Frecuencia',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos históricos disponibles. Haz clic en 'Actualizar Datos Históricos' para comenzar.")

with tab2:
    st.header("🔢 Análisis Detallado de Números")
    
    if total_draws > 0:
        # Tabla de frecuencias completa
        all_frequencies = analyzer.calculate_all_frequencies(days=days_to_analyze)
        
        if all_frequencies:
            df_freq = pd.DataFrame(all_frequencies, columns=[
                'Número', 'Frecuencia Absoluta', 'Frecuencia Relativa', 'Clasificación'
            ])
            df_freq['Frecuencia Relativa'] = df_freq['Frecuencia Relativa'].apply(lambda x: f"{x:.2%}")
            
            st.subheader(f"📋 Tabla de Frecuencias ({days_to_analyze} días)")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                classification_filter = st.selectbox(
                    "Filtrar por clasificación",
                    ["Todos", "Caliente", "Normal", "Frío"]
                )
            
            with col2:
                sort_by = st.selectbox(
                    "Ordenar por",
                    ["Frecuencia Absoluta", "Número", "Frecuencia Relativa"]
                )
            
            # Aplicar filtros
            if classification_filter != "Todos":
                df_filtered = df_freq[df_freq['Clasificación'] == classification_filter]
            else:
                df_filtered = df_freq
            
            # Aplicar ordenamiento
            if sort_by == "Frecuencia Absoluta":
                df_filtered = df_filtered.sort_values('Frecuencia Absoluta', ascending=False)
            elif sort_by == "Número":
                df_filtered = df_filtered.sort_values('Número')
            else:
                df_filtered = df_filtered.sort_values('Frecuencia Relativa', ascending=False)
            
            st.dataframe(df_filtered, use_container_width=True)
            
            # Distribución de frecuencias
            st.subheader("📊 Distribución de Frecuencias")
            
            fig = px.histogram(
                df_freq,
                x='Frecuencia Absoluta',
                nbins=20,
                title="Distribución de Frecuencias de Números",
                labels={'Frecuencia Absoluta': 'Frecuencia', 'count': 'Cantidad de Números'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Análisis por rangos
            st.subheader("🎯 Análisis por Rangos de Números")
            
            range_analysis = analyzer.analyze_by_ranges(days=days_to_analyze)
            if range_analysis:
                df_ranges = pd.DataFrame(range_analysis, columns=[
                    'Rango', 'Frecuencia Promedio', 'Números en Rango'
                ])
                
                fig = px.bar(
                    df_ranges,
                    x='Rango',
                    y='Frecuencia Promedio',
                    title="Frecuencia Promedio por Rango de Números",
                    labels={'Frecuencia Promedio': 'Frecuencia Promedio'}
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos suficientes para el análisis. Actualiza los datos históricos primero.")

with tab3:
    st.header("🎯 Predicciones y Recomendaciones")
    
    if total_draws > 0:
        # Configuración de predicción
        col1, col2 = st.columns(2)
        
        with col1:
            num_predictions = st.slider(
                "Cantidad de números a predecir",
                min_value=5,
                max_value=20,
                value=10,
                help="Número de predicciones a generar"
            )
        
        with col2:
            confidence_threshold = st.slider(
                "Umbral de confianza (%)",
                min_value=50,
                max_value=95,
                value=70,
                help="Nivel mínimo de confianza para las predicciones"
            )
        
        if st.button("🎯 Generar Predicciones", type="primary"):
            with st.spinner("Generando predicciones..."):
                predictions = predictor.generate_predictions(
                    method=prediction_method.lower().replace(" ", "_"),
                    days=days_to_analyze,
                    num_predictions=num_predictions,
                    confidence_threshold=confidence_threshold
                )
                
                if predictions:
                    st.success("✅ Predicciones generadas exitosamente")
                    
                    # Mostrar predicciones
                    st.subheader("🎯 Números Recomendados")
                    
                    df_pred = pd.DataFrame(predictions, columns=[
                        'Número', 'Puntuación', 'Confianza', 'Razón'
                    ])
                    df_pred['Confianza'] = df_pred['Confianza'].apply(lambda x: f"{x:.1%}")
                    df_pred['Puntuación'] = df_pred['Puntuación'].apply(lambda x: f"{x:.2f}")
                    
                    # Mostrar en formato de cards
                    cols = st.columns(5)
                    for i, (_, row) in enumerate(df_pred.head(10).iterrows()):
                        with cols[i % 5]:
                            st.metric(
                                label=f"#{i+1}",
                                value=row['Número'],
                                delta=row['Confianza'],
                                help=row['Razón']
                            )
                    
                    # Tabla detallada
                    st.subheader("📋 Detalles de Predicciones")
                    st.dataframe(df_pred, use_container_width=True)
                    
                    # Gráfico de confianza
                    fig = px.bar(
                        df_pred,
                        x='Número',
                        y='Puntuación',
                        title="Puntuación de Predicciones",
                        labels={'Puntuación': 'Puntuación de Predicción'},
                        color='Puntuación',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ No se pudieron generar predicciones. Verifica los datos.")
        
        # Historial de sorteos recientes
        st.subheader("📅 Últimos Sorteos")
        recent_results = db.get_recent_draws(limit=10)
        
        if recent_results:
            df_recent = pd.DataFrame(recent_results, columns=[
                'Fecha', 'Número Ganador', 'Posición', 'Premio'
            ])
            df_recent['Fecha'] = pd.to_datetime(df_recent['Fecha']).dt.strftime('%Y-%m-%d')
            if 'Premio' in df_recent.columns:
                df_recent['Premio'] = df_recent['Premio'].apply(format_currency)
            
            st.dataframe(df_recent, use_container_width=True)
    else:
        st.warning("⚠️ Se requieren datos históricos para generar predicciones.")

with tab4:
    st.header("📊 Estadísticas Avanzadas")
    
    if total_draws > 0:
        # Tendencias temporales
        st.subheader("📈 Tendencias Temporales")
        
        temporal_data = analyzer.get_temporal_trends(days=days_to_analyze)
        if temporal_data:
            df_temporal = pd.DataFrame(temporal_data)
            df_temporal['Fecha'] = pd.to_datetime(df_temporal['Fecha'])
            
            fig = px.line(
                df_temporal,
                x='Fecha',
                y='Frecuencia_Promedio',
                title="Tendencia de Frecuencia Promedio en el Tiempo",
                labels={'Frecuencia_Promedio': 'Frecuencia Promedio'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlaciones
        st.subheader("🔗 Análisis de Correlaciones")
        
        correlations = analyzer.calculate_correlations(days=days_to_analyze)
        if correlations:
            st.write("Correlaciones entre apariciones de números:")
            
            # Heatmap de correlaciones (muestra simplificada)
            st.write("📊 Los números con correlaciones más altas tienden a aparecer juntos.")
            
            # Mostrar top correlaciones
            top_correlations = correlations[:10]  # Top 10 correlaciones
            df_corr = pd.DataFrame(top_correlations, columns=[
                'Número 1', 'Número 2', 'Correlación', 'Significancia'
            ])
            df_corr['Correlación'] = df_corr['Correlación'].apply(lambda x: f"{x:.3f}")
            
            st.dataframe(df_corr, use_container_width=True)
        
        # Estadísticas de rendimiento
        st.subheader("⚡ Estadísticas de Rendimiento")
        
        performance_stats = analyzer.get_performance_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Números Únicos Registrados",
                performance_stats.get('unique_numbers', 0)
            )
            st.metric(
                "Promedio de Sorteos por Día",
                f"{performance_stats.get('avg_draws_per_day', 0):.1f}"
            )
        
        with col2:
            st.metric(
                "Número Más Frecuente",
                performance_stats.get('most_frequent_number', 'N/A')
            )
            st.metric(
                "Número Menos Frecuente",
                performance_stats.get('least_frequent_number', 'N/A')
            )
        
        # Información adicional
        st.subheader("ℹ️ Información del Sistema")
        
        st.info("""
        **Metodología de Análisis:**
        - 🔥 **Números Calientes**: Aparecen con frecuencia superior al promedio
        - 🧊 **Números Fríos**: Aparecen con frecuencia inferior al promedio
        - 📊 **Frecuencia Relativa**: Probabilidad histórica de aparición
        - 🎯 **Predicciones**: Basadas en análisis estadístico, no garantizan resultados
        
        **Descargo de Responsabilidad:**
        Este sistema es para fines educativos y de entretenimiento. Los juegos de azar 
        son impredecibles por naturaleza y ningún análisis estadístico puede garantizar 
        resultados futuros.
        """)
    else:
        st.warning("⚠️ No hay datos suficientes para estadísticas avanzadas.")

# Footer
st.markdown("---")
st.markdown(
    "🎯 **Sistema de Análisis Estadístico Quiniela Loteka** | "
    "Desarrollado para análisis educativo de patrones en lotería"
)
