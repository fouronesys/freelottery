import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import time

from database import DatabaseManager
from scraper import QuinielaScraperManager
from analyzer import StatisticalAnalyzer
from predictor import LotteryPredictor
from utils import format_currency, format_percentage

# Caching para análisis complejos
@st.cache_data(ttl=3600)  # Cache por 1 hora
def cached_complex_analysis(analysis_type: str, days: int):
    """Cache para análisis estadísticos complejos"""
    analyzer = StatisticalAnalyzer(DatabaseManager())
    
    if analysis_type == "autocorrelation":
        return analyzer.analyze_autocorrelation(days)
    elif analysis_type == "time_series":
        return analyzer.analyze_time_series_patterns(days)
    elif analysis_type == "randomness":
        return analyzer.test_randomness_quality(days)
    elif analysis_type == "clustering":
        return analyzer.analyze_number_clustering(days)
    elif analysis_type == "formula":
        return analyzer.create_predictive_formula(days)
    
    return {}

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

# Sección explicativa sobre la Quiniela de Loteka
with st.expander("❓ ¿Cómo funciona la Quiniela de Loteka? - Guía Completa", expanded=False):
    st.markdown("""
    ## 🎯 **¿Qué es la Quiniela Loteka?**
    La Quiniela Loteka es un juego diario de lotería electrónica operado por la empresa Loteka en República Dominicana desde 2009. Es uno de los sorteos más populares del país.

    ## ⚙️ **¿Cómo Funciona?**
    - **Sistema**: Usa 3 globos/tómbolas electrónicas
    - **Números**: Cada globo contiene bolos numerados del 00 al 99
    - **Extracción**: Se extrae 1 bolo de cada globo
    - **Premios**: Globo 1 = 1er premio, Globo 2 = 2do premio, Globo 3 = 3er premio

    ## 🕰️ **Horario de Sorteos**
    - **Días**: Todos los días (lunes a domingo)
    - **Hora**: 7:55 PM
    - **Transmisión**: Por Telesistema (Canal 11)

    ## 🎲 **Tipos de Jugadas**

    ### 1. **Quiniela Simple**
    - Eliges 1 número del 00 al 99
    - Puedes ganar con cualquiera de los 3 premios
    - **Pagos por peso apostado**:
      - 1er premio: 60-75 pesos
      - 2do premio: 8-10 pesos  
      - 3er premio: 4-5 pesos

    ### 2. **Quiniela Exacta**
    - Solo juegas al primer número sorteado
    - Paga 70 pesos por peso apostado

    ### 3. **Palé**
    - Juegas a combinaciones de 2 números
    - **Pagos por peso apostado**:
      - 1ro y 2do: 1,000 pesos
      - 1ro y 3ro: 1,000 pesos
      - 2do y 3ro: 100 pesos

    ### 4. **Tripleta**
    - Juegas los 3 números exactos
    - **Pagos por peso apostado**:
      - 3 cifras exactas: 20,000 pesos
      - 2 cifras: 100 pesos

    ## 🎮 **Cómo Jugar**
    1. **Visita** un punto de venta autorizado de Loteka
    2. **Elige** tu número(s) del 00 al 99
    3. **Especifica** el tipo de jugada (quiniela, palé, tripleta)
    4. **Paga** la apuesta (mínimo RD$5)
    5. **Conserva** tu boleto como comprobante

    ## ⚠️ **Notas Importantes**
    - Los sorteos se realizan incluso en días feriados (una hora más temprano)
    - Conserva tu boleto original para cobrar premios
    - Los premios mayores a RD$100,001 están sujetos a retención de impuestos
    - Ser mayor de 18 años para participar
    """)
    
    st.info("💡 **Este sistema te ayuda a analizar patrones históricos y generar predicciones inteligentes para mejorar tus decisiones de juego.**")

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📈 Dashboard Principal",
    "🔢 Análisis de Números",
    "🎯 Predicciones",
    "📊 Estadísticas Avanzadas",
    "⏰ Análisis Temporal",
    "🤝 Co-ocurrencia y Patrones",
    "📅 Recomendaciones por Día",
    "🧠 Análisis Estadístico Complejo",
    "📩 Mis Predicciones"
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
            df_hot = pd.DataFrame.from_records(hot_numbers, columns=['Número', 'Frecuencia', 'Frecuencia Relativa'])
            
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
            st.plotly_chart(fig, width='stretch')
        
        # Números fríos
        st.subheader("🧊 Números Menos Frecuentes (Últimos 30 días)")
        
        cold_numbers = analyzer.get_cold_numbers(days=30, limit=10)
        if cold_numbers:
            df_cold = pd.DataFrame.from_records(cold_numbers, columns=['Número', 'Frecuencia', 'Frecuencia Relativa'])
            
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
            st.plotly_chart(fig, width='stretch')
    else:
        st.warning("⚠️ No hay datos históricos disponibles. Haz clic en 'Actualizar Datos Históricos' para comenzar.")

