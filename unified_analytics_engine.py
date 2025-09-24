#!/usr/bin/env python3
"""
Motor de Análisis Unificado - Quiniela Loteka
Consolida toda la funcionalidad de análisis en un solo motor eficiente
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import statistics
from collections import defaultdict, Counter
from database import DatabaseManager

class UnifiedAnalyticsEngine:
    """Motor de análisis unificado con cache inteligente"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.number_range = (0, 99)
        
        # Cache con diferentes niveles de TTL
        self._cache = {
            'recent': {},      # TTL: 5 minutos
            'medium': {},      # TTL: 30 minutos  
            'long': {}         # TTL: 2 horas
        }
        
        self._cache_ttl = {
            'recent': 300,     # 5 minutos
            'medium': 1800,    # 30 minutos
            'long': 7200       # 2 horas
        }
    
    def get_dashboard_overview(self, days: int = 365) -> Dict[str, Any]:
        """Obtiene resumen completo para dashboard principal"""
        
        cache_key = f"overview_{days}"
        cached = self._get_cached_data('medium', cache_key)
        if cached:
            return cached
        
        print(f"📊 Generando resumen de {days} días...")
        
        # Datos básicos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if not draws:
            return {'error': 'No hay datos disponibles'}
        
        # Estadísticas generales
        total_draws = len(draws)
        unique_numbers = len(set(draw[1] for draw in draws))
        unique_dates = len(set(str(draw[0]) for draw in draws))
        
        # Números más frecuentes (Top 10)
        number_counts = Counter(draw[1] for draw in draws)
        hot_numbers = number_counts.most_common(10)
        
        # Números menos frecuentes
        all_numbers = set(range(0, 100))
        drawn_numbers = set(draw[1] for draw in draws)
        missing_numbers = list(all_numbers - drawn_numbers)
        
        cold_numbers = []
        for num in all_numbers:
            count = number_counts.get(num, 0)
            cold_numbers.append((num, count))
        cold_numbers.sort(key=lambda x: x[1])
        
        # Análisis temporal reciente (últimos 30 días)
        recent_date = end_date - timedelta(days=30)
        recent_draws = [d for d in draws if datetime.strptime(str(d[0]), '%Y-%m-%d') >= recent_date]
        recent_activity = len(recent_draws)
        
        # Distribución por rangos
        range_distribution = self._calculate_range_distribution(draws)
        
        # Últimos sorteos
        latest_draws = self._get_latest_draws(5)
        
        overview = {
            'period': {
                'days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'general_stats': {
                'total_draws': total_draws,
                'unique_numbers': unique_numbers,
                'unique_dates': unique_dates,
                'draws_per_day': round(total_draws / max(unique_dates, 1), 2),
                'coverage_percentage': round((unique_numbers / 100) * 100, 1)
            },
            'hot_numbers': [{'number': num, 'count': count, 'percentage': round((count/total_draws)*100, 1)} 
                           for num, count in hot_numbers],
            'cold_numbers': [{'number': num, 'count': count, 'percentage': round((count/total_draws)*100, 1)} 
                            for num, count in cold_numbers[:10]],
            'missing_numbers': missing_numbers,
            'recent_activity': {
                'last_30_days': recent_activity,
                'daily_average': round(recent_activity / 30, 1)
            },
            'range_distribution': range_distribution,
            'latest_draws': latest_draws,
            'last_updated': datetime.now().isoformat()
        }
        
        self._cache_data('medium', cache_key, overview)
        return overview
    
    def get_number_analysis(self, number: int, days: int = 365) -> Dict[str, Any]:
        """Análisis detallado de un número específico"""
        
        if not (0 <= number <= 99):
            return {'error': 'Número fuera de rango'}
        
        cache_key = f"number_{number}_{days}"
        cached = self._get_cached_data('recent', cache_key)
        if cached:
            return cached
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener todas las apariciones del número
        draws = self.db.get_draws_in_period(start_date, end_date)
        number_draws = [d for d in draws if d[1] == number]
        
        if not number_draws:
            return {
                'number': number,
                'status': 'No apareció en el período',
                'days_since_last': None,
                'analysis': 'Sin datos suficientes'
            }
        
        # Análisis de frecuencia
        total_draws = len(draws)
        appearances = len(number_draws)
        frequency = appearances / total_draws if total_draws > 0 else 0
        
        # Análisis de gaps
        dates = [datetime.strptime(str(d[0]), '%Y-%m-%d') for d in number_draws]
        dates.sort()
        
        gaps = []
        if len(dates) > 1:
            gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        
        # Última aparición
        last_appearance = dates[-1] if dates else None
        days_since_last = (datetime.now() - last_appearance).days if last_appearance else None
        
        # Estadísticas de gaps
        gap_stats = {}
        if gaps:
            gap_stats = {
                'average': round(statistics.mean(gaps), 1),
                'min': min(gaps),
                'max': max(gaps),
                'median': round(statistics.median(gaps), 1),
                'std_dev': round(statistics.stdev(gaps), 1) if len(gaps) > 1 else 0
            }
        
        # Predicción de próxima aparición
        prediction_status = 'normal'
        if gap_stats and days_since_last:
            expected_gap = gap_stats['average']
            if days_since_last > expected_gap * 1.5:
                prediction_status = 'overdue'
            elif days_since_last < expected_gap * 0.5:
                prediction_status = 'recent'
        
        # Análisis de tendencia (últimos vs anteriores)
        mid_point = len(dates) // 2
        if len(dates) >= 4:
            recent_dates = dates[mid_point:]
            older_dates = dates[:mid_point]
            
            recent_period = (recent_dates[-1] - recent_dates[0]).days if len(recent_dates) > 1 else days
            older_period = (older_dates[-1] - older_dates[0]).days if len(older_dates) > 1 else days
            
            recent_frequency = len(recent_dates) / max(recent_period, 1) * 30  # Por mes
            older_frequency = len(older_dates) / max(older_period, 1) * 30
            
            trend = 'increasing' if recent_frequency > older_frequency * 1.2 else \
                   'decreasing' if recent_frequency < older_frequency * 0.8 else 'stable'
        else:
            trend = 'insufficient_data'
        
        analysis = {
            'number': number,
            'period_days': days,
            'frequency_analysis': {
                'appearances': appearances,
                'total_draws': total_draws,
                'frequency_rate': round(frequency, 4),
                'frequency_percentage': round(frequency * 100, 2)
            },
            'timing_analysis': {
                'last_appearance': last_appearance.strftime('%Y-%m-%d') if last_appearance else None,
                'days_since_last': days_since_last,
                'gap_statistics': gap_stats,
                'prediction_status': prediction_status
            },
            'trend_analysis': {
                'trend_direction': trend,
                'data_quality': 'good' if len(dates) >= 4 else 'limited'
            },
            'all_appearances': [d.strftime('%Y-%m-%d') for d in dates[-10:]]  # Últimas 10
        }
        
        self._cache_data('recent', cache_key, analysis)
        return analysis
    
    def get_pattern_insights(self, days: int = 180) -> Dict[str, Any]:
        """Obtiene insights de patrones importantes"""
        
        cache_key = f"patterns_{days}"
        cached = self._get_cached_data('long', cache_key)
        if cached:
            return cached
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 50:
            return {'error': 'Datos insuficientes para análisis de patrones'}
        
        numbers = [draw[1] for draw in draws]
        
        # Análisis de dígitos
        units = [n % 10 for n in numbers]
        tens = [n // 10 for n in numbers]
        
        digit_patterns = {
            'units_distribution': dict(Counter(units).most_common()),
            'tens_distribution': dict(Counter(tens).most_common()),
            'favorite_units': Counter(units).most_common(3),
            'favorite_tens': Counter(tens).most_common(3)
        }
        
        # Análisis de rangos
        ranges = {
            '00-19': len([n for n in numbers if 0 <= n <= 19]),
            '20-39': len([n for n in numbers if 20 <= n <= 39]),
            '40-59': len([n for n in numbers if 40 <= n <= 59]),
            '60-79': len([n for n in numbers if 60 <= n <= 79]),
            '80-99': len([n for n in numbers if 80 <= n <= 99])
        }
        
        # Análisis de paridad
        even_count = len([n for n in numbers if n % 2 == 0])
        odd_count = len(numbers) - even_count
        
        parity_analysis = {
            'even_count': even_count,
            'odd_count': odd_count,
            'even_percentage': round((even_count / len(numbers)) * 100, 1),
            'odd_percentage': round((odd_count / len(numbers)) * 100, 1),
            'balance': 'balanced' if abs(even_count - odd_count) < len(numbers) * 0.1 else 'unbalanced'
        }
        
        # Números que no han aparecido
        all_numbers = set(range(0, 100))
        drawn_numbers = set(numbers)
        missing_numbers = list(all_numbers - drawn_numbers)
        
        insights = {
            'analysis_period': days,
            'total_draws': len(numbers),
            'digit_patterns': digit_patterns,
            'range_distribution': ranges,
            'parity_analysis': parity_analysis,
            'missing_numbers': {
                'count': len(missing_numbers),
                'numbers': sorted(missing_numbers),
                'percentage': round((len(missing_numbers) / 100) * 100, 1)
            },
            'summary': self._generate_pattern_summary(digit_patterns, ranges, parity_analysis, missing_numbers)
        }
        
        self._cache_data('long', cache_key, insights)
        return insights
    
    def get_performance_metrics(self, days: int = 90) -> Dict[str, Any]:
        """Métricas de rendimiento del sistema"""
        
        cache_key = f"performance_{days}"
        cached = self._get_cached_data('medium', cache_key)
        if cached:
            return cached
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        # Métricas básicas
        total_draws = len(draws)
        unique_dates = len(set(str(d[0]) for d in draws))
        unique_numbers = len(set(d[1] for d in draws))
        
        # Distribución temporal
        dates_count = Counter(str(d[0]) for d in draws)
        draws_per_day = list(dates_count.values())
        
        # Calidad de datos
        data_quality = {
            'completeness': round((unique_numbers / 100) * 100, 1),
            'consistency': 'good' if statistics.stdev(draws_per_day) < 1 else 'variable',
            'coverage_days': unique_dates,
            'total_days': days,
            'data_density': round((unique_dates / days) * 100, 1)
        }
        
        # Tendencias recientes
        recent_draws = [d for d in draws if 
                       datetime.strptime(str(d[0]), '%Y-%m-%d') >= 
                       datetime.now() - timedelta(days=7)]
        
        recent_activity = {
            'last_7_days': len(recent_draws),
            'daily_average': round(len(recent_draws) / 7, 1),
            'last_update': max(str(d[0]) for d in draws) if draws else None
        }
        
        metrics = {
            'period': {
                'days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'data_summary': {
                'total_draws': total_draws,
                'unique_numbers': unique_numbers,
                'unique_dates': unique_dates,
                'average_draws_per_day': round(total_draws / max(unique_dates, 1), 2)
            },
            'data_quality': data_quality,
            'recent_activity': recent_activity,
            'cache_status': {
                'recent_entries': len(self._cache['recent']),
                'medium_entries': len(self._cache['medium']),
                'long_entries': len(self._cache['long'])
            }
        }
        
        self._cache_data('medium', cache_key, metrics)
        return metrics
    
    def _calculate_range_distribution(self, draws: List) -> Dict[str, Any]:
        """Calcula distribución por rangos"""
        
        numbers = [draw[1] for draw in draws]
        total = len(numbers)
        
        ranges = {
            '00-19': len([n for n in numbers if 0 <= n <= 19]),
            '20-39': len([n for n in numbers if 20 <= n <= 39]),
            '40-59': len([n for n in numbers if 40 <= n <= 59]),
            '60-79': len([n for n in numbers if 60 <= n <= 79]),
            '80-99': len([n for n in numbers if 80 <= n <= 99])
        }
        
        # Agregar porcentajes
        for range_key in ranges:
            count = ranges[range_key]
            ranges[range_key] = {
                'count': count,
                'percentage': round((count / total) * 100, 1) if total > 0 else 0
            }
        
        return ranges
    
    def _get_latest_draws(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los últimos sorteos"""
        
        recent_date = datetime.now() - timedelta(days=30)
        draws = self.db.get_draws_in_period(recent_date, datetime.now())
        
        # Organizar por fecha
        by_date = defaultdict(list)
        for draw in draws:
            date_str = str(draw[0])
            number = draw[1]
            by_date[date_str].append(number)
        
        # Obtener las fechas más recientes
        sorted_dates = sorted(by_date.keys(), reverse=True)
        
        latest = []
        for date_str in sorted_dates[:limit]:
            numbers = sorted(by_date[date_str])
            latest.append({
                'date': date_str,
                'numbers': numbers,
                'count': len(numbers)
            })
        
        return latest
    
    def _generate_pattern_summary(self, digit_patterns, ranges, parity_analysis, missing_numbers):
        """Genera resumen de patrones"""
        
        summary = []
        
        # Dígitos favoritos
        fav_unit = digit_patterns['favorite_units'][0][0] if digit_patterns['favorite_units'] else None
        fav_ten = digit_patterns['favorite_tens'][0][0] if digit_patterns['favorite_tens'] else None
        
        if fav_unit is not None:
            summary.append(f"Dígito de unidad más frecuente: {fav_unit}")
        if fav_ten is not None:
            summary.append(f"Dígito de decena más frecuente: {fav_ten}")
        
        # Rango dominante
        max_range = max(ranges.items(), key=lambda x: x[1])
        summary.append(f"Rango más activo: {max_range[0]} ({max_range[1]} apariciones)")
        
        # Paridad
        if parity_analysis['balance'] == 'unbalanced':
            if parity_analysis['even_percentage'] > 55:
                summary.append("Predominio de números pares")
            else:
                summary.append("Predominio de números impares")
        
        # Números faltantes
        if len(missing_numbers) > 50:
            summary.append(f"Muchos números sin aparecer: {len(missing_numbers)}")
        elif len(missing_numbers) < 10:
            summary.append("Buena cobertura de números")
        
        return summary
    
    def _get_cached_data(self, cache_type: str, key: str) -> Optional[Any]:
        """Obtiene datos del cache si están válidos"""
        
        if cache_type not in self._cache:
            return None
        
        if key not in self._cache[cache_type]:
            return None
        
        entry = self._cache[cache_type][key]
        ttl = self._cache_ttl[cache_type]
        
        if (datetime.now() - entry['timestamp']).seconds < ttl:
            return entry['data']
        else:
            # Cache expirado
            del self._cache[cache_type][key]
            return None
    
    def _cache_data(self, cache_type: str, key: str, data: Any):
        """Guarda datos en cache"""
        
        self._cache[cache_type][key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def clear_cache(self, cache_type: str = None):
        """Limpia el cache"""
        
        if cache_type:
            if cache_type in self._cache:
                self._cache[cache_type].clear()
        else:
            for cache in self._cache.values():
                cache.clear()

def main():
    """Función de prueba"""
    print("🔧 MOTOR DE ANÁLISIS UNIFICADO")
    print("="*50)
    
    db = DatabaseManager()
    engine = UnifiedAnalyticsEngine(db)
    
    # Prueba de resumen
    overview = engine.get_dashboard_overview(days=180)
    print(f"📊 Resumen generado: {overview['general_stats']['total_draws']} sorteos")
    
    # Prueba de análisis de número
    number_analysis = engine.get_number_analysis(60, days=180)
    print(f"🔍 Análisis del número 60: {number_analysis.get('frequency_analysis', {}).get('appearances', 0)} apariciones")
    
    # Prueba de patrones
    patterns = engine.get_pattern_insights(days=180)
    print(f"🎯 Patrones encontrados: {len(patterns.get('summary', []))} insights")

if __name__ == "__main__":
    main()