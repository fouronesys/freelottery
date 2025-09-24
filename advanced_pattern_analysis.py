#!/usr/bin/env python3
"""
Análisis avanzado de patrones en los datos históricos de la Quiniela Loteka
para mejorar la precisión del sistema de predicciones
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import statistics
import math
from collections import defaultdict, Counter
from database import DatabaseManager
from analyzer import StatisticalAnalyzer

class AdvancedPatternAnalyzer:
    """Análisis avanzado de patrones para mejorar predicciones"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = StatisticalAnalyzer(db_manager)
        self.patterns = {}
        
    def analyze_all_patterns(self, days: int = 5475) -> Dict[str, Any]:
        """Ejecuta todos los análisis de patrones avanzados"""
        
        print("🔍 INICIANDO ANÁLISIS AVANZADO DE PATRONES")
        print("="*60)
        
        results = {
            'analysis_period': days,
            'analysis_date': datetime.now().isoformat(),
            'patterns': {}
        }
        
        # 1. Análisis de secuencias y periodicidad
        print("\n1. ANÁLISIS DE SECUENCIAS Y PERIODICIDAD:")
        sequence_patterns = self._analyze_sequence_patterns(days)
        results['patterns']['sequences'] = sequence_patterns
        
        # 2. Análisis de correlaciones entre números
        print("\n2. ANÁLISIS DE CORRELACIONES ENTRE NÚMEROS:")
        correlation_patterns = self._analyze_number_correlations(days)
        results['patterns']['correlations'] = correlation_patterns
        
        # 3. Análisis de distribución temporal
        print("\n3. ANÁLISIS DE DISTRIBUCIÓN TEMPORAL:")
        temporal_patterns = self._analyze_temporal_distribution(days)
        results['patterns']['temporal'] = temporal_patterns
        
        # 4. Análisis de gaps (intervalos entre apariciones)
        print("\n4. ANÁLISIS DE GAPS (INTERVALOS):")
        gap_patterns = self._analyze_gap_patterns(days)
        results['patterns']['gaps'] = gap_patterns
        
        # 5. Análisis de dígitos y matemático
        print("\n5. ANÁLISIS DE DÍGITOS Y MATEMÁTICO:")
        digit_patterns = self._analyze_digit_mathematics(days)
        results['patterns']['digits'] = digit_patterns
        
        # 6. Análisis de clusters y agrupaciones
        print("\n6. ANÁLISIS DE CLUSTERS Y AGRUPACIONES:")
        cluster_patterns = self._analyze_number_clusters(days)
        results['patterns']['clusters'] = cluster_patterns
        
        # 7. Generar métricas de calidad predictiva
        print("\n7. MÉTRICAS DE CALIDAD PREDICTIVA:")
        quality_metrics = self._calculate_predictive_quality(results['patterns'])
        results['quality_metrics'] = quality_metrics
        
        print(f"\n🎯 ANÁLISIS COMPLETADO: {len(results['patterns'])} categorías de patrones analizadas")
        return results
    
    def _analyze_sequence_patterns(self, days: int) -> Dict[str, Any]:
        """Analiza patrones en secuencias de números"""
        
        # Obtener todos los sorteos ordenados por fecha
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        if len(draws) < 50:  # Mínimo para análisis confiable
            return {'error': 'Datos insuficientes para análisis de secuencias'}
        
        # Organizar por fecha y posición
        dates_data = defaultdict(list)
        for draw in draws:
            date_str = str(draw[0])
            number = draw[1]
            position = draw[2] if len(draw) > 2 else 1
            dates_data[date_str].append((number, position))
        
        # Análisis de secuencias consecutivas
        sequences = []
        number_sequences = []
        
        sorted_dates = sorted(dates_data.keys())
        for date in sorted_dates:
            if len(dates_data[date]) >= 3:  # Quiniela tiene 3 números
                sorted_numbers = sorted([num for num, pos in dates_data[date]])
                sequences.append(sorted_numbers)
                number_sequences.extend(sorted_numbers)
        
        # Patrones de repetición
        repetition_patterns = {}
        if len(sequences) >= 2:
            # Números que aparecen en sorteos consecutivos
            consecutive_repeats = 0
            for i in range(len(sequences) - 1):
                current_set = set(sequences[i])
                next_set = set(sequences[i + 1])
                intersection = current_set.intersection(next_set)
                if intersection:
                    consecutive_repeats += len(intersection)
                    
            repetition_patterns['consecutive_repeat_rate'] = consecutive_repeats / (len(sequences) - 1)
        
        # Análisis de periodicidad
        periodicity = {}
        if len(number_sequences) >= 100:
            # Buscar ciclos de números
            for period in [7, 14, 21, 30]:  # Períodos comunes
                cycle_count = 0
                for i in range(period, len(number_sequences)):
                    if number_sequences[i] == number_sequences[i - period]:
                        cycle_count += 1
                periodicity[f'cycle_{period}'] = cycle_count / (len(number_sequences) - period)
        
        print(f"   📊 Analizadas {len(sequences)} secuencias de sorteos")
        print(f"   🔄 Tasa de repetición consecutiva: {repetition_patterns.get('consecutive_repeat_rate', 0):.3f}")
        
        return {
            'total_sequences': len(sequences),
            'repetition_patterns': repetition_patterns,
            'periodicity': periodicity,
            'sequence_sample': sequences[:5] if sequences else []
        }
    
    def _analyze_number_correlations(self, days: int) -> Dict[str, Any]:
        """Analiza correlaciones avanzadas entre números"""
        
        # Obtener datos de co-ocurrencia
        correlations = self.analyzer.calculate_correlations(days)
        
        # Manejar diferentes formatos de respuesta
        if isinstance(correlations, dict) and 'error' in correlations:
            return correlations
        
        # Si correlations es una lista, convertir a formato manejable
        if isinstance(correlations, list):
            if not correlations:
                return {'error': 'No se encontraron correlaciones'}
            
            # Procesar lista de correlaciones
            significant_pairs = []
            for item in correlations:
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    try:
                        num1, num2, correlation = item[0], item[1], item[2]
                        significance_text = item[3] if len(item) > 3 else "Media"
                        
                        # Convertir significancia textual a numérica
                        sig_numeric = 0.01 if significance_text == "Alta" else 0.05 if significance_text == "Media" else 0.1
                        
                        if correlation > 0.1:
                            significant_pairs.append((f"({num1},{num2})", correlation, sig_numeric))
                    except:
                        continue
        else:
            # Manejar formato dict
            pair_data = correlations.get('correlation_matrix', {}) if isinstance(correlations, dict) else {}
            significant_pairs = []
            
            for pair, data in pair_data.items():
                if isinstance(data, dict) and 'correlation' in data:
                    correlation = data['correlation']
                    significance = data.get('significance', 0)
                    if correlation > 0.1 and significance < 0.05:  # Umbral de significancia
                        significant_pairs.append((pair, correlation, significance))
        
        # Ordenar por correlación
        significant_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Análisis de números que tienden a aparecer juntos
        co_occurrence = {}
        strong_correlations = significant_pairs[:10]
        
        for pair, corr, sig in strong_correlations:
            try:
                num1, num2 = map(int, pair.strip('()').split(','))
                co_occurrence[f"{num1}-{num2}"] = {
                    'correlation': corr,
                    'significance': sig,
                    'strength': 'alta' if corr > 0.2 else 'media' if corr > 0.1 else 'baja'
                }
            except:
                continue
        
        print(f"   📈 Encontradas {len(significant_pairs)} correlaciones significativas")
        print(f"   🔗 Top 3 correlaciones:")
        for i, (pair, corr, sig) in enumerate(strong_correlations[:3]):
            print(f"      {i+1}. {pair}: r={corr:.3f} (p={sig:.3f})")
        
        return {
            'significant_correlations_count': len(significant_pairs),
            'strong_correlations': co_occurrence,
            'top_pairs': strong_correlations[:10],
            'correlation_strength_distribution': {
                'alta': len([p for p in significant_pairs if p[1] > 0.2]),
                'media': len([p for p in significant_pairs if 0.1 < p[1] <= 0.2]),
                'baja': len([p for p in significant_pairs if p[1] <= 0.1])
            }
        }
    
    def _analyze_temporal_distribution(self, days: int) -> Dict[str, Any]:
        """Analiza distribución temporal de números"""
        
        temporal_trends = self.analyzer.get_temporal_trends(days)
        
        if not temporal_trends:
            return {'error': 'No se pudieron obtener tendencias temporales'}
        
        # Análisis de tendencias por día de la semana
        weekday_patterns = {}
        seasonal_patterns = {}
        
        # Obtener datos detallados
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if draws:
            # Organizar por día de la semana
            weekday_numbers = defaultdict(list)
            month_numbers = defaultdict(list)
            
            for draw in draws:
                try:
                    draw_date = datetime.strptime(str(draw[0]), '%Y-%m-%d')
                    weekday = draw_date.weekday()  # 0=lunes, 6=domingo
                    month = draw_date.month
                    number = draw[1]
                    
                    weekday_numbers[weekday].append(number)
                    month_numbers[month].append(number)
                except:
                    continue
            
            # Análisis por día de la semana
            weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            for weekday, numbers in weekday_numbers.items():
                if numbers:
                    most_common = Counter(numbers).most_common(3)
                    avg_number = statistics.mean(numbers)
                    weekday_patterns[weekday_names[weekday]] = {
                        'most_common': most_common,
                        'average': avg_number,
                        'sample_size': len(numbers)
                    }
            
            # Análisis estacional (por mes)
            month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            for month, numbers in month_numbers.items():
                if numbers:
                    most_common = Counter(numbers).most_common(3)
                    avg_number = statistics.mean(numbers)
                    seasonal_patterns[month_names[month-1]] = {
                        'most_common': most_common,
                        'average': avg_number,
                        'sample_size': len(numbers)
                    }
        
        print(f"   📅 Patrones de día de semana: {len(weekday_patterns)} días analizados")
        print(f"   🌙 Patrones estacionales: {len(seasonal_patterns)} meses analizados")
        
        return {
            'temporal_trends': temporal_trends,
            'weekday_patterns': weekday_patterns,
            'seasonal_patterns': seasonal_patterns,
            'analysis_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days_analyzed': days
            }
        }
    
    def _analyze_gap_patterns(self, days: int) -> Dict[str, Any]:
        """Analiza patrones en los intervalos entre apariciones de números"""
        
        # Obtener todas las apariciones de cada número
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 100:
            return {'error': 'Datos insuficientes para análisis de gaps'}
        
        # Organizar apariciones por número
        number_appearances = defaultdict(list)
        
        for draw in draws:
            try:
                draw_date = datetime.strptime(str(draw[0]), '%Y-%m-%d')
                number = draw[1]
                number_appearances[number].append(draw_date)
            except:
                continue
        
        # Calcular gaps para cada número
        gap_analysis = {}
        
        for number, dates in number_appearances.items():
            if len(dates) >= 3:  # Mínimo para calcular gaps
                dates.sort()
                gaps = []
                
                for i in range(1, len(dates)):
                    gap = (dates[i] - dates[i-1]).days
                    gaps.append(gap)
                
                if gaps:
                    gap_analysis[number] = {
                        'appearances': len(dates),
                        'average_gap': statistics.mean(gaps),
                        'min_gap': min(gaps),
                        'max_gap': max(gaps),
                        'median_gap': statistics.median(gaps),
                        'gap_std': statistics.stdev(gaps) if len(gaps) > 1 else 0,
                        'last_appearance': dates[-1].strftime('%Y-%m-%d'),
                        'days_since_last': (datetime.now() - dates[-1]).days
                    }
        
        # Identificar números con gaps anómalos
        overdue_numbers = []
        regular_numbers = []
        
        for number, data in gap_analysis.items():
            avg_gap = data['average_gap']
            days_since = data['days_since_last']
            
            # Número considerado "atrasado" si ha pasado más del doble de su gap promedio
            if days_since > avg_gap * 2:
                overdue_numbers.append((number, days_since, avg_gap))
            elif abs(days_since - avg_gap) < data['gap_std']:
                regular_numbers.append((number, days_since, avg_gap))
        
        # Ordenar números atrasados por días desde última aparición
        overdue_numbers.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   📊 Analizados {len(gap_analysis)} números con historial suficiente")
        print(f"   ⏰ Números 'atrasados': {len(overdue_numbers)}")
        print(f"   🔄 Números 'regulares': {len(regular_numbers)}")
        
        return {
            'total_numbers_analyzed': len(gap_analysis),
            'gap_statistics': gap_analysis,
            'overdue_numbers': overdue_numbers[:10],  # Top 10 más atrasados
            'regular_numbers': regular_numbers[:10],   # Top 10 más regulares
            'average_gaps_distribution': {
                'short_gaps': len([n for n, d in gap_analysis.items() if d['average_gap'] < 7]),
                'medium_gaps': len([n for n, d in gap_analysis.items() if 7 <= d['average_gap'] < 21]),
                'long_gaps': len([n for n, d in gap_analysis.items() if d['average_gap'] >= 21])
            }
        }
    
    def _analyze_digit_mathematics(self, days: int) -> Dict[str, Any]:
        """Analiza patrones matemáticos y de dígitos"""
        
        # Obtener todos los números de los últimos sorteos
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 50:
            return {'error': 'Datos insuficientes para análisis de dígitos'}
        
        numbers = [draw[1] for draw in draws]
        
        # Análisis de dígitos
        units_digits = [num % 10 for num in numbers]
        tens_digits = [num // 10 for num in numbers]
        
        digit_patterns = {
            'units_distribution': dict(Counter(units_digits)),
            'tens_distribution': dict(Counter(tens_digits)),
            'units_most_common': Counter(units_digits).most_common(3),
            'tens_most_common': Counter(tens_digits).most_common(3)
        }
        
        # Análisis matemático
        math_patterns = {}
        
        # Distribución par/impar
        even_count = sum(1 for num in numbers if num % 2 == 0)
        odd_count = len(numbers) - even_count
        math_patterns['parity'] = {
            'even_ratio': even_count / len(numbers),
            'odd_ratio': odd_count / len(numbers),
            'even_count': even_count,
            'odd_count': odd_count
        }
        
        # Análisis de rangos
        range_distribution = {
            '00-19': len([n for n in numbers if 0 <= n <= 19]),
            '20-39': len([n for n in numbers if 20 <= n <= 39]),
            '40-59': len([n for n in numbers if 40 <= n <= 59]),
            '60-79': len([n for n in numbers if 60 <= n <= 79]),
            '80-99': len([n for n in numbers if 80 <= n <= 99])
        }
        
        math_patterns['range_distribution'] = range_distribution
        
        # Análisis de sumas de dígitos
        digit_sums = [sum(divmod(num, 10)) for num in numbers]
        math_patterns['digit_sums'] = {
            'average_sum': statistics.mean(digit_sums),
            'most_common_sums': Counter(digit_sums).most_common(5),
            'sum_range': f"{min(digit_sums)}-{max(digit_sums)}"
        }
        
        print(f"   🔢 Distribución de unidades: {dict(Counter(units_digits).most_common(3))}")
        print(f"   🔢 Distribución de decenas: {dict(Counter(tens_digits).most_common(3))}")
        print(f"   ⚖️ Par/Impar: {even_count}/{odd_count} ({even_count/len(numbers):.1%}/{odd_count/len(numbers):.1%})")
        
        return {
            'digit_patterns': digit_patterns,
            'mathematical_patterns': math_patterns,
            'sample_size': len(numbers)
        }
    
    def _analyze_number_clusters(self, days: int) -> Dict[str, Any]:
        """Analiza agrupaciones y clusters de números"""
        
        try:
            cluster_results = self.analyzer.analyze_number_clustering(days)
            
            if 'error' in cluster_results:
                return cluster_results
            
            # Análisis adicional de clusters
            clusters = cluster_results.get('clusters', {})
            cluster_analysis = {}
            
            for cluster_id, numbers in clusters.items():
                if numbers:
                    # Calcular características del cluster
                    avg_number = statistics.mean(numbers)
                    number_range = max(numbers) - min(numbers)
                    cluster_size = len(numbers)
                    
                    cluster_analysis[f'cluster_{cluster_id}'] = {
                        'numbers': sorted(numbers),
                        'size': cluster_size,
                        'average': avg_number,
                        'range': number_range,
                        'min_number': min(numbers),
                        'max_number': max(numbers),
                        'density': cluster_size / (number_range + 1) if number_range > 0 else 1.0
                    }
            
            print(f"   📊 Identificados {len(cluster_analysis)} clusters de números")
            for cluster_id, data in cluster_analysis.items():
                print(f"      {cluster_id}: {data['size']} números, rango {data['min_number']}-{data['max_number']}")
            
            return {
                'cluster_analysis': cluster_analysis,
                'cluster_quality': cluster_results.get('silhouette_score', 0),
                'total_clusters': len(cluster_analysis)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis de clusters: {str(e)}'}
    
    def _calculate_predictive_quality(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de calidad predictiva basadas en los patrones encontrados"""
        
        quality_metrics = {
            'pattern_strength': {},
            'data_quality': {},
            'predictive_indicators': {}
        }
        
        # Evaluar fortaleza de patrones
        if 'correlations' in patterns and not 'error' in patterns['correlations']:
            corr_data = patterns['correlations']
            strong_corrs = corr_data.get('correlation_strength_distribution', {}).get('alta', 0)
            total_corrs = corr_data.get('significant_correlations_count', 0)
            
            quality_metrics['pattern_strength']['correlation_strength'] = {
                'strong_correlations': strong_corrs,
                'total_significant': total_corrs,
                'strength_ratio': strong_corrs / total_corrs if total_corrs > 0 else 0
            }
        
        # Evaluar calidad de datos temporales
        if 'temporal' in patterns and not 'error' in patterns['temporal']:
            temp_data = patterns['temporal']
            weekday_coverage = len(temp_data.get('weekday_patterns', {}))
            seasonal_coverage = len(temp_data.get('seasonal_patterns', {}))
            
            quality_metrics['data_quality']['temporal_coverage'] = {
                'weekday_coverage': weekday_coverage / 7,  # Proporción de días cubiertos
                'seasonal_coverage': seasonal_coverage / 12,  # Proporción de meses cubiertos
                'overall_temporal_quality': (weekday_coverage + seasonal_coverage) / 19  # /19 = 7+12
            }
        
        # Evaluar indicadores predictivos
        predictive_score = 0.0
        total_indicators = 0
        
        # Factor: Gaps (números atrasados)
        if 'gaps' in patterns and not 'error' in patterns['gaps']:
            overdue_count = len(patterns['gaps'].get('overdue_numbers', []))
            if overdue_count > 0:
                predictive_score += 0.3  # Los gaps son buenos predictores
            total_indicators += 1
        
        # Factor: Correlaciones fuertes
        if 'correlations' in patterns and not 'error' in patterns['correlations']:
            strong_corrs = patterns['correlations'].get('correlation_strength_distribution', {}).get('alta', 0)
            if strong_corrs > 3:  # Al menos 3 correlaciones fuertes
                predictive_score += 0.4
            total_indicators += 1
        
        # Factor: Patrones de clusters
        if 'clusters' in patterns and not 'error' in patterns['clusters']:
            cluster_quality = patterns['clusters'].get('cluster_quality', 0)
            if cluster_quality > 0.3:  # Silhouette score > 0.3 es bueno
                predictive_score += 0.3
            total_indicators += 1
        
        quality_metrics['predictive_indicators']['overall_predictive_quality'] = {
            'score': predictive_score / total_indicators if total_indicators > 0 else 0,
            'indicators_evaluated': total_indicators,
            'quality_level': 'alta' if predictive_score / max(total_indicators, 1) > 0.7 else 
                           'media' if predictive_score / max(total_indicators, 1) > 0.4 else 'baja'
        }
        
        print(f"   🎯 Calidad predictiva general: {quality_metrics['predictive_indicators']['overall_predictive_quality']['quality_level']}")
        print(f"   📊 Score: {quality_metrics['predictive_indicators']['overall_predictive_quality']['score']:.3f}")
        
        return quality_metrics

def main():
    """Función principal para ejecutar el análisis"""
    
    print("🎲 ANÁLISIS AVANZADO DE PATRONES - QUINIELA LOTEKA")
    print("="*70)
    
    # Inicializar
    db = DatabaseManager()
    analyzer = AdvancedPatternAnalyzer(db)
    
    # Ejecutar análisis completo
    days_to_analyze = 1825  # ~5 años de datos para balance entre profundidad y relevancia
    results = analyzer.analyze_all_patterns(days_to_analyze)
    
    # Mostrar resumen final
    print(f"\n📋 RESUMEN EJECUTIVO:")
    print(f"   📅 Período analizado: {days_to_analyze} días (~{days_to_analyze/365:.1f} años)")
    print(f"   🔍 Categorías de patrones: {len(results['patterns'])}")
    
    if 'quality_metrics' in results:
        quality = results['quality_metrics']['predictive_indicators']['overall_predictive_quality']
        print(f"   🎯 Calidad predictiva: {quality['quality_level']} ({quality['score']:.3f})")
    
    # Guardar resultados
    import json
    with open('pattern_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Resultados guardados en: pattern_analysis_results.json")
    return results

if __name__ == "__main__":
    try:
        results = main()
        print("\n🎉 ANÁLISIS COMPLETADO EXITOSAMENTE")
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        raise