with tab2:
    st.header("🔢 Análisis Detallado de Números")
    
    if total_draws > 0:
        # Tabla de frecuencias completa
        all_frequencies = analyzer.calculate_all_frequencies(days=days_to_analyze)
        
        if all_frequencies:
            df_freq = pd.DataFrame.from_records(all_frequencies, columns=['Número', 'Frecuencia Absoluta', 'Frecuencia_Relativa_Num', 'Clasificación'])
            # Crear columna formateada para mostrar
            df_freq['Frecuencia Relativa'] = df_freq['Frecuencia_Relativa_Num'].apply(lambda x: f"{x:.2%}")
            
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
                df_filtered = df_filtered.sort_values(by='Frecuencia Absoluta', ascending=False)
            elif sort_by == "Número":
                df_filtered = df_filtered.sort_values(by='Número', ascending=True)
            else:
                df_filtered = df_filtered.sort_values(by='Frecuencia_Relativa_Num', ascending=False)
            
            # Remover columna numérica auxiliar para mostrar
            df_filtered = df_filtered.drop('Frecuencia_Relativa_Num', axis=1)
            
            st.dataframe(df_filtered, width='stretch')
            
            # Distribución de frecuencias
            st.subheader("📊 Distribución de Frecuencias")
            
            fig = px.histogram(
                df_freq,
                x='Frecuencia Absoluta',
                nbins=20,
                title="Distribución de Frecuencias de Números",
                labels={'Frecuencia Absoluta': 'Frecuencia', 'count': 'Cantidad de Números'}
            )
            st.plotly_chart(fig, width='stretch')
            
            # Análisis por rangos
            st.subheader("🎯 Análisis por Rangos de Números")
            
            range_analysis = analyzer.analyze_by_ranges(days=days_to_analyze)
            if range_analysis:
                df_ranges = pd.DataFrame.from_records(range_analysis, columns=['Rango', 'Frecuencia Promedio', 'Números en Rango'])
                
                fig = px.bar(
                    df_ranges,
                    x='Rango',
                    y='Frecuencia Promedio',
                    title="Frecuencia Promedio por Rango de Números",
                    labels={'Frecuencia Promedio': 'Frecuencia Promedio'}
                )
                st.plotly_chart(fig, width='stretch')
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
                    
                    df_pred = pd.DataFrame.from_records(predictions, columns=['Número', 'Puntuación_Num', 'Confianza_Num', 'Razón'])
                    # Crear columnas formateadas para mostrar
                    df_pred['Confianza'] = df_pred['Confianza_Num'].apply(lambda x: f"{x:.1%}")
                    df_pred['Puntuación'] = df_pred['Puntuación_Num'].apply(lambda x: f"{x:.2f}")
                    
                    # Mostrar en formato de cards
                    cols = st.columns(5)
                    for i, (_, row) in enumerate(df_pred.head(10).iterrows()):
                        with cols[i % 5]:
                            st.metric(
                                label=f"#{i+1}",
                                value=str(row['Número']),
                                delta=str(row['Confianza']),
                                help=str(row['Razón'])
                            )
                    
                    # Tabla detallada
                    st.subheader("📋 Detalles de Predicciones")
                    # Mostrar solo columnas formateadas para la tabla
                    display_df = df_pred[['Número', 'Puntuación', 'Confianza', 'Razón']]
                    st.dataframe(display_df, width='stretch')
                    
                    # Gráfico de confianza
                    fig = px.bar(
                        df_pred,
                        x='Número',
                        y='Puntuación_Num',
                        title="Puntuación de Predicciones",
                        labels={'Puntuación_Num': 'Puntuación de Predicción'},
                        color='Puntuación_Num',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.error("❌ No se pudieron generar predicciones. Verifica los datos.")
        
        # Historial de sorteos recientes
        st.subheader("📅 Últimos Sorteos")
        recent_results = db.get_recent_draws(limit=10)
        
        if recent_results:
            df_recent = pd.DataFrame.from_records(recent_results, columns=['Fecha', 'Número Ganador', 'Posición', 'Premio'])
            df_recent['Fecha'] = pd.to_datetime(df_recent['Fecha']).dt.strftime('%Y-%m-%d')
            if 'Premio' in df_recent.columns:
                df_recent['Premio'] = df_recent['Premio'].apply(format_currency)
            
            st.dataframe(df_recent, width='stretch')
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
            st.plotly_chart(fig, width='stretch')
        
        # Correlaciones
        st.subheader("🔗 Análisis de Correlaciones")
        
        correlations = analyzer.calculate_correlations(days=days_to_analyze)
        if correlations:
            st.write("Correlaciones entre apariciones de números:")
            
            # Heatmap de correlaciones (muestra simplificada)
            st.write("📊 Los números con correlaciones más altas tienden a aparecer juntos.")
            
            # Mostrar top correlaciones
            top_correlations = correlations[:10]  # Top 10 correlaciones
            df_corr = pd.DataFrame.from_records(top_correlations, columns=['Número 1', 'Número 2', 'Correlación', 'Significancia'])
            df_corr['Correlación'] = df_corr['Correlación'].apply(lambda x: f"{x:.3f}")
            
            st.dataframe(df_corr, width='stretch')
        
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

with tab5:
    st.header("⏰ Análisis Temporal Avanzado")
    
    if total_draws > 0:
        # Análisis por día de la semana
        st.subheader("📅 Patrones por Día de la Semana")
        
        day_patterns = analyzer.analyze_day_of_week_patterns(days=days_to_analyze)
        
        if day_patterns:
            # Preparar datos para visualización
            days_data = []
            for day, stats in day_patterns.items():
                days_data.append({
                    'Día': day,
                    'Total Sorteos': stats['total_draws'],
                    'Números Únicos': stats['unique_numbers'],
                    'Más Frecuente': stats['most_frequent'],
                    'Promedio': round(stats['avg_number'], 1)
                })
            
            df_days = pd.DataFrame(days_data)
            # Orden cronológico para días de la semana
            day_order = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            df_days['Día'] = pd.Categorical(df_days['Día'], categories=day_order, ordered=True)
            df_days = df_days.sort_values('Día')
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras de sorteos por día
                fig = px.bar(
                    df_days,
                    x='Día',
                    y='Total Sorteos',
                    title="Total de Sorteos por Día de la Semana",
                    labels={'Total Sorteos': 'Cantidad de Sorteos'},
                    category_orders={'Día': day_order}
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Gráfico de números únicos por día
                fig = px.bar(
                    df_days,
                    x='Día',
                    y='Números Únicos',
                    title="Números Únicos por Día de la Semana",
                    labels={'Números Únicos': 'Cantidad de Números Únicos'},
                    color='Números Únicos',
                    color_continuous_scale='Blues',
                    category_orders={'Día': day_order}
                )
                st.plotly_chart(fig, width='stretch')
            
            # Tabla resumen
            st.dataframe(df_days, width='stretch')
        
        # Análisis mensual
        st.subheader("📆 Patrones por Mes del Año")
        
        monthly_patterns = analyzer.analyze_monthly_patterns(days=days_to_analyze)
        
        if monthly_patterns:
            months_data = []
            for month, stats in monthly_patterns.items():
                months_data.append({
                    'Mes': month,
                    'Total Sorteos': stats['total_draws'],
                    'Números Únicos': stats['unique_numbers'],
                    'Más Frecuente': stats['most_frequent'],
                    'Promedio': round(stats['avg_number'], 1)
                })
            
            df_months = pd.DataFrame(months_data)
            
            if len(df_months) > 0:
                # Orden cronológico para meses
                spanish_month_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                df_months['Mes'] = pd.Categorical(df_months['Mes'], categories=spanish_month_order, ordered=True)
                df_months = df_months.sort_values('Mes')
                
                # Gráfico de sorteos por mes
                fig = px.bar(
                    df_months,
                    x='Mes',
                    y='Total Sorteos',
                    title="Distribución de Sorteos por Mes",
                    labels={'Total Sorteos': 'Cantidad de Sorteos'},
                    category_orders={'Mes': spanish_month_order}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, width='stretch')
                
                st.dataframe(df_months, width='stretch')
        
        # Tendencias EWMA
        st.subheader("📈 Tendencias EWMA (Promedio Móvil Exponencial)")
        
        st.info("""
        **¿Qué es EWMA?**
        El Promedio Móvil Exponencial da más peso a las observaciones recientes, 
        permitiendo detectar tendencias emergentes en la frecuencia de números.
        """)
        
        ewma_trends = analyzer.calculate_ewma_trends(days=days_to_analyze)
        
        if ewma_trends:
            # Ordenar por tendencia
            sorted_trends = sorted(ewma_trends.items(), key=lambda x: x[1], reverse=True)
            
            # Top 15 tendencias más altas
            top_trends = sorted_trends[:15]
            
            trends_data = []
            for number, trend in top_trends:
                trends_data.append({
                    'Número': number,
                    'Tendencia EWMA': round(trend, 3),
                    'Clasificación': 'Alta' if trend > np.mean(list(ewma_trends.values())) else 'Normal'
                })
            
            df_trends = pd.DataFrame(trends_data)
            
            # Gráfico de tendencias
            fig = px.bar(
                df_trends,
                x='Número',
                y='Tendencia EWMA',
                title="Top 15 Números con Mayor Tendencia EWMA",
                labels={'Tendencia EWMA': 'Valor de Tendencia'},
                color='Tendencia EWMA',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, width='stretch')
            
            st.dataframe(df_trends, width='stretch')
        
        # Detección de cambios significativos
        st.subheader("🔍 Cambios Significativos en Frecuencias")
        
        st.info("""
        **Análisis de Cambios:**
        Detecta números que han experimentado cambios significativos en su frecuencia 
        comparando el período reciente con el período anterior.
        """)
        
        frequency_changes = analyzer.detect_frequency_changes(days=days_to_analyze)
        
        if frequency_changes:
            changes_data = []
            for change in frequency_changes[:15]:  # Top 15 cambios
                changes_data.append({
                    'Número': change['number'],
                    'Tipo de Cambio': change['change_type'],
                    'Cambio %': f"{change['change_ratio']:.1%}",
                    'Freq. Reciente': change['recent_frequency'],
                    'Freq. Anterior': change['previous_frequency'],
                    'Significancia': round(change['significance'], 3)
                })
            
            df_changes = pd.DataFrame(changes_data)
            
            # Separar incrementos y disminuciones
            incrementos = df_changes[df_changes['Tipo de Cambio'] == 'Incremento']
            disminuciones = df_changes[df_changes['Tipo de Cambio'] == 'Disminución']
            
            col1, col2 = st.columns(2)
            
            with col1:
                if len(incrementos) > 0:
                    st.subheader("⬆️ Mayores Incrementos")
                    st.dataframe(incrementos.head(10), width='stretch')
            
            with col2:
                if len(disminuciones) > 0:
                    st.subheader("⬇️ Mayores Disminuciones")
                    st.dataframe(disminuciones.head(10), width='stretch')
            
            # Gráfico de cambios
            if len(df_changes) > 0:
                fig = px.scatter(
                    df_changes,
                    x='Freq. Anterior',
                    y='Freq. Reciente',
                    size='Significancia',
                    color='Tipo de Cambio',
                    hover_name='Número',
                    title="Cambios en Frecuencias: Anterior vs Reciente",
                    labels={
                        'Freq. Anterior': 'Frecuencia Período Anterior',
                        'Freq. Reciente': 'Frecuencia Período Reciente'
                    }
                )
                # Línea diagonal para referencia (sin cambio)
                max_val = max(df_changes['Freq. Anterior'].max(), df_changes['Freq. Reciente'].max())
                fig.add_shape(
                    type="line",
                    x0=0, y0=0, x1=max_val, y1=max_val,
                    line=dict(color="gray", dash="dash")
                )
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("No se detectaron cambios significativos en las frecuencias en este período.")
    
    else:
        st.warning("⚠️ Se requieren datos históricos para el análisis temporal.")

with tab6:
    st.header("🤝 Análisis de Co-ocurrencia y Patrones")
    
    if total_draws > 0:
        # Análisis de co-ocurrencia
        st.subheader("🔗 Co-ocurrencia de Números")
        st.write("Análisis de qué números aparecen juntos con mayor frecuencia en el mismo sorteo.")
        
        # Controles para co-ocurrencia
        col1, col2 = st.columns(2)
        with col1:
            cooccurrence_days = st.selectbox(
                "Período de análisis para co-ocurrencia",
                [90, 180, 365, 720],
                index=1,
                help="Días hacia atrás para analizar co-ocurrencias"
            )
        
        with col2:
            min_cooccurrence = st.number_input(
                "Frecuencia mínima de co-ocurrencia",
                min_value=2,
                max_value=20,
                value=3,
                help="Número mínimo de veces que deben aparecer juntos"
            )
        
        # Calcular co-ocurrencias
        with st.spinner("Analizando co-ocurrencias..."):
            cooccurrences = analyzer.analyze_number_cooccurrence(days=cooccurrence_days)
        
        if cooccurrences:
            # Crear tabla de las mejores co-ocurrencias
            best_pairs = []
            for num1, partners in cooccurrences.items():
                for num2, freq in partners.items():
                    if freq >= min_cooccurrence and num1 < num2:  # Evitar duplicados
                        best_pairs.append({
                            'Número 1': num1,
                            'Número 2': num2,
                            'Frecuencia': freq,
                            'Par': f"{num1}-{num2}"
                        })
            
            if best_pairs:
                df_pairs = pd.DataFrame(best_pairs)
                df_pairs = df_pairs.sort_values('Frecuencia', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏆 Mejores Pares")
                    st.dataframe(df_pairs.head(20), width='stretch')
                
                with col2:
                    # Gráfico de barras de mejores pares
                    top_pairs = df_pairs.head(15)
                    fig = px.bar(
                        top_pairs,
                        x='Par',
                        y='Frecuencia',
                        title="Top 15 Pares Más Frecuentes",
                        labels={'Frecuencia': 'Veces que Aparecieron Juntos'}
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, width='stretch')
            else:
                st.info("No se encontraron pares con la frecuencia mínima especificada.")
        else:
            st.warning("No se pudieron calcular co-ocurrencias para el período seleccionado.")
        
        # Análisis de transiciones de dígitos
        st.subheader("🔄 Transiciones de Dígitos")
        st.write("Análisis de cómo cambian los dígitos de un número al siguiente en secuencias temporales.")
        
        transition_days = st.selectbox(
            "Período para análisis de transiciones",
            [30, 60, 90, 180],
            index=2,
            help="Días para analizar transiciones de dígitos"
        )
        
        with st.spinner("Analizando transiciones de dígitos..."):
            transitions = analyzer.analyze_digit_transitions(days=transition_days)
        
        if transitions:
            # Mostrar transiciones más frecuentes
            transition_data = []
            for key, next_digits in transitions.items():
                for next_digit, freq in next_digits.items():
                    if freq >= 2:  # Mínimo 2 ocurrencias
                        transition_data.append({
                            'Transición': f"{key} → {next_digit}",
                            'Frecuencia': freq,
                            'Posición': key.split('_')[1],
                            'De': key.split('_')[2],
                            'A': next_digit
                        })
            
            if transition_data:
                df_transitions = pd.DataFrame(transition_data)
                df_transitions = df_transitions.sort_values('Frecuencia', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔄 Transiciones Más Frecuentes")
                    st.dataframe(df_transitions.head(20), width='stretch')
                
                with col2:
                    # Gráfico de transiciones por posición
                    pos_0 = df_transitions[df_transitions['Posición'] == '0'].head(10)
                    if len(pos_0) > 0:
                        fig = px.bar(
                            pos_0,
                            x='Transición',
                            y='Frecuencia',
                            title="Top Transiciones - Primera Posición",
                            labels={'Frecuencia': 'Cantidad de Transiciones'}
                        )
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, width='stretch')
        else:
            st.warning("No se pudieron calcular transiciones para el período seleccionado.")
        
        # Patrones de combinación
        st.subheader("🧩 Patrones de Combinación")
        st.write("Análisis de patrones matemáticos en las combinaciones de números (suma, paridad, rangos).")
        
        col1, col2 = st.columns(2)
        with col1:
            pattern_days = st.selectbox(
                "Período para patrones",
                [90, 180, 365],
                index=1,
                help="Días para analizar patrones de combinación"
            )
        
        with col2:
            min_pattern_freq = st.number_input(
                "Frecuencia mínima del patrón",
                min_value=3,
                max_value=20,
                value=5,
                help="Mínimas ocurrencias para considerar un patrón válido"
            )
        
        with st.spinner("Buscando patrones de combinación..."):
            patterns = analyzer.find_combination_patterns(
                min_frequency=min_pattern_freq, 
                days=pattern_days
            )
        
        if patterns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Patrones de suma
                sum_patterns = [p for p in patterns if p['type'] == 'suma_rango']
                if sum_patterns:
                    st.subheader("➕ Patrones de Suma")
                    for pattern in sum_patterns[:10]:
                        st.write(f"**Rango {pattern['pattern']}**: {pattern['frequency']} veces")
                        with st.expander(f"Ejemplos de {pattern['pattern']}"):
                            for example in pattern['examples']:
                                st.write(f"• {example} (suma: {sum(example)})")
            
            with col2:
                # Patrones de paridad
                parity_patterns = [p for p in patterns if p['type'] == 'paridad']
                if parity_patterns:
                    st.subheader("⚖️ Patrones de Paridad")
                    for pattern in parity_patterns[:10]:
                        st.write(f"**{pattern['pattern']}**: {pattern['frequency']} veces")
                        with st.expander(f"Ejemplos de {pattern['pattern']}"):
                            for example in pattern['examples']:
                                st.write(f"• {example}")
            
            # Gráfico resumen de patrones
            if len(patterns) > 0:
                pattern_df = pd.DataFrame(patterns)
                fig = px.bar(
                    pattern_df.head(15),
                    x='pattern',
                    y='frequency',
                    color='type',
                    title="Patrones de Combinación Más Frecuentes",
                    labels={
                        'frequency': 'Frecuencia',
                        'pattern': 'Patrón',
                        'type': 'Tipo de Patrón'
                    }
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("No se encontraron patrones con la frecuencia mínima especificada.")
    
    else:
        st.warning("⚠️ Se requieren datos históricos para el análisis de co-ocurrencia y patrones.")

with tab7:
    st.header("📅 Recomendaciones Inteligentes por Día")
    st.write("Sistema avanzado de recomendaciones que combina múltiples análisis para sugerir los mejores números y jugadas.")
    
    if total_draws > 0:
        # Sección de recomendación del día actual
        st.subheader("🌟 Mejor Jugada del Día - HOY")
        
        if st.button("🚀 Obtener Mejor Jugada para HOY", type="primary", key="today_best"):
            with st.spinner("Analizando todos los patrones para generar la mejor recomendación..."):
                today_recommendation = analyzer.get_best_play_recommendation()
                
                if today_recommendation:
                    # Mostrar fecha y información básica
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Fecha", today_recommendation['target_date'])
                        st.metric("Día del Mes", today_recommendation['day_of_month'])
                    
                    with col2:
                        st.metric("Día de la Semana", today_recommendation['day_of_week'])
                        st.metric("Confianza", today_recommendation['analysis_confidence'])
                    
                    with col3:
                        st.metric("🏆 Mejor Número", 
                                today_recommendation['best_single_number'], 
                                help="Número con mayor puntuación del análisis integrado")
                    
                    # Recomendaciones de jugadas
                    st.subheader("🎯 Estrategias de Juego Recomendadas")
                    
                    play_strategies = today_recommendation['play_strategies']
                    
                    # Quiniela Simple
                    quiniela = play_strategies['quiniela_simple']
                    st.success(f"**🎲 Quiniela Simple:** Número **{quiniela['number']}** | Confianza: {quiniela['confidence']} | Pago: {quiniela['expected_payout']}")
                    
                    # Palé
                    if play_strategies['pale_combinations']:
                        pale = play_strategies['pale_combinations'][0]
                        st.info(f"**🎯 Palé Recomendado:** {pale['numbers'][0]}-{pale['numbers'][1]} ({pale['type']}) | Pago: {pale['payout']}")
                    
                    # Tripleta
                    if play_strategies['tripleta_suggestion']:
                        tripleta = play_strategies['tripleta_suggestion']
                        st.warning(f"**🎰 Tripleta Sugerida:** {tripleta[0]}-{tripleta[1]}-{tripleta[2]} | Pago máximo: 20,000 pesos")
                    
                    # Top 5 recomendaciones detalladas
                    st.subheader("🏅 Top 5 Números Recomendados")
                    
                    cols = st.columns(5)
                    for i, (num, score, reasons) in enumerate(today_recommendation['top_recommendations']):
                        with cols[i]:
                            st.metric(
                                label=f"#{i+1}",
                                value=str(num),
                                delta=f"{score:.1f} pts",
                                help=f"Razones: {' | '.join(reasons[:2])}"
                            )
                    
                    # Metodología
                    with st.expander("📋 Metodología del Análisis"):
                        st.write(today_recommendation['methodology'])
                        st.write("Esta recomendación combina análisis histórico, patrones temporales y tendencias recientes para maximizar las probabilidades de éxito.")
        
        st.divider()
        
        # Sección de recomendaciones semanales por posición
        st.subheader("🗓️ Recomendaciones Semanales por Posición")
        st.write("Análisis especializado que indica qué números jugar en cada posición (1ra, 2da, 3ra) basado en patrones históricos.")
        
        # Selector de período para recomendaciones semanales
        weekly_analysis_period = st.selectbox(
            "Período de análisis para recomendaciones semanales (días)",
            [90, 180, 365],
            index=1,
            help="Días históricos para el análisis por posición",
            key="weekly_period_selector"
        )
        
        if st.button("📊 Generar Recomendaciones Semanales", type="secondary", key="weekly_recommendations"):
            with st.spinner("Analizando patrones por posición para generar recomendaciones semanales..."):
                weekly_recs = analyzer.get_weekly_recommendations_by_position(days=weekly_analysis_period)
                
                if weekly_recs and 'by_position' in weekly_recs and weekly_recs['by_position']:
                    st.success(f"✅ Recomendaciones generadas basadas en {weekly_recs.get('analysis_period', weekly_analysis_period)} días de análisis")
                    
                    # Mostrar recomendaciones por posición
                    st.subheader("🎯 Números Recomendados por Posición")
                    
                    positions = weekly_recs['by_position']
                    
                    if positions:
                        cols = st.columns(len(positions))
                        
                        for i, (pos_name, pos_data) in enumerate(positions.items()):
                            with cols[i]:
                                st.write(f"### {pos_name} Posición")
                                
                                # Verificar que pos_data tiene la estructura esperada
                                if pos_data and isinstance(pos_data, dict):
                                    # Métricas de la posición con valores por defecto
                                    top_recs = pos_data.get('top_recommendations', [])
                                    main_number = top_recs[0][0] if top_recs else "N/A"
                                    
                                    st.metric(
                                        "Número Principal", 
                                        main_number,
                                        help=f"Número más recomendado para la {pos_name} posición"
                                    )
                                    
                                    confidence = pos_data.get('confidence', 0)
                                    st.metric(
                                        "Confianza", 
                                        f"{confidence:.1f}%",
                                        help=f"Nivel de confianza basado en {pos_data.get('total_draws', 0)} sorteos"
                                    )
                                    
                                    avg_number = pos_data.get('avg_number', 0)
                                    st.metric(
                                        "Promedio Histórico", 
                                        avg_number,
                                        help=f"Promedio de números en esta posición"
                                    )
                                    
                                    # Top 3 números recomendados para esta posición
                                    st.write("**Top 3 Recomendados:**")
                                    if top_recs:
                                        for j, (num, score) in enumerate(top_recs[:3]):
                                            st.write(f"{j+1}. **{num}** (Puntuación: {score:.1f})")
                                    else:
                                        st.write("No hay recomendaciones disponibles")
                                else:
                                    st.warning(f"No hay datos suficientes para la {pos_name} posición")
                    
                    st.divider()
                    
                    # Estrategias de juego semanales
                    if 'weekly_strategy' in weekly_recs and weekly_recs['weekly_strategy']:
                        strategy = weekly_recs['weekly_strategy']
                        
                        st.subheader("🎲 Estrategias de Juego Recomendadas para Esta Semana")
                        
                        # Verificar si hay estrategias disponibles
                        if 'strategies' in strategy and strategy['strategies']:
                            for strat in strategy['strategies']:
                                strat_name = strat.get('name', 'Desconocida')
                                strat_desc = strat.get('description', 'Sin descripción')
                                strat_confidence = strat.get('confidence', 0)
                                strat_type = strat.get('play_type', 'N/A')
                                strat_numbers = strat.get('numbers', {})
                                
                                if strat_name == 'Conservadora':
                                    st.success(f"""
                                    **🛡️ Estrategia {strat_name}**: {strat_desc}
                                    
                                    **Números a jugar:**
                                    - 1ra posición: **{strat_numbers.get('1ra', 'N/A')}**
                                    - 2da posición: **{strat_numbers.get('2da', 'N/A')}**
                                    - 3ra posición: **{strat_numbers.get('3ra', 'N/A')}**
                                    
                                    **Confianza:** {strat_confidence:.1f}% | **Tipo:** {strat_type}
                                    """)
                                elif strat_name == 'Balanceada':
                                    st.info(f"""
                                    **⚖️ Estrategia {strat_name}**: {strat_desc}
                                    
                                    **Números a jugar:**
                                    - 1ra posición: **{strat_numbers.get('1ra', 'N/A')}**
                                    - 2da posición: **{strat_numbers.get('2da', 'N/A')}**
                                    - 3ra posición: **{strat_numbers.get('3ra', 'N/A')}**
                                    
                                    **Confianza:** {strat_confidence:.1f}% | **Tipo:** {strat_type}
                                    """)
                        else:
                            st.info("No se pudieron generar estrategias específicas con los datos disponibles.")
                        
                        # Resumen de recomendación
                        st.write("**💡 Resumen de Recomendación:**")
                        st.write(strategy.get('recommendation_summary', 'Estrategias basadas en análisis histórico y tendencias recientes.'))
                        
                        # Información adicional
                        with st.expander("📋 Detalles del Análisis"):
                            st.write(f"**Período analizado:** {weekly_recs.get('analysis_period', weekly_analysis_period)} días")
                            st.write(f"**Posiciones analizadas:** {weekly_recs.get('total_positions', 0)}")
                            st.write(f"**Generado:** {weekly_recs.get('generated_at', 'Fecha no disponible')}")
                            st.write("**Metodología:** Este análisis examina los patrones históricos específicos por posición para identificar números que tienden a salir más frecuentemente en cada posición (1ra, 2da, 3ra). Combina datos históricos (60%) con tendencias recientes (40%) para generar recomendaciones balanceadas.")
                    else:
                        st.info("Estrategias de juego no disponibles. Es posible que se necesiten más datos históricos para generar estrategias completas.")
                
                else:
                    st.warning("⚠️ No se pudieron generar recomendaciones semanales. Verifica que haya suficientes datos históricos.")
        
        st.divider()
        
        # Análisis por día del mes específico
        st.subheader("📊 Análisis Específico por Día del Mes")
        
        # Selector de día del mes y período
        col_day, col_period = st.columns(2)
        
        with col_day:
            selected_day_month = st.selectbox(
                "Selecciona día del mes",
                list(range(1, 32)),
                index=datetime.now().day - 1,
                help="Día del mes para análisis específico (1-31)"
            )
        
        with col_period:
            month_analysis_period = st.selectbox(
                "Período de análisis (días del mes)",
                [180, 365, 720],
                index=1,
                help="Días históricos para el análisis por día del mes"
            )
        
        if st.button("📈 Analizar Día del Mes Específico", key="specific_month_day"):
            with st.spinner(f"Analizando patrones para el día {selected_day_month} del mes..."):
                month_patterns = analyzer.analyze_day_of_month_patterns(days=month_analysis_period)
                
                if month_patterns and 'day_statistics' in month_patterns:
                    day_stats = month_patterns['day_statistics']
                    best_numbers_by_day = month_patterns['best_numbers_by_day']
                    
                    if selected_day_month in day_stats:
                        stats = day_stats[selected_day_month]
                        best_nums = best_numbers_by_day.get(selected_day_month, [])
                        
                        # Métricas del día específico
                        st.success(f"✅ Análisis completado para el día {selected_day_month}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Sorteos", stats['total_draws'])
                        
                        with col2:
                            st.metric("Números Únicos", stats['unique_numbers'])
                        
                        with col3:
                            st.metric("Número Más Frecuente", stats['most_frequent_number'])
                        
                        with col4:
                            st.metric("Promedio", f"{stats['avg_number']:.1f}")
                        
                        # Top números recomendados para este día
                        if best_nums:
                            st.subheader(f"🏅 Top 5 Números para el Día {selected_day_month}")
                            
                            cols = st.columns(5)
                            for i, num in enumerate(best_nums[:5]):
                                with cols[i]:
                                    freq_count = stats['frequency_distribution'].get(num, 0)
                                    st.metric(
                                        label=f"#{i+1}",
                                        value=str(num),
                                        delta=f"{freq_count} veces",
                                        help=f"Apareció {freq_count} veces en día {selected_day_month}"
                                    )
                            
                            # Gráfico de frecuencias del día específico
                            if stats['frequency_distribution']:
                                freq_data = []
                                for num, count in list(stats['frequency_distribution'].most_common(15)):
                                    freq_data.append({'Número': num, 'Frecuencia': count})
                                
                                if freq_data:
                                    df_freq = pd.DataFrame(freq_data)
                                    fig = px.bar(
                                        df_freq,
                                        x='Número',
                                        y='Frecuencia',
                                        title=f"Frecuencia de Números - Día {selected_day_month} del Mes",
                                        color='Frecuencia',
                                        color_continuous_scale='viridis'
                                    )
                                    st.plotly_chart(fig, width='stretch')
                        
                        # Recomendación específica
                        confidence = 'Alta' if stats['total_draws'] >= 10 else 'Media' if stats['total_draws'] >= 5 else 'Baja'
                        st.info(f"**Recomendación para día {selected_day_month}:** {', '.join(map(str, best_nums[:3]))} | Confianza: {confidence} | Basado en {stats['total_draws']} sorteos históricos")
                    
                    else:
                        st.warning(f"No hay datos suficientes para el día {selected_day_month} del mes en el período seleccionado.")
                        
                    # Resumen general de todos los días
                    summary = month_patterns['analysis_summary']
                    
                    with st.expander("📊 Resumen General - Todos los Días del Mes"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Días Analizados", summary['days_analyzed'])
                        
                        with col2:
                            st.metric("Días con Datos", summary['total_days_with_data'])
                        
                        with col3:
                            if summary['most_active_day']:
                                st.metric("Día Más Activo", f"Día {summary['most_active_day']}")
                        
                        with col4:
                            if summary['least_active_day']:
                                st.metric("Día Menos Activo", f"Día {summary['least_active_day']}")
                        
                        # Tabla completa de todos los días
                        table_data = []
                        for day in range(1, 32):
                            if day in best_numbers_by_day and day in day_stats:
                                top_3 = best_numbers_by_day[day][:3]
                                stats_day = day_stats[day]
                                table_data.append({
                                    'Día del Mes': day,
                                    'Top 3 Números': ', '.join(map(str, top_3)),
                                    'Más Frecuente': stats_day['most_frequent_number'],
                                    'Total Sorteos': stats_day['total_draws'],
                                    'Promedio': stats_day['avg_number']
                                })
                        
                        if table_data:
                            df_month = pd.DataFrame(table_data)
                            st.dataframe(df_month, width='stretch')
        
        st.divider()
        
        # Selector de día personalizado
        st.subheader("🎯 Recomendaciones Personalizadas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_day = st.selectbox(
                "Selecciona el día de la semana",
                ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                help="Día para el cual generar recomendaciones"
            )
        
        with col2:
            recommendation_period = st.selectbox(
                "Período de análisis",
                [90, 180, 365, 720],
                index=2,
                help="Días históricos para el análisis"
            )
        
        with col3:
            num_recommendations = st.slider(
                "Número de recomendaciones",
                min_value=5,
                max_value=20,
                value=10,
                help="Cantidad de números a recomendar"
            )
        
        if st.button("🎯 Generar Recomendaciones Personalizadas", type="secondary"):
            with st.spinner("Analizando patrones y generando recomendaciones..."):
                
                # 1. Análisis por día de la semana
                day_patterns = analyzer.analyze_day_of_week_patterns(days=recommendation_period)
                day_specific_numbers = []
                
                if target_day in day_patterns:
                    day_stats = day_patterns[target_day]
                    if 'top_numbers' in day_stats:
                        day_specific_numbers = day_stats['top_numbers'][:10]
                
                # 2. Análisis de tendencias EWMA
                ewma_trends = analyzer.calculate_ewma_trends(days=recommendation_period)
                trending_numbers = []
                if ewma_trends:
                    sorted_trends = sorted(ewma_trends.items(), key=lambda x: x[1], reverse=True)
                    trending_numbers = [num for num, trend in sorted_trends[:15] if trend > 0]
                
                # 3. Análisis de co-ocurrencia para números calientes
                hot_numbers = analyzer.get_hot_numbers(days=60, limit=5)
                hot_nums = [num for num, _, _ in hot_numbers] if hot_numbers else []
                
                cooccurrence_recommendations = []
                if hot_nums:
                    cooccurrences = analyzer.analyze_number_cooccurrence(days=recommendation_period)
                    for hot_num in hot_nums:
                        if hot_num in cooccurrences:
                            partners = cooccurrences[hot_num]
                            # Obtener los mejores compañeros del número caliente
                            best_partners = sorted(partners.items(), key=lambda x: x[1], reverse=True)[:3]
                            cooccurrence_recommendations.extend([partner for partner, _ in best_partners])
                
                # 4. Análisis de frecuencia general 
                frequency_data = analyzer.calculate_all_frequencies(days=recommendation_period)
                balanced_numbers = []
                if frequency_data:
                    # Números con clasificación "Normal" y "Caliente" 
                    for num, freq, rel_freq, classification in frequency_data:
                        if classification in ["Normal", "Caliente"]:
                            balanced_numbers.append((num, freq, rel_freq))
                    balanced_numbers = sorted(balanced_numbers, key=lambda x: x[2], reverse=True)[:10]
                    balanced_numbers = [num for num, _, _ in balanced_numbers]
                
                # 5. Combinar todas las recomendaciones con sistema de puntuación
                recommendation_scores = {}
                
                # Puntuación por análisis específico del día (peso alto)
                for i, num in enumerate(day_specific_numbers):
                    recommendation_scores[num] = recommendation_scores.get(num, 0) + (50 - i * 2)
                
                # Puntuación por tendencias EWMA (peso medio-alto)
                for i, num in enumerate(trending_numbers):
                    recommendation_scores[num] = recommendation_scores.get(num, 0) + (30 - i)
                
                # Puntuación por co-ocurrencia (peso medio)
                for num in cooccurrence_recommendations:
                    recommendation_scores[num] = recommendation_scores.get(num, 0) + 15
                
                # Puntuación por frecuencia balanceada (peso bajo)
                for i, num in enumerate(balanced_numbers):
                    recommendation_scores[num] = recommendation_scores.get(num, 0) + (10 - i)
                
                # Ordenar por puntuación y seleccionar los mejores
                if recommendation_scores:
                    sorted_recommendations = sorted(recommendation_scores.items(), key=lambda x: x[1], reverse=True)
                    final_recommendations = sorted_recommendations[:num_recommendations]
                    
                    # Mostrar resultados
                    st.success(f"✅ Recomendaciones generadas para {target_day}")
                    
                    # Panel de recomendaciones principales
                    st.subheader("🏆 Números Recomendados")
                    
                    # Mostrar en formato de cards
                    cols = st.columns(5)
                    # Calcular max_score una vez para todas las recomendaciones
                    max_score = max([s for _, s in final_recommendations]) if final_recommendations else 1
                    
                    for i, (number, score) in enumerate(final_recommendations[:10]):
                        with cols[i % 5]:
                            # Calcular confianza basada en la puntuación
                            confidence = (score / max_score) * 100
                            
                            st.metric(
                                label=f"#{i+1}",
                                value=str(number),
                                delta=f"{confidence:.0f}% confianza",
                                help=f"Puntuación: {score}"
                            )
                    
                    # Tabla detallada con análisis
                    st.subheader("📊 Análisis Detallado de Recomendaciones")
                    
                    detailed_data = []
                    for number, score in final_recommendations:
                        # Determinar fuentes de la recomendación
                        sources = []
                        if number in [n for n, _, _ in hot_numbers] if hot_numbers else []:
                            sources.append("🔥 Número Caliente")
                        if number in day_specific_numbers:
                            sources.append(f"📅 Específico de {target_day}")
                        if number in trending_numbers:
                            sources.append("📈 Tendencia EWMA")
                        if number in cooccurrence_recommendations:
                            sources.append("🤝 Co-ocurrencia")
                        if number in balanced_numbers:
                            sources.append("⚖️ Frecuencia Balanceada")
                        
                        # Obtener frecuencia actual
                        freq_abs, freq_rel = db.get_number_frequency(number, days=60)
                        
                        detailed_data.append({
                            'Número': number,
                            'Puntuación': score,
                            'Confianza': f"{(score / max_score) * 100:.0f}%",
                            'Frecuencia (60d)': freq_abs,
                            'Fuentes': " | ".join(sources[:3])  # Máximo 3 fuentes
                        })
                    
                    df_detailed = pd.DataFrame(detailed_data)
                    st.dataframe(df_detailed, width='stretch')
                    
                    # Gráfico de puntuaciones
                    fig = px.bar(
                        df_detailed.head(15),
                        x='Número',
                        y='Puntuación',
                        title="Puntuación de Recomendaciones",
                        labels={'Puntuación': 'Puntuación Total'},
                        color='Puntuación',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, width='stretch')
                    
                    # Panel de información del método
                    with st.expander("ℹ️ Metodología de Recomendaciones"):
                        st.write("""
                        **Sistema de Puntuación Combinado:**
                        
                        1. **Análisis Específico del Día** (peso alto): Números que históricamente salen más en el día seleccionado
                        2. **Tendencias EWMA** (peso medio-alto): Números con tendencia creciente según promedio móvil exponencial
                        3. **Co-ocurrencia** (peso medio): Números que frecuentemente aparecen junto a números calientes actuales
                        4. **Frecuencia Balanceada** (peso bajo): Números con frecuencia normal/caliente para equilibrio
                        
                        **Ventajas del Sistema:**
                        - ✅ Combina múltiples análisis estadísticos
                        - ✅ Considera patrones específicos por día de la semana
                        - ✅ Incluye análisis de tendencias recientes
                        - ✅ Balancea números calientes y normales
                        
                        **Nota:** Las recomendaciones son sugerencias basadas en análisis histórico y no garantizan resultados.
                        """)
                    
                else:
                    st.warning("No se pudieron generar recomendaciones con los datos disponibles.")
        
        # Estadísticas del día seleccionado
        st.subheader(f"📊 Estadísticas Históricas para {target_day}")
        
        day_patterns = analyzer.analyze_day_of_week_patterns(days=recommendation_period)
        if target_day in day_patterns:
            day_stats = day_patterns[target_day]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Sorteos",
                    day_stats['total_draws'],
                    help=f"Sorteos realizados en {target_day} durante los últimos {recommendation_period} días"
                )
            
            with col2:
                st.metric(
                    "Números Únicos",
                    day_stats['unique_numbers'],
                    help="Cantidad de números diferentes que han salido"
                )
            
            with col3:
                st.metric(
                    "Más Frecuente",
                    day_stats['most_frequent'],
                    help="Número que más veces ha salido en este día"
                )
            
            with col4:
                st.metric(
                    "Promedio",
                    f"{day_stats['avg_number']:.1f}",
                    help="Promedio de los números que salen en este día"
                )
        
    else:
        st.warning("⚠️ Se requieren datos históricos para generar recomendaciones por día.")

with tab8:
    st.header("🧠 Análisis Estadístico Complejo y Fórmulas Predictivas")
    st.write("Análisis estadísticos avanzados basados en autocorrelación, series temporales, clustering y tests de aleatoriedad.")
    
    if total_draws > 0:
        # Panel de configuración
        col1, col2 = st.columns(2)
        
        with col1:
            complex_analysis_days = st.selectbox(
                "Período para análisis complejo",
                [180, 365, 720],
                index=1,
                help="Días históricos para análisis estadístico complejo"
            )
        
        with col2:
            analysis_type = st.selectbox(
                "Tipo de análisis",
                ["Fórmula Predictiva Completa", "Autocorrelación", "Series Temporales", "Clustering", "Tests de Aleatoriedad"],
                help="Selecciona el tipo de análisis a ejecutar"
            )
        
        if st.button("🧮 Ejecutar Análisis Estadístico Complejo", type="primary"):
            
            if analysis_type == "Fórmula Predictiva Completa":
                with st.spinner("Ejecutando análisis integrado completo..."):
                    formula_results = analyzer.create_predictive_formula(days=complex_analysis_days)
                    
                    if formula_results:
                        st.success("✅ Fórmula predictiva generada exitosamente")
                        
                        # Mostrar fórmula matemática
                        st.subheader("📐 Fórmula Matemática Integrada")
                        st.code(formula_results['formula_description'], language='text')
                        
                        # Top predicciones
                        st.subheader("🏆 Top Predicciones de la Fórmula")
                        
                        if formula_results['top_predictions']:
                            top_nums = formula_results['top_predictions'][:10]
                            
                            # Cards de predicciones
                            cols = st.columns(5)
                            for i, (num, data) in enumerate(top_nums):
                                with cols[i % 5]:
                                    st.metric(
                                        label=f"#{i+1}",
                                        value=str(num),
                                        delta=f"{data['total_score']:.1f} pts",
                                        help=f"Clasificación: {data['classification']}"
                                    )
                            
                            # Tabla detallada
                            detailed_predictions = []
                            for num, data in top_nums:
                                detailed_predictions.append({
                                    'Número': num,
                                    'Puntuación Total': f"{data['total_score']:.1f}",
                                    'Clasificación': data['classification'],
                                    'Factores Principales': " | ".join(data['confidence_factors'][:2])
                                })
                            
                            df_predictions = pd.DataFrame(detailed_predictions)
                            st.dataframe(df_predictions, width='stretch')
                        
                        # Estadísticas del modelo
                        st.subheader("📊 Estadísticas del Modelo")
                        model_stats = formula_results['model_statistics']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Números Evaluados", model_stats['total_numbers_evaluated'])
                        
                        with col2:
                            st.metric("Autocorrelación", model_stats['autocorrelation_detected'])
                        
                        with col3:
                            st.metric("Calidad Aleatoriedad", model_stats['randomness_quality'])
                        
                        with col4:
                            st.metric("Tendencia Serie Temporal", model_stats['time_series_trend'])
                        
                        # Gráfico de puntuaciones
                        if formula_results['top_predictions']:
                            chart_data = []
                            for num, data in formula_results['top_predictions'][:15]:
                                chart_data.append({
                                    'Número': num,
                                    'Puntuación': data['total_score']
                                })
                            
                            df_chart = pd.DataFrame(chart_data)
                            fig = px.bar(
                                df_chart,
                                x='Número',
                                y='Puntuación',
                                title="Puntuaciones de la Fórmula Predictiva Integrada",
                                color='Puntuación',
                                color_continuous_scale='plasma'
                            )
                            st.plotly_chart(fig, width='stretch')
                    
                    else:
                        st.error("No se pudo generar la fórmula predictiva.")
            
            elif analysis_type == "Autocorrelación":
                with st.spinner("Analizando autocorrelación..."):
                    autocorr_results = analyzer.analyze_autocorrelation(days=complex_analysis_days)
                    
                    if isinstance(autocorr_results, dict) and 'error' not in autocorr_results and autocorr_results:
                        st.subheader("📈 Análisis de Autocorrelación")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Test Durbin-Watson", f"{autocorr_results['durbin_watson_stat']:.3f}")
                            st.metric("Test Ljung-Box (p-valor)", f"{autocorr_results['ljung_box_p_value']:.4f}")
                            st.metric("Evaluación", autocorr_results['randomness_assessment'])
                        
                        with col2:
                            if autocorr_results['autocorrelation_lags']:
                                lag_data = []
                                for lag_info in autocorr_results['autocorrelation_lags']:
                                    lag_data.append({
                                        'Lag': lag_info['lag'],
                                        'Correlación': lag_info['correlation']
                                    })
                                
                                df_lags = pd.DataFrame(lag_data)
                                fig = px.bar(
                                    df_lags,
                                    x='Lag',
                                    y='Correlación',
                                    title="Función de Autocorrelación (ACF)"
                                )
                                st.plotly_chart(fig, width='stretch')
                        
                        if autocorr_results['significant_lags']:
                            st.info(f"Lags significativos detectados: {', '.join(map(str, autocorr_results['significant_lags']))}")
                    
                    elif isinstance(autocorr_results, dict) and 'error' in autocorr_results:
                        st.error(f"Error en análisis de autocorrelación: {autocorr_results['error']}")
                    else:
                        st.warning("No se pudo realizar el análisis de autocorrelación.")
            
            elif analysis_type == "Series Temporales":
                with st.spinner("Analizando series temporales..."):
                    ts_results = analyzer.analyze_time_series_patterns(days=complex_analysis_days)
                    
                    if ts_results:
                        st.subheader("📊 Análisis de Series Temporales")
                        
                        # Análisis ARIMA
                        if 'arima_analysis' in ts_results and 'error' not in ts_results['arima_analysis']:
                            st.subheader("🔮 Modelo ARIMA")
                            arima = ts_results['arima_analysis']
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("AIC del Modelo", f"{arima.get('aic', 0):.2f}")
                            
                            with col2:
                                if 'forecast_next_7_days' in arima:
                                    forecast_avg = np.mean(arima['forecast_next_7_days'])
                                    st.metric("Promedio Predicción 7 días", f"{forecast_avg:.1f}")
                        
                        # Detección de ciclos
                        if ts_results['cycle_detection']:
                            st.subheader("🔄 Ciclos Detectados")
                            cycles_data = []
                            for cycle in ts_results['cycle_detection']:
                                cycles_data.append({
                                    'Período (días)': f"{cycle['period_days']:.1f}",
                                    'Fuerza': f"{cycle['strength']:.2f}"
                                })
                            
                            df_cycles = pd.DataFrame(cycles_data)
                            st.dataframe(df_cycles, width='stretch')
                        
                        # Análisis de tendencias
                        if ts_results['trend_analysis']:
                            st.subheader("📈 Análisis de Tendencias")
                            trend = ts_results['trend_analysis']
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Dirección", trend['trend_direction'])
                            with col2:
                                st.metric("Fuerza", trend['trend_strength'])
                            with col3:
                                st.metric("R²", f"{trend['r_squared']:.3f}")
                    
                    else:
                        st.warning("No se pudo realizar el análisis de series temporales.")
            
            elif analysis_type == "Clustering":
                with st.spinner("Ejecutando análisis de clustering..."):
                    cluster_results = analyzer.analyze_number_clustering(days=complex_analysis_days)
                    
                    if cluster_results:
                        st.subheader("🎯 Análisis de Clustering K-means")
                        
                        st.metric("Número Óptimo de Clusters", cluster_results['best_k_clusters'])
                        
                        # Mostrar clusters
                        for cluster_id, cluster_info in cluster_results['cluster_analysis'].items():
                            with st.expander(f"Cluster {cluster_id}: {cluster_info['type']} ({cluster_info['size']} números)"):
                                st.write(f"**Frecuencia Promedio:** {cluster_info['avg_frequency']:.4f}")
                                st.write(f"**Números:** {', '.join(map(str, cluster_info['numbers']))}")
                        
                        # Visualización de clusters
                        cluster_viz_data = []
                        for cluster_id, cluster_info in cluster_results['cluster_analysis'].items():
                            for num in cluster_info['numbers']:
                                cluster_viz_data.append({
                                    'Número': num,
                                    'Cluster': f"Cluster {cluster_id}",
                                    'Tipo': cluster_info['type'],
                                    'Frecuencia': cluster_info['avg_frequency']
                                })
                        
                        df_clusters = pd.DataFrame(cluster_viz_data)
                        fig = px.scatter(
                            df_clusters,
                            x='Número',
                            y='Frecuencia',
                            color='Tipo',
                            title="Distribución de Números por Clusters",
                            hover_data=['Cluster']
                        )
                        st.plotly_chart(fig, width='stretch')
                    
                    else:
                        st.warning("No se pudo realizar el análisis de clustering.")
            
            elif analysis_type == "Tests de Aleatoriedad":
                with st.spinner("Ejecutando tests de aleatoriedad..."):
                    randomness_results = analyzer.test_randomness_quality(days=complex_analysis_days)
                    
                    if randomness_results:
                        st.subheader("🎲 Tests de Calidad de Aleatoriedad")
                        
                        # Métricas principales
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Puntuación Aleatoriedad", f"{randomness_results['randomness_score']}/100")
                        
                        with col2:
                            st.metric("Evaluación General", randomness_results['quality_assessment'])
                        
                        with col3:
                            st.metric("Chi-cuadrado (p)", f"{randomness_results['chi_square']['p_value']:.4f}")
                        
                        with col4:
                            st.metric("Kolmogorov-Smirnov (p)", f"{randomness_results['kolmogorov_smirnov']['p_value']:.4f}")
                        
                        # Detalles de tests
                        st.subheader("📋 Detalles de Tests Estadísticos")
                        
                        test_details = [
                            {
                                'Test': 'Chi-cuadrado',
                                'Estadística': f"{randomness_results['chi_square']['statistic']:.2f}",
                                'P-valor': f"{randomness_results['chi_square']['p_value']:.4f}",
                                'Interpretación': 'Aleatorio' if randomness_results['chi_square']['p_value'] > 0.05 else 'No Aleatorio'
                            },
                            {
                                'Test': 'Kolmogorov-Smirnov',
                                'Estadística': f"{randomness_results['kolmogorov_smirnov']['statistic']:.4f}",
                                'P-valor': f"{randomness_results['kolmogorov_smirnov']['p_value']:.4f}",
                                'Interpretación': 'Aleatorio' if randomness_results['kolmogorov_smirnov']['p_value'] > 0.05 else 'No Aleatorio'
                            },
                            {
                                'Test': 'Runs Test',
                                'Estadística': f"{randomness_results['runs_test']['n_runs']}",
                                'P-valor': f"{randomness_results['runs_test']['p_value']:.4f}",
                                'Interpretación': 'Aleatorio' if randomness_results['runs_test']['p_value'] > 0.05 else 'No Aleatorio'
                            }
                        ]
                        
                        df_tests = pd.DataFrame(test_details)
                        st.dataframe(df_tests, width='stretch')
                        
                        # Estadísticas de secuencia
                        st.subheader("📊 Estadísticas de la Secuencia")
                        seq_stats = randomness_results['sequence_stats']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Media", f"{seq_stats['mean']:.2f}")
                        with col2:
                            st.metric("Desviación Estándar", f"{seq_stats['std']:.2f}")
                        with col3:
                            st.metric("Mediana", f"{seq_stats['median']:.2f}")
                    
                    else:
                        st.warning("No se pudieron ejecutar los tests de aleatoriedad.")
        
        # Panel informativo
        with st.expander("ℹ️ Información sobre Análisis Estadísticos Complejos"):
            st.write("""
            **Análisis Implementados:**
            
            🔹 **Autocorrelación**: Detecta patrones no aleatorios usando tests Durbin-Watson y Ljung-Box
            
            🔹 **Series Temporales**: Modelo ARIMA para pronósticos, detección de ciclos con FFT, análisis de tendencias
            
            🔹 **Clustering**: Agrupación K-means de números basada en frecuencia y co-ocurrencia
            
            🔹 **Tests de Aleatoriedad**: Chi-cuadrado, Kolmogorov-Smirnov, y Runs test para evaluar calidad aleatoria
            
            🔹 **Fórmula Predictiva**: Integra todos los análisis en un sistema de puntuación unificado
            
            **Fundamento Científico:**
            - Basado en literatura académica de análisis estadístico para series temporales
            - Utiliza métodos establecidos en econometría y análisis de datos financieros
            - Implementa tests estándar de aleatoriedad y autocorrelación
            
            **Limitaciones:**
            - Los sorteos de lotería están diseñados para ser aleatorios
            - Ningún análisis puede garantizar predicciones exactas
            - Los resultados son para fines educativos y de investigación
            """)
    
    else:
        st.warning("⚠️ Se requieren datos históricos para ejecutar análisis estadísticos complejos.")

with tab9:
    st.header("📩 Mis Predicciones y Notificaciones")
    
    # Sistema de identificación de usuario
    st.subheader("👤 Identificación de Usuario")
    
    # Usar session state para mantener el user_id
    if 'user_id' not in st.session_state:
        st.session_state.user_id = ""
    
    user_id = st.text_input(
        "Ingresa tu ID de usuario único",
        value=st.session_state.user_id,
        help="Usa un identificador único como tu email o nombre de usuario para asociar tus predicciones",
        placeholder="ej: usuario@email.com o mi_usuario_123"
    )
    
    if user_id:
        st.session_state.user_id = user_id
        
        # Obtener notificaciones no leídas
        unread_count = db.get_unread_notifications_count(user_id)
        
        if unread_count > 0:
            st.warning(f"🔔 Tienes {unread_count} notificación(es) nueva(s)!")
        
        # Crear tabs secundarias
        subtab1, subtab2, subtab3 = st.tabs([
            "🎯 Guardar Predicciones",
            "📋 Mis Predicciones",
            "🔔 Notificaciones"
        ])
        
        with subtab1:
            st.subheader("🎯 Guardar Nuevas Predicciones")
            
            if total_draws > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    save_num_predictions = st.slider(
                        "Cantidad de números a predecir",
                        min_value=5,
                        max_value=20,
                        value=10,
                        help="Número de predicciones a generar y guardar"
                    )
                
                with col2:
                    save_confidence_threshold = st.slider(
                        "Umbral de confianza (%)",
                        min_value=50,
                        max_value=95,
                        value=70,
                        help="Nivel mínimo de confianza para las predicciones"
                    )
                
                # Área para notas del usuario
                user_notes = st.text_area(
                    "Notas personales (opcional)",
                    help="Agrega notas sobre esta predicción",
                    placeholder="Ej: Predicción para el sorteo de fin de semana..."
                )
                
                if st.button("🎯 Generar y Guardar Predicciones", type="primary"):
                    with st.spinner("Generando y guardando predicciones..."):
                        # Generar predicciones usando el sistema existente
                        predictions = predictor.generate_predictions(
                            method=prediction_method.lower().replace(" ", "_"),
                            days=days_to_analyze,
                            num_predictions=save_num_predictions,
                            confidence_threshold=save_confidence_threshold / 100
                        )
                        
                        if predictions:
                            # Extraer solo los números de las predicciones
                            predicted_numbers = [pred[0] for pred in predictions]
                            
                            # Guardar en base de datos
                            prediction_id = db.save_user_prediction(
                                user_id=user_id,
                                predicted_numbers=predicted_numbers,
                                prediction_method=prediction_method,
                                confidence_threshold=save_confidence_threshold / 100,
                                analysis_days=days_to_analyze,
                                notes=user_notes
                            )
                            
                            if prediction_id > 0:
                                st.success(f"✅ Predicción guardada exitosamente (ID: {prediction_id})")
                                
                                # Mostrar predicciones guardadas
                                st.subheader("🎯 Números Predichos y Guardados")
                                
                                cols = st.columns(5)
                                for i, number in enumerate(predicted_numbers[:10]):
                                    with cols[i % 5]:
                                        st.metric(
                                            label=f"#{i+1}",
                                            value=str(number),
                                            help=f"Número predicho con confianza {save_confidence_threshold}%"
                                        )
                                
                                st.info("🔔 Ahora recibirás notificaciones automáticamente cuando alguno de estos números coincida con los sorteos ganadores.")
                            else:
                                st.error("❌ Error al guardar la predicción. Inténtalo de nuevo.")
                        else:
                            st.error("❌ No se pudieron generar predicciones. Verifica los datos.")
            else:
                st.warning("⚠️ Se requieren datos históricos para generar predicciones.")
        
        with subtab2:
            st.subheader("📋 Mis Predicciones Guardadas")
            
            # Filtros
            col1, col2 = st.columns(2)
            
            with col1:
                show_active_only = st.checkbox("Solo predicciones activas", value=True)
            
            with col2:
                if st.button("🔄 Actualizar Lista"):
                    st.rerun()
            
            # Obtener predicciones del usuario
            user_predictions = db.get_user_predictions(user_id, active_only=show_active_only)
            
            if user_predictions:
                st.write(f"📊 **Total de predicciones:** {len(user_predictions)}")
                
                for i, prediction in enumerate(user_predictions):
                    with st.expander(f"🎯 Predicción {prediction['id']} - {prediction['prediction_date'][:10]}", expanded=i==0):
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**Información:**")
                            st.write(f"**ID:** {prediction['id']}")
                            st.write(f"**Método:** {prediction['prediction_method']}")
                            st.write(f"**Fecha:** {prediction['prediction_date'][:10]}")
                            if prediction['confidence_threshold']:
                                st.write(f"**Confianza:** {prediction['confidence_threshold']:.1%}")
                            st.write(f"**Estado:** {'🟢 Activa' if prediction['is_active'] else '🔴 Inactiva'}")
                        
                        with col2:
                            st.write("**Números Predichos:**")
                            # Mostrar números en filas de 5
                            numbers = prediction['predicted_numbers']
                            for j in range(0, len(numbers), 5):
                                row_numbers = numbers[j:j+5]
                                st.write(" | ".join([f"**{num}**" for num in row_numbers]))
                        
                        with col3:
                            st.write("**Acciones:**")
                            
                            if prediction['is_active']:
                                if st.button(f"🔴 Desactivar", key=f"deactivate_{prediction['id']}"):
                                    if db.deactivate_user_prediction(prediction['id']):
                                        st.success("Predicción desactivada")
                                        st.rerun()
                                    else:
                                        st.error("Error al desactivar")
                        
                        if prediction['notes']:
                            st.write(f"**Notas:** {prediction['notes']}")
                        
                        # Verificar si hay notificaciones para esta predicción
                        notifications = db.get_user_notifications(user_id)
                        prediction_notifications = [n for n in notifications if n['prediction_id'] == prediction['id']]
                        
                        if prediction_notifications:
                            st.success(f"🎉 Esta predicción ha tenido {len(prediction_notifications)} coincidencia(s)!")
            else:
                st.info("📝 No tienes predicciones guardadas. Usa la pestaña 'Guardar Predicciones' para crear tu primera predicción.")
        
        with subtab3:
            st.subheader("🔔 Mis Notificaciones")
            
            # Botones de acción
            col1, col2 = st.columns(2)
            
            with col1:
                show_unread_only = st.checkbox("Solo no leídas", value=True)
            
            with col2:
                if st.button("✅ Marcar todas como leídas"):
                    marked_count = db.mark_all_user_notifications_as_read(user_id)
                    if marked_count > 0:
                        st.success(f"Se marcaron {marked_count} notificaciones como leídas")
                        st.rerun()
                    else:
                        st.info("No había notificaciones por marcar")
            
            # Obtener notificaciones
            user_notifications = db.get_user_notifications(user_id, unread_only=show_unread_only)
            
            if user_notifications:
                st.write(f"📧 **Total de notificaciones:** {len(user_notifications)}")
                
                for notification in user_notifications:
                    # Estilo de la notificación según si está leída o no
                    if notification['is_read']:
                        container = st.container()
                        emoji = "📨"
                    else:
                        container = st.container()
                        emoji = "🔔"
                    
                    with container:
                        col1, col2, col3 = st.columns([6, 2, 2])
                        
                        with col1:
                            st.write(f"{emoji} {notification['notification_message']}")
                            st.caption(f"Fecha: {notification['matched_at'][:10]} | Predicción ID: {notification['prediction_id']}")
                        
                        with col2:
                            if notification['winning_position']:
                                positions = {1: "1ra", 2: "2da", 3: "3ra"}
                                st.write(f"**{positions.get(notification['winning_position'], 'N/A')} posición**")
                        
                        with col3:
                            if not notification['is_read']:
                                if st.button(f"✅ Marcar leída", key=f"read_{notification['id']}"):
                                    if db.mark_notification_as_read(notification['id']):
                                        st.success("Marcada como leída")
                                        st.rerun()
                        
                        st.divider()
            else:
                if show_unread_only:
                    st.info("🎉 No tienes notificaciones nuevas.")
                else:
                    st.info("📭 No tienes notificaciones.")
            
            # Información sobre el sistema de notificaciones
            with st.expander("ℹ️ ¿Cómo funcionan las notificaciones?"):
                st.write("""
                **Sistema de Notificaciones Automáticas:**
                
                🔹 **Detección Automática**: El sistema compara automáticamente los números ganadores de los sorteos con tus predicciones activas.
                
                🔹 **Notificación Inmediata**: Cuando uno de tus números predichos coincide con un número ganador, recibes una notificación instantánea.
                
                🔹 **Detalles Completos**: Cada notificación incluye el número ganador, la fecha del sorteo, la posición (1ra, 2da, 3ra) y la predicción que coincidió.
                
                🔹 **Gestión de Estados**: Puedes marcar notificaciones como leídas y filtrar entre leídas y no leídas.
                
                **Consejos:**
                - Mantén tus predicciones activas para seguir recibiendo notificaciones
                - Revisa regularmente tus notificaciones para no perderte coincidencias
                - Usa las notas en las predicciones para recordar tu estrategia
                """)
    else:
        st.info("👤 Por favor, ingresa tu ID de usuario para acceder a tus predicciones y notificaciones.")

# Footer
st.markdown("---")
st.markdown(
    "🎯 **Sistema de Análisis Estadístico Quiniela Loteka** | "
    "Desarrollado para análisis educativo de patrones en lotería"
)
