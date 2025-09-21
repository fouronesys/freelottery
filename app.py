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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Dashboard Principal",
    "🔢 Análisis de Números",
    "🎯 Predicciones",
    "📊 Estadísticas Avanzadas",
    "⏰ Análisis Temporal",
    "🤝 Co-ocurrencia y Patrones",
    "📅 Recomendaciones por Día"
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
    st.write("Sistema de recomendaciones que combina múltiples análisis para sugerir números según el día de la semana seleccionado.")
    
    if total_draws > 0:
        # Selector de día
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
        
        if st.button("🎯 Generar Recomendaciones Inteligentes", type="primary"):
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

# Footer
st.markdown("---")
st.markdown(
    "🎯 **Sistema de Análisis Estadístico Quiniela Loteka** | "
    "Desarrollado para análisis educativo de patrones en lotería"
)
