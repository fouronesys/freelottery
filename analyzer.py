import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter, defaultdict
import statistics
from database import DatabaseManager
import calendar
from scipy import stats

class StatisticalAnalyzer:
    """Realiza análisis estadísticos de los datos de lotería"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.number_range = (0, 99)  # Rango típico para Quiniela
        
    def calculate_all_frequencies(self, days: int = 180) -> List[Tuple[int, int, float, str]]:
        """
        Calcula frecuencias para todos los números
        
        Returns:
            List[Tuple]: [(numero, freq_absoluta, freq_relativa, clasificacion), ...]
        """
        frequency_data = self.db.get_all_numbers_frequency(days)
        
        if not frequency_data:
            return []
        
        # Calcular estadísticas para clasificación
        frequencies = [freq for _, freq, _ in frequency_data]
        if not frequencies:
            return []
        
        mean_freq = statistics.mean(frequencies)
        std_freq = statistics.stdev(frequencies) if len(frequencies) > 1 else 0
        
        # Umbrales mejorados para clasificación usando percentiles
        sorted_frequencies = sorted(frequencies)
        n = len(sorted_frequencies)
        
        # Usar percentiles para umbrales más precisos
        hot_threshold = sorted_frequencies[int(n * 0.75)] if n > 4 else mean_freq + (0.5 * std_freq)
        cold_threshold = sorted_frequencies[int(n * 0.25)] if n > 4 else mean_freq - (0.5 * std_freq)
        
        results = []
        for number, abs_freq, rel_freq in frequency_data:
            # Clasificar número
            if abs_freq >= hot_threshold:
                classification = "Caliente"
            elif abs_freq <= cold_threshold:
                classification = "Frío"
            else:
                classification = "Normal"
            
            results.append((number, abs_freq, rel_freq, classification))
        
        return results
    
    def get_hot_numbers(self, days: int = 180, limit: int = 10) -> List[Tuple[int, int, float]]:
        """
        Obtiene los números más frecuentes (calientes)
        
        Returns:
            List[Tuple]: [(numero, frecuencia, frecuencia_relativa), ...]
        """
        all_frequencies = self.db.get_all_numbers_frequency(days)
        
        # Ordenar por frecuencia descendente
        sorted_frequencies = sorted(all_frequencies, key=lambda x: x[1], reverse=True)
        
        return sorted_frequencies[:limit]
    
    def get_cold_numbers(self, days: int = 180, limit: int = 10) -> List[Tuple[int, int, float]]:
        """
        Obtiene los números menos frecuentes (fríos)
        
        Returns:
            List[Tuple]: [(numero, frecuencia, frecuencia_relativa), ...]
        """
        all_frequencies = self.db.get_all_numbers_frequency(days)
        
        # Obtener todos los números posibles
        all_possible_numbers = set(range(self.number_range[0], self.number_range[1] + 1))
        appearing_numbers = {num for num, _, _ in all_frequencies}
        missing_numbers = all_possible_numbers - appearing_numbers
        
        # Agregar números que no han aparecido
        extended_frequencies = list(all_frequencies)
        for missing_num in missing_numbers:
            extended_frequencies.append((missing_num, 0, 0.0))
        
        # Ordenar por frecuencia ascendente
        sorted_frequencies = sorted(extended_frequencies, key=lambda x: x[1])
        
        return sorted_frequencies[:limit]
    
    def analyze_by_ranges(self, days: int = 180) -> List[Tuple[str, float, int]]:
        """
        Analiza frecuencias por rangos de números
        
        Returns:
            List[Tuple]: [(rango, frecuencia_promedio, count_numeros), ...]
        """
        all_frequencies = self.db.get_all_numbers_frequency(days)
        
        if not all_frequencies:
            return []
        
        # Definir rangos
        ranges = [
            ("00-09", 0, 9),
            ("10-19", 10, 19),
            ("20-29", 20, 29),
            ("30-39", 30, 39),
            ("40-49", 40, 49),
            ("50-59", 50, 59),
            ("60-69", 60, 69),
            ("70-79", 70, 79),
            ("80-89", 80, 89),
            ("90-99", 90, 99)
        ]
        
        range_analysis = []
        
        for range_name, min_num, max_num in ranges:
            range_frequencies = [
                freq for num, freq, _ in all_frequencies 
                if min_num <= num <= max_num
            ]
            
            if range_frequencies:
                avg_frequency = statistics.mean(range_frequencies)
                num_count = len(range_frequencies)
            else:
                avg_frequency = 0.0
                num_count = 0
            
            range_analysis.append((range_name, avg_frequency, num_count))
        
        return range_analysis
    
    def get_temporal_trends(self, days: int = 180) -> List[Dict[str, Any]]:
        """
        Analiza tendencias temporales en las frecuencias
        
        Returns:
            List[Dict]: [{'Fecha': date, 'Frecuencia_Promedio': float}, ...]
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener datos por períodos semanales
        temporal_data = []
        current_date = start_date
        
        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)
            
            # Obtener sorteos de la semana
            week_draws = self.db.get_numbers_by_date_range(current_date, week_end)
            
            if week_draws:
                # Calcular frecuencia promedio de la semana
                numbers_count = Counter([num for _, num in week_draws])
                avg_frequency = statistics.mean(numbers_count.values()) if numbers_count else 0
            else:
                avg_frequency = 0
            
            temporal_data.append({
                'Fecha': current_date.strftime('%Y-%m-%d'),
                'Frecuencia_Promedio': avg_frequency
            })
            
            current_date = week_end
        
        return temporal_data
    
    def calculate_correlations(self, days: int = 180) -> List[Tuple[int, int, float, str]]:
        """
        Calcula correlaciones mejoradas entre números usando análisis estadístico avanzado
        
        Returns:
            List[Tuple]: [(num1, num2, correlacion, significancia), ...]
        """
        # Obtener datos del período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
        
        if len(draws_data) < 20:  # Necesitamos datos suficientes para análisis robusto
            return []
        
        # Organizar datos por fecha
        dates_numbers = {}
        for date_str, number in draws_data:
            if date_str not in dates_numbers:
                dates_numbers[date_str] = []
            dates_numbers[date_str].append(number)
        
        correlations = []
        unique_numbers = sorted(set(num for _, num in draws_data))
        
        # Calcular estadísticas base para normalizar
        total_dates = len(dates_numbers)
        
        for i, num1 in enumerate(unique_numbers):
            for num2 in unique_numbers[i+1:]:
                # Contar apariciones individuales y conjuntas
                num1_appearances = sum(1 for date_numbers in dates_numbers.values() if num1 in date_numbers)
                num2_appearances = sum(1 for date_numbers in dates_numbers.values() if num2 in date_numbers)
                joint_appearances = sum(1 for date_numbers in dates_numbers.values() 
                                      if num1 in date_numbers and num2 in date_numbers)
                
                # Calcular probabilidades
                p_num1 = num1_appearances / total_dates
                p_num2 = num2_appearances / total_dates
                p_joint = joint_appearances / total_dates
                
                # Probabilidad esperada bajo independencia
                p_expected = p_num1 * p_num2
                
                # Calcular correlación usando información mutua normalizada
                if p_num1 > 0 and p_num2 > 0 and p_expected > 0:
                    # Correlación normalizada (similar a coeficiente de Pearson para datos binarios)
                    max_p = max(p_num1, p_num2)
                    if max_p < 1.0:  # Evitar división por cero
                        correlation = (p_joint - p_expected) / (max_p * (1 - max_p))
                        correlation = max(-1.0, min(1.0, correlation))  # Limitar a [-1, 1]
                    else:
                        correlation = 0.0
                else:
                    correlation = 0.0
                
                # Calcular significancia estadística mejorada
                # Usar test de chi-cuadrado simplificado
                expected_joint = p_expected * total_dates
                
                if expected_joint > 5 and joint_appearances >= 5:  # Criterio para validez del test
                    chi_square = ((joint_appearances - expected_joint) ** 2) / expected_joint
                    
                    if chi_square > 7.88:  # p < 0.005
                        significance = "Muy Alta"
                    elif chi_square > 3.84:  # p < 0.05
                        significance = "Alta"
                    elif chi_square > 2.71:  # p < 0.10
                        significance = "Media"
                    else:
                        significance = "Baja"
                else:
                    # Para muestras pequeñas, usar criterio basado en frecuencia
                    if joint_appearances >= max(3, total_dates * 0.05):
                        significance = "Media"
                    else:
                        significance = "Baja"
                
                # Solo incluir correlaciones con cierta relevancia
                if abs(correlation) > 0.01 or joint_appearances >= 3:
                    correlations.append((num1, num2, correlation, significance))
        
        # Ordenar por valor absoluto de correlación descendente
        correlations.sort(key=lambda x: abs(x[2]), reverse=True)
        
        return correlations[:25]  # Top 25 correlaciones más significativas
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de rendimiento
        """
        try:
            unique_numbers = self.db.get_unique_numbers()
            total_draws = self.db.get_total_draws()
            
            # Calcular estadísticas básicas
            stats = {
                'unique_numbers': len(unique_numbers),
                'total_draws': total_draws,
                'avg_draws_per_day': 0,
                'most_frequent_number': None,
                'least_frequent_number': None,
                'coverage_period_days': self.db.get_data_coverage_days()
            }
            
            if stats['coverage_period_days'] > 0:
                stats['avg_draws_per_day'] = total_draws / stats['coverage_period_days']
            
            # Obtener números más y menos frecuentes
            all_frequencies = self.db.get_all_numbers_frequency(days=365)  # Último año
            
            if all_frequencies:
                # Más frecuente
                most_frequent = max(all_frequencies, key=lambda x: x[1])
                stats['most_frequent_number'] = f"{most_frequent[0]} ({most_frequent[1]} veces)"
                
                # Menos frecuente (excluyendo los que nunca aparecieron)
                appearing_frequencies = [f for f in all_frequencies if f[1] > 0]
                if appearing_frequencies:
                    least_frequent = min(appearing_frequencies, key=lambda x: x[1])
                    stats['least_frequent_number'] = f"{least_frequent[0]} ({least_frequent[1]} veces)"
            
            return stats
            
        except Exception as e:
            print(f"Error calculando estadísticas: {e}")
            return {
                'unique_numbers': 0,
                'total_draws': 0,
                'avg_draws_per_day': 0,
                'most_frequent_number': 'N/A',
                'least_frequent_number': 'N/A',
                'coverage_period_days': 0
            }
    
    def analyze_number_patterns(self, days: int = 180) -> Dict[str, Any]:
        """
        Analiza patrones en los números ganadores
        """
        all_frequencies = self.db.get_all_numbers_frequency(days)
        
        if not all_frequencies:
            return {}
        
        numbers = [num for num, _, _ in all_frequencies]
        frequencies = [freq for _, freq, _ in all_frequencies]
        
        patterns = {
            'total_unique_numbers': len(numbers),
            'most_common_digit_units': Counter([num % 10 for num in numbers]),
            'most_common_digit_tens': Counter([num // 10 for num in numbers]),
            'even_odd_distribution': {
                'even': len([n for n in numbers if n % 2 == 0]),
                'odd': len([n for n in numbers if n % 2 == 1])
            },
            'frequency_distribution': {
                'mean': statistics.mean(frequencies) if frequencies else 0,
                'median': statistics.median(frequencies) if frequencies else 0,
                'std_dev': statistics.stdev(frequencies) if len(frequencies) > 1 else 0
            }
        }
        
        return patterns
    
    def get_prediction_confidence_score(self, number: int, days: int = 180) -> float:
        """
        Calcula un puntaje de confianza mejorado para la predicción de un número
        Implementa múltiples factores estadísticos para mayor precisión
        
        Returns:
            float: Puntaje de confianza entre 0 y 1
        """
        try:
            # Obtener frecuencia del número
            abs_freq, rel_freq = self.db.get_number_frequency(number, days)
            
            # Obtener estadísticas generales
            all_frequencies = self.db.get_all_numbers_frequency(days)
            
            if not all_frequencies:
                return 0.0
            
            frequencies = [freq for _, freq, _ in all_frequencies]
            if len(frequencies) < 2:
                return rel_freq
            
            mean_freq = statistics.mean(frequencies)
            std_freq = statistics.stdev(frequencies)
            max_freq = max(frequencies)
            min_freq = min(frequencies)
            
            # Factor 1: Z-score normalizado (qué tan alejado está del promedio)
            z_score = (abs_freq - mean_freq) / std_freq if std_freq > 0 else 0
            z_factor = 0.5 + (z_score / 6.0)  # Normalizar z-score típico (-3,3) a (0,1)
            z_factor = max(0.0, min(1.0, z_factor))
            
            # Factor 2: Posición relativa en el rango
            if max_freq > min_freq:
                range_factor = (abs_freq - min_freq) / (max_freq - min_freq)
            else:
                range_factor = 0.5
            
            # Factor 3: Consistencia histórica (usando análisis de tendencia)
            consistency_factor = self._calculate_consistency_factor(number, days)
            
            # Factor 4: Frecuencia relativa suavizada
            smoothed_rel_freq = rel_freq + 0.01 / (days / 180)  # Pequeño ajuste por período
            
            # Factor 5: Factor de regularidad (qué tan regular es la aparición)
            regularity_factor = self._calculate_regularity_factor(number, days)
            
            # Combinar factores con pesos optimizados
            confidence_score = (
                smoothed_rel_freq * 0.25 +      # Frecuencia relativa
                z_factor * 0.20 +               # Posición estadística
                range_factor * 0.20 +           # Posición en rango
                consistency_factor * 0.20 +     # Consistencia temporal
                regularity_factor * 0.15        # Regularidad de aparición
            )
            
            # Normalizar y aplicar límites
            confidence_score = min(max(confidence_score, 0.0), 1.0)
            
            return confidence_score
            
        except Exception as e:
            print(f"Error calculando confianza para número {number}: {e}")
            return 0.0
    
    def _calculate_consistency_factor(self, number: int, days: int) -> float:
        """
        Calcula qué tan consistente ha sido la frecuencia del número a lo largo del tiempo
        """
        try:
            # Dividir el período en cuartos para analizar consistencia
            quarter_days = days // 4
            quarter_frequencies = []
            
            for i in range(4):
                start_days = (3 - i) * quarter_days
                end_days = (4 - i) * quarter_days if i < 3 else days
                
                if start_days < days:
                    _, rel_freq = self.db.get_number_frequency(number, end_days - start_days)
                    quarter_frequencies.append(rel_freq)
            
            if len(quarter_frequencies) < 2:
                return 0.5
            
            # Calcular coeficiente de variación (menor variación = mayor consistencia)
            mean_freq = statistics.mean(quarter_frequencies)
            if mean_freq == 0:
                return 0.0
            
            std_freq = statistics.stdev(quarter_frequencies)
            cv = std_freq / mean_freq  # Coeficiente de variación
            
            # Convertir a factor de consistencia (menor CV = mayor consistencia)
            consistency = max(0.0, 1.0 - min(cv, 2.0) / 2.0)
            
            return consistency
            
        except Exception:
            return 0.5
    
    def _calculate_regularity_factor(self, number: int, days: int) -> float:
        """
        Calcula qué tan regular es la aparición del número (espaciado entre apariciones)
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener todas las fechas donde apareció el número
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            number_dates = [datetime.strptime(date_str, '%Y-%m-%d') 
                          for date_str, num in draws_data if num == number]
            
            if len(number_dates) < 2:
                return 0.3  # Valor neutral para números con pocas apariciones
            
            # Calcular intervalos entre apariciones
            number_dates.sort()
            intervals = [(number_dates[i+1] - number_dates[i]).days 
                        for i in range(len(number_dates) - 1)]
            
            if not intervals:
                return 0.3
            
            # Analizar regularidad de intervalos
            mean_interval = statistics.mean(intervals)
            if len(intervals) > 1:
                std_interval = statistics.stdev(intervals)
                cv_interval = std_interval / mean_interval if mean_interval > 0 else 2.0
            else:
                cv_interval = 0.0
            
            # Convertir a factor de regularidad
            regularity = max(0.0, 1.0 - min(cv_interval, 3.0) / 3.0)
            
            return regularity
            
        except Exception:
            return 0.3
    
    def analyze_day_of_week_patterns(self, days: int = 180) -> Dict[str, Any]:
        """
        Analiza patrones por día de la semana
        
        Returns:
            Dict con análisis por día de la semana
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            
            if not draws_data:
                return {}
            
            # Agrupar por día de la semana
            day_patterns = {}
            day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            for date_str, number in draws_data:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_of_week = day_names[date_obj.weekday()]
                
                if day_of_week not in day_patterns:
                    day_patterns[day_of_week] = []
                day_patterns[day_of_week].append(number)
            
            # Calcular estadísticas por día
            day_stats = {}
            for day, numbers in day_patterns.items():
                if numbers:
                    day_stats[day] = {
                        'total_draws': len(numbers),
                        'unique_numbers': len(set(numbers)),
                        'most_frequent': max(set(numbers), key=numbers.count),
                        'avg_number': statistics.mean(numbers),
                        'frequency_distribution': Counter(numbers)
                    }
            
            return day_stats
            
        except Exception as e:
            print(f"Error analizando patrones de día de la semana: {e}")
            return {}
    
    def analyze_day_of_month_patterns(self, days: int = 365) -> Dict[str, Any]:
        """
        Analiza patrones por día del mes (1-31)
        
        Returns:
            Dict con análisis por día del mes, recomendaciones específicas
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            
            if not draws_data:
                return {}
            
            # Agrupar por día del mes
            month_day_patterns = {}
            
            for date_str, number in draws_data:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_of_month = date_obj.day
                
                if day_of_month not in month_day_patterns:
                    month_day_patterns[day_of_month] = []
                month_day_patterns[day_of_month].append(number)
            
            # Calcular estadísticas por día del mes
            day_stats = {}
            best_numbers_by_day = {}
            
            for day, numbers in month_day_patterns.items():
                if numbers:
                    frequency_counter = Counter(numbers)
                    # Top 5 números más frecuentes para este día
                    top_numbers = frequency_counter.most_common(5)
                    
                    day_stats[day] = {
                        'total_draws': len(numbers),
                        'unique_numbers': len(set(numbers)),
                        'most_frequent_number': top_numbers[0][0] if top_numbers else None,
                        'most_frequent_count': top_numbers[0][1] if top_numbers else 0,
                        'avg_number': round(statistics.mean(numbers), 1),
                        'top_5_numbers': [(num, count) for num, count in top_numbers],
                        'frequency_distribution': frequency_counter,
                        'std_deviation': round(statistics.stdev(numbers), 2) if len(numbers) > 1 else 0
                    }
                    
                    # Recomendaciones específicas para este día
                    best_numbers_by_day[day] = [num for num, count in top_numbers]
            
            # Obtener día actual para recomendación inmediata
            today = datetime.now().day
            today_recommendation = best_numbers_by_day.get(today, [])
            
            return {
                'day_statistics': day_stats,
                'best_numbers_by_day': best_numbers_by_day,
                'today_recommendation': {
                    'day': today,
                    'recommended_numbers': today_recommendation[:3],  # Top 3 para hoy
                    'confidence_level': 'Alta' if len(today_recommendation) >= 3 else 'Media'
                },
                'analysis_summary': {
                    'days_analyzed': days,
                    'total_days_with_data': len(day_stats),
                    'most_active_day': max(day_stats.items(), key=lambda x: x[1]['total_draws'])[0] if day_stats else None,
                    'least_active_day': min(day_stats.items(), key=lambda x: x[1]['total_draws'])[0] if day_stats else None
                }
            }
            
        except Exception as e:
            print(f"Error analizando patrones de día del mes: {e}")
            return {}
    
    def get_best_play_recommendation(self, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Genera la mejor recomendación de jugada basada en todos los análisis disponibles
        
        Args:
            target_date: Fecha objetivo (por defecto hoy)
            
        Returns:
            Dict con recomendación completa de la mejor jugada del día
        """
        try:
            if target_date is None:
                target_date = datetime.now()
            
            day_of_month = target_date.day
            day_of_week = target_date.strftime('%A')
            
            # Análisis de frecuencias (últimos 180 días)
            hot_numbers = self.get_hot_numbers(days=180, limit=10)
            cold_numbers = self.get_cold_numbers(days=180, limit=10)
            
            # Análisis por día del mes
            month_patterns = self.analyze_day_of_month_patterns(days=365)
            day_specific_numbers = month_patterns.get('best_numbers_by_day', {}).get(day_of_month, [])
            
            # Análisis por día de la semana
            week_patterns = self.analyze_day_of_week_patterns(days=180)
            day_names_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            weekday_index = target_date.weekday()
            day_name_spanish = day_names_spanish[weekday_index]
            week_specific_data = week_patterns.get(day_name_spanish, {})
            
            # Análisis de tendencias recientes (últimos 30 días)
            recent_trends = self.get_temporal_trends(days=30)
            
            # Sistema de puntuación integrado
            number_scores = {}
            
            # Inicializar puntuaciones para todos los números
            for num in range(100):
                number_scores[num] = {
                    'total_score': 0,
                    'frequency_score': 0,
                    'day_month_score': 0,
                    'day_week_score': 0,
                    'trend_score': 0,
                    'reasons': []
                }
            
            # 1. Puntuación por frecuencia histórica (30% del peso)
            hot_nums_dict = {num: freq for num, freq, _ in hot_numbers}
            max_hot_freq = max(hot_nums_dict.values()) if hot_nums_dict else 1
            
            for num, freq, _ in hot_numbers:
                score = (freq / max_hot_freq) * 30
                number_scores[num]['frequency_score'] = score
                number_scores[num]['total_score'] += score
                number_scores[num]['reasons'].append(f"Número caliente (freq: {freq})")
            
            # 2. Puntuación por día del mes (25% del peso)
            for i, num in enumerate(day_specific_numbers[:10]):
                score = (10 - i) * 2.5  # Decreciente del 25 al 2.5
                number_scores[num]['day_month_score'] = score
                number_scores[num]['total_score'] += score
                number_scores[num]['reasons'].append(f"Favorito para día {day_of_month} del mes")
            
            # 3. Puntuación por día de la semana (20% del peso)
            if week_specific_data and 'most_frequent' in week_specific_data:
                most_freq_weekday = week_specific_data['most_frequent']
                number_scores[most_freq_weekday]['day_week_score'] = 20
                number_scores[most_freq_weekday]['total_score'] += 20
                number_scores[most_freq_weekday]['reasons'].append(f"Más frecuente los {day_name_spanish}")
            
            # 4. Puntuación por tendencias recientes (25% del peso)
            recent_avg = statistics.mean([trend['Frecuencia_Promedio'] for trend in recent_trends]) if recent_trends else 0
            if recent_avg > 0:
                recent_hot = self.get_hot_numbers(days=30, limit=5)
                for i, (num, freq, _) in enumerate(recent_hot):
                    score = (5 - i) * 5  # 25, 20, 15, 10, 5 puntos
                    number_scores[num]['trend_score'] = score
                    number_scores[num]['total_score'] += score
                    number_scores[num]['reasons'].append("Tendencia reciente positiva")
            
            # Ordenar por puntuación total
            sorted_recommendations = sorted(
                [(num, data) for num, data in number_scores.items()],
                key=lambda x: x[1]['total_score'],
                reverse=True
            )
            
            # Top recomendaciones
            top_recommendations = sorted_recommendations[:10]
            
            # Tipos de jugadas recomendadas
            best_number = top_recommendations[0][0]
            second_best = top_recommendations[1][0] if len(top_recommendations) > 1 else None
            third_best = top_recommendations[2][0] if len(top_recommendations) > 2 else None
            
            play_recommendations = {
                'quiniela_simple': {
                    'number': best_number,
                    'confidence': 'Alta' if top_recommendations[0][1]['total_score'] > 50 else 'Media',
                    'expected_payout': '60-75 pesos por peso'
                },
                'pale_combinations': [],
                'tripleta_suggestion': [best_number, second_best, third_best] if all([best_number, second_best, third_best]) else None
            }
            
            # Combinaciones Palé recomendadas
            if second_best:
                play_recommendations['pale_combinations'] = [
                    {'numbers': [best_number, second_best], 'type': '1ro y 2do', 'payout': '1,000 pesos'},
                ]
            
            return {
                'target_date': target_date.strftime('%Y-%m-%d'),
                'day_of_month': day_of_month,
                'day_of_week': day_name_spanish,
                'best_single_number': best_number,
                'top_recommendations': [(num, data['total_score'], data['reasons']) for num, data in top_recommendations[:5]],
                'play_strategies': play_recommendations,
                'analysis_confidence': 'Alta' if top_recommendations[0][1]['total_score'] > 60 else 'Media',
                'methodology': 'Análisis integrado: frecuencia histórica (30%) + patrones día del mes (25%) + día de la semana (20%) + tendencias recientes (25%)'
            }
            
        except Exception as e:
            print(f"Error generando recomendación de jugada: {e}")
            return {}
    
    def analyze_monthly_patterns(self, days: int = 365) -> Dict[str, Any]:
        """
        Analiza patrones por mes del año
        
        Returns:
            Dict con análisis mensual
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            
            if not draws_data:
                return {}
            
            # Agrupar por mes
            month_patterns = {}
            
            # Nombres de meses en español
            spanish_months = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            for date_str, number in draws_data:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                month_name = spanish_months[date_obj.month]
                
                if month_name not in month_patterns:
                    month_patterns[month_name] = []
                month_patterns[month_name].append(number)
            
            # Calcular estadísticas por mes
            month_stats = {}
            for month, numbers in month_patterns.items():
                if numbers:
                    month_stats[month] = {
                        'total_draws': len(numbers),
                        'unique_numbers': len(set(numbers)),
                        'most_frequent': max(set(numbers), key=numbers.count),
                        'avg_number': statistics.mean(numbers),
                        'frequency_distribution': Counter(numbers)
                    }
            
            return month_stats
            
        except Exception as e:
            print(f"Error analizando patrones mensuales: {e}")
            return {}
    
    def calculate_ewma_trends(self, days: int = 90, alpha: float = 0.3) -> Dict[int, float]:
        """
        Calcula tendencias EWMA (Exponentially Weighted Moving Average) para números
        
        Args:
            days: Período de análisis
            alpha: Factor de suavizado (0 < alpha <= 1)
            
        Returns:
            Dict[int, float]: Número -> tendencia EWMA
        """
        try:
            import pandas as pd
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Crear rango completo de fechas
            date_range = pd.date_range(start=start_date.date(), end=end_date.date(), freq='D')
            
            # Obtener datos organizados por fecha
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            
            if not draws_data:
                return {}
            
            # Organizar por fecha
            daily_counts = {}
            for date_str, number in draws_data:
                if date_str not in daily_counts:
                    daily_counts[date_str] = Counter()
                daily_counts[date_str][number] += 1
            
            # Obtener todos los números únicos
            unique_numbers = self.db.get_unique_numbers()
            
            # Calcular EWMA para cada número
            ewma_trends = {}
            
            for number in unique_numbers:
                # Crear serie temporal completa con ceros
                series = []
                for date in date_range:
                    date_str = date.strftime('%Y-%m-%d')
                    count = daily_counts.get(date_str, {}).get(number, 0)
                    series.append(count)
                
                # Calcular EWMA solo si hay alguna aparición
                if series and sum(series) > 0:
                    ewma = series[0]
                    for value in series[1:]:
                        ewma = alpha * value + (1 - alpha) * ewma
                    
                    ewma_trends[number] = ewma
            
            return ewma_trends
            
        except Exception as e:
            print(f"Error calculando tendencias EWMA: {e}")
            return {}
    
    def detect_frequency_changes(self, days: int = 90, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detecta cambios significativos en la frecuencia de números
        
        Args:
            days: Período de análisis
            threshold: Umbral en desviaciones estándar
            
        Returns:
            Lista de cambios detectados
        """
        try:
            # Dividir el período en dos mitades
            half_period = days // 2
            
            # Obtener frecuencias de ambos períodos
            recent_frequencies = self.db.get_all_numbers_frequency(half_period)
            previous_frequencies = self.db.get_all_numbers_frequency(days)
            
            # Crear diccionarios para comparación
            recent_dict = {num: freq for num, freq, _ in recent_frequencies}
            previous_dict = {num: freq for num, freq, _ in previous_frequencies}
            
            changes_detected = []
            all_numbers = set(recent_dict.keys()) | set(previous_dict.keys())
            
            for number in all_numbers:
                recent_freq = recent_dict.get(number, 0)
                previous_freq = previous_dict.get(number, 0)
                
                # Calcular cambio relativo
                if previous_freq > 0:
                    change_ratio = (recent_freq - previous_freq) / previous_freq
                    
                    # Calcular significancia estadística (simplificada)
                    if abs(change_ratio) > threshold / 10:  # Ajuste empírico
                        change_type = "Incremento" if change_ratio > 0 else "Disminución"
                        
                        changes_detected.append({
                            'number': number,
                            'change_type': change_type,
                            'change_ratio': change_ratio,
                            'recent_frequency': recent_freq,
                            'previous_frequency': previous_freq,
                            'significance': abs(change_ratio)
                        })
            
            # Ordenar por significancia
            changes_detected.sort(key=lambda x: x['significance'], reverse=True)
            
            return changes_detected[:20]  # Top 20 cambios
            
        except Exception as e:
            print(f"Error detectando cambios de frecuencia: {e}")
            return []
    
    def analyze_number_cooccurrence(self, days: int = 365) -> Dict[int, Dict[int, int]]:
        """
        Analiza co-ocurrencia de números en el mismo sorteo
        
        Args:
            days: Período de análisis
            
        Returns:
            Dict[int, Dict[int, int]]: Número -> {Número compañero: frecuencia}
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws = self.db.get_draws_by_date_range(start_date, end_date)
            
            if not draws:
                return {}
            
            cooccurrence = defaultdict(lambda: defaultdict(int))
            
            # Agrupar números por sorteo
            draws_by_id = defaultdict(list)
            for draw_id, number, date in draws:
                draws_by_id[draw_id].append(number)
            
            # Calcular co-ocurrencias
            for draw_id, numbers in draws_by_id.items():
                unique_numbers = list(set(numbers))  # Eliminar duplicados si los hay
                
                # Para cada par de números en el mismo sorteo
                for i, num1 in enumerate(unique_numbers):
                    for num2 in unique_numbers[i+1:]:
                        cooccurrence[num1][num2] += 1
                        cooccurrence[num2][num1] += 1  # Simétrico
            
            return dict(cooccurrence)
            
        except Exception as e:
            print(f"Error analizando co-ocurrencia: {e}")
            return {}
    
    def analyze_digit_transitions(self, days: int = 365) -> Dict[str, Dict[str, int]]:
        """
        Analiza transiciones entre dígitos de números consecutivos
        
        Args:
            days: Período de análisis
            
        Returns:
            Dict[str, Dict[str, int]]: Dígito -> {Siguiente dígito: frecuencia}
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws = self.db.get_draws_by_date_range(start_date, end_date)
            
            if not draws:
                return {}
            
            transitions = defaultdict(lambda: defaultdict(int))
            
            # Ordenar por fecha para analizar secuencias temporales
            draws_sorted = sorted(draws, key=lambda x: x[2])  # Ordenar por fecha
            
            previous_number = None
            for draw_id, number, date in draws_sorted:
                if previous_number is not None:
                    # Analizar transición dígito a dígito
                    prev_str = str(previous_number).zfill(2)
                    curr_str = str(number).zfill(2)
                    
                    # Transiciones de cada posición
                    for i in range(min(len(prev_str), len(curr_str))):
                        prev_digit = prev_str[i]
                        curr_digit = curr_str[i]
                        transitions[f"pos_{i}_{prev_digit}"][curr_digit] += 1
                
                previous_number = number
            
            return dict(transitions)
            
        except Exception as e:
            print(f"Error analizando transiciones de dígitos: {e}")
            return {}
    
    def find_combination_patterns(self, min_frequency: int = 3, days: int = 365) -> List[Dict[str, Any]]:
        """
        Encuentra patrones en combinaciones de números
        
        Args:
            min_frequency: Frecuencia mínima para considerar un patrón
            days: Período de análisis
            
        Returns:
            List[Dict[str, Any]]: Lista de patrones encontrados
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws = self.db.get_draws_by_date_range(start_date, end_date)
            
            if not draws:
                return []
            
            # Agrupar números por sorteo
            draws_by_id = defaultdict(list)
            for draw_id, number, date in draws:
                draws_by_id[draw_id].append(number)
            
            patterns = []
            
            # Analizar patrones de suma, paridad, rangos
            for draw_id, numbers in draws_by_id.items():
                unique_numbers = list(set(numbers))
                
                if len(unique_numbers) >= 2:
                    # Patrón de suma
                    total_sum = sum(unique_numbers)
                    
                    # Patrón de paridad
                    even_count = sum(1 for n in unique_numbers if n % 2 == 0)
                    odd_count = len(unique_numbers) - even_count
                    
                    # Patrón de rango
                    min_num = min(unique_numbers)
                    max_num = max(unique_numbers)
                    range_span = max_num - min_num
                    
                    patterns.append({
                        'draw_id': draw_id,
                        'numbers': sorted(unique_numbers),
                        'sum': total_sum,
                        'even_count': even_count,
                        'odd_count': odd_count,
                        'range_span': range_span,
                        'min_num': min_num,
                        'max_num': max_num
                    })
            
            # Encontrar patrones frecuentes
            frequent_patterns = []
            
            # Analizar rangos de suma frecuentes
            sum_ranges = defaultdict(list)
            for pattern in patterns:
                sum_range = (pattern['sum'] // 50) * 50  # Agrupar en rangos de 50
                sum_ranges[sum_range].append(pattern)
            
            for sum_range, pattern_list in sum_ranges.items():
                if len(pattern_list) >= min_frequency:
                    frequent_patterns.append({
                        'type': 'suma_rango',
                        'pattern': f"{sum_range}-{sum_range + 49}",
                        'frequency': len(pattern_list),
                        'examples': [p['numbers'] for p in pattern_list[:3]]
                    })
            
            # Analizar patrones de paridad
            parity_patterns = defaultdict(list)
            for pattern in patterns:
                parity_key = f"{pattern['even_count']}E-{pattern['odd_count']}O"
                parity_patterns[parity_key].append(pattern)
            
            for parity_key, pattern_list in parity_patterns.items():
                if len(pattern_list) >= min_frequency:
                    frequent_patterns.append({
                        'type': 'paridad',
                        'pattern': parity_key,
                        'frequency': len(pattern_list),
                        'examples': [p['numbers'] for p in pattern_list[:3]]
                    })
            
            return sorted(frequent_patterns, key=lambda x: x['frequency'], reverse=True)
            
        except Exception as e:
            print(f"Error encontrando patrones de combinación: {e}")
            return []

    # ================== ANÁLISIS ESTADÍSTICOS COMPLEJOS ==================
    
    def analyze_autocorrelation(self, days: int = 365) -> Dict[str, Any]:
        """
        Análisis de autocorrelación mejorado usando series temporales agregadas
        Detecta patrones no aleatorios de forma estadísticamente válida
        """
        try:
            from scipy import stats
            from statsmodels.stats.diagnostic import acorr_ljungbox
            from statsmodels.stats.stattools import durbin_watson
            from statsmodels.tsa.stattools import acf, pacf
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener datos y crear serie temporal agregada por día
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            if not draws_data:
                return {}
            
            # Agrupar por día y calcular estadísticas diarias
            daily_stats = defaultdict(list)
            for date_str, number in draws_data:
                daily_stats[date_str].append(number)
            
            # Crear serie temporal de promedios diarios (más estable estadísticamente)
            daily_series = []
            dates = sorted(daily_stats.keys())
            
            for date_str in dates:
                if daily_stats[date_str]:
                    daily_avg = np.mean(daily_stats[date_str])
                    daily_series.append(daily_avg)
            
            if len(daily_series) < 15:
                return {'error': 'Serie temporal muy corta para análisis válido'}
            
            # Convertir a array numpy
            time_series = np.array(daily_series)
            
            # Test de estacionariedad simple (diferencias)
            diff_series = np.diff(time_series)
            
            # 1. Test Durbin-Watson en las diferencias (más apropiado)
            dw_stat = durbin_watson(diff_series)
            
            # 2. Análisis ACF/PACF usando statsmodels (método correcto)
            try:
                acf_values = acf(diff_series, nlags=min(10, len(diff_series)//4), fft=False)
                pacf_values = pacf(diff_series, nlags=min(10, len(diff_series)//4))
                
                autocorr_lags = []
                for i in range(1, len(acf_values)):
                    autocorr_lags.append({
                        'lag': i,
                        'acf': float(acf_values[i]),
                        'pacf': float(pacf_values[i]) if i < len(pacf_values) else 0
                    })
            except:
                autocorr_lags = []
            
            # 3. Test Ljung-Box en diferencias
            try:
                ljung_result = acorr_ljungbox(diff_series, lags=min(10, len(diff_series)//3), return_df=True)
                ljung_p = float(ljung_result.iloc[0]['lb_pvalue'])
            except:
                ljung_p = 1.0
            
            # Interpretación mejorada
            randomness_assessment = "Serie Aleatoria"
            confidence_level = "Alta"
            
            if ljung_p < 0.05:
                randomness_assessment = "Patrones Detectados (Serie No Aleatoria)"
                confidence_level = "Alta"
            elif ljung_p < 0.1:
                randomness_assessment = "Posibles Patrones Débiles"
                confidence_level = "Media"
            
            # Análisis de significancia estadística
            significant_lags = []
            for lag_info in autocorr_lags:
                # Umbral aproximado para significancia en ACF
                threshold = 1.96 / np.sqrt(len(time_series))
                if abs(lag_info['acf']) > threshold:
                    significant_lags.append(lag_info['lag'])
            
            return {
                'series_length': len(time_series),
                'durbin_watson_stat': float(dw_stat),
                'ljung_box_p_value': ljung_p,
                'autocorr_lags': autocorr_lags,
                'randomness_assessment': randomness_assessment,
                'confidence_level': confidence_level,
                'significant_lags': significant_lags,
                'methodology_note': 'Análisis realizado en diferencias de promedios diarios para mayor validez estadística'
            }
            
        except Exception as e:
            print(f"Error en análisis de autocorrelación: {e}")
            return {'error': str(e)}
    
    def analyze_time_series_patterns(self, days: int = 365) -> Dict[str, Any]:
        """
        Análisis de series temporales usando ARIMA y detección de estacionalidad
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.seasonal import seasonal_decompose
            from scipy.fft import fft, fftfreq
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            if not draws_data:
                return {}
            
            # Crear serie temporal de frecuencias diarias
            daily_stats = defaultdict(list)
            for date_str, number in draws_data:
                daily_stats[date_str].append(number)
            
            # Promedio diario de números
            daily_averages = []
            dates = []
            for date_str in sorted(daily_stats.keys()):
                if daily_stats[date_str]:
                    daily_averages.append(np.mean(daily_stats[date_str]))
                    dates.append(date_str)
            
            if len(daily_averages) < 15:
                return {}
            
            # 1. Análisis ARIMA simple
            try:
                model = ARIMA(daily_averages, order=(1,1,1))
                fitted_model = model.fit()
                forecast = fitted_model.forecast(steps=7)
                arima_summary = {
                    'aic': float(fitted_model.aic),
                    'forecast_next_7_days': [float(x) for x in forecast],
                    'model_params': fitted_model.params.to_dict()
                }
            except:
                arima_summary = {'error': 'No se pudo ajustar modelo ARIMA'}
            
            # 2. Análisis de frecuencias (FFT para detectar ciclos)
            if len(daily_averages) >= 20:
                fft_values = fft(daily_averages)
                frequencies = fftfreq(len(daily_averages))
                
                # Encontrar frecuencias dominantes
                magnitude = np.abs(np.array(fft_values))
                dominant_freqs = []
                for i in range(1, len(magnitude)//2):
                    if magnitude[i] > np.mean(magnitude) + 2*np.std(magnitude):
                        period = 1/abs(frequencies[i]) if frequencies[i] != 0 else 0
                        if period > 2:  # Ciclos de más de 2 días
                            dominant_freqs.append({
                                'period_days': float(period),
                                'strength': float(magnitude[i])
                            })
                
                cycle_analysis = sorted(dominant_freqs, key=lambda x: x['strength'], reverse=True)[:5]
            else:
                cycle_analysis = []
            
            # 3. Detección de tendencias
            if len(daily_averages) >= 10:
                x = np.arange(len(daily_averages))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, daily_averages)
                
                trend_analysis = {
                    'slope': float(slope),
                    'r_squared': float(r_value**2),
                    'p_value': float(p_value),
                    'trend_direction': 'Creciente' if slope > 0 else 'Decreciente',
                    'trend_strength': 'Fuerte' if abs(r_value) > 0.5 else 'Débil'
                }
            else:
                trend_analysis = {}
            
            return {
                'arima_analysis': arima_summary,
                'cycle_detection': cycle_analysis,
                'trend_analysis': trend_analysis,
                'data_points': len(daily_averages),
                'date_range': {'start': dates[0], 'end': dates[-1]}
            }
            
        except Exception as e:
            print(f"Error en análisis de series temporales: {e}")
            return {}
    
    def test_randomness_quality(self, days: int = 365) -> Dict[str, Any]:
        """
        Tests estadísticos de calidad de aleatoriedad
        Chi-square test, runs test, y análisis de distribución
        """
        try:
            from scipy.stats import chisquare, kstest, shapiro
            from scipy import stats
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
            if not draws_data:
                return {}
            
            numbers_sequence = [number for _, number in draws_data]
            
            if len(numbers_sequence) < 30:
                return {}
            
            # 1. Chi-square test para uniformidad
            observed_freq = Counter(numbers_sequence)
            all_numbers = list(range(self.number_range[0], self.number_range[1] + 1))
            observed_counts = [observed_freq.get(num, 0) for num in all_numbers]
            
            expected_count = len(numbers_sequence) / len(all_numbers)
            expected_counts = [expected_count] * len(all_numbers)
            
            chi2_stat, chi2_p = chisquare(observed_counts, expected_counts)
            
            # 2. Kolmogorov-Smirnov test para distribución uniforme
            ks_stat, ks_p = kstest(numbers_sequence, 'uniform', 
                                   args=(self.number_range[0], self.number_range[1] - self.number_range[0] + 1))
            
            # 3. Runs test (test de rachas)
            median_val = np.median(numbers_sequence)
            runs = []
            current_run = []
            
            for num in numbers_sequence:
                if not current_run:
                    current_run = [num >= median_val]
                elif (num >= median_val) == current_run[-1]:
                    current_run.append(num >= median_val)
                else:
                    runs.append(len(current_run))
                    current_run = [num >= median_val]
            
            if current_run:
                runs.append(len(current_run))
            
            # Estadísticas de runs
            n_runs = len(runs)
            n_total = len(numbers_sequence)
            n_positive = sum(1 for x in numbers_sequence if x >= median_val)
            n_negative = n_total - n_positive
            
            if n_positive > 0 and n_negative > 0:
                expected_runs = (2 * n_positive * n_negative) / n_total + 1
                variance_runs = (2 * n_positive * n_negative * (2 * n_positive * n_negative - n_total)) / (n_total**2 * (n_total - 1))
                
                if variance_runs > 0:
                    z_runs = (n_runs - expected_runs) / np.sqrt(variance_runs)
                    runs_p = 2 * (1 - stats.norm.cdf(abs(z_runs)))
                else:
                    z_runs, runs_p = 0, 1
            else:
                expected_runs = 0.0
                z_runs, runs_p = 0, 1
            
            # 4. Análisis de gaps (intervalos entre apariciones)
            number_gaps = defaultdict(list)
            last_positions = {}
            
            for i, num in enumerate(numbers_sequence):
                if num in last_positions:
                    gap = i - last_positions[num]
                    number_gaps[num].append(gap)
                last_positions[num] = i
            
            avg_gaps = {}
            for num, gaps in number_gaps.items():
                if gaps:
                    avg_gaps[num] = np.mean(gaps)
            
            # Evaluación general de aleatoriedad
            randomness_score = 0
            if chi2_p > 0.05: randomness_score += 25
            if ks_p > 0.05: randomness_score += 25  
            if runs_p > 0.05: randomness_score += 25
            if 0.4 < len(set(numbers_sequence))/len(all_numbers) < 0.8: randomness_score += 25
            
            quality_assessment = "Excelente" if randomness_score >= 75 else \
                               "Buena" if randomness_score >= 50 else \
                               "Regular" if randomness_score >= 25 else "Pobre"
            
            return {
                'chi_square': {'statistic': float(chi2_stat), 'p_value': float(chi2_p)},
                'kolmogorov_smirnov': {'statistic': float(ks_stat), 'p_value': float(ks_p)},
                'runs_test': {'n_runs': n_runs, 'expected_runs': float(expected_runs), 'p_value': float(runs_p)},
                'randomness_score': randomness_score,
                'quality_assessment': quality_assessment,
                'unique_numbers_ratio': len(set(numbers_sequence))/len(all_numbers),
                'sequence_stats': {
                    'mean': float(np.mean(numbers_sequence)),
                    'std': float(np.std(numbers_sequence)),
                    'median': float(np.median(numbers_sequence))
                }
            }
            
        except Exception as e:
            print(f"Error en test de aleatoriedad: {e}")
            return {}
    
    def analyze_number_clustering(self, days: int = 365) -> Dict[str, Any]:
        """
        Análisis de clustering para detectar grupos de números relacionados
        """
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            # Obtener datos de frecuencia y co-ocurrencia
            frequency_data = self.calculate_all_frequencies(days)
            cooccurrence_data = self.analyze_number_cooccurrence(days)
            
            if not frequency_data or not cooccurrence_data:
                return {}
            
            # Preparar matriz de características
            features = []
            numbers = []
            
            for num, freq, rel_freq, classification in frequency_data:
                # Características: frecuencia relativa, número de co-ocurrencias, promedio de co-ocurrencias
                cooc_count = len(cooccurrence_data.get(num, {}))
                cooc_avg = np.mean(list(cooccurrence_data.get(num, {0: 0}).values())) if cooc_count > 0 else 0
                
                features.append([rel_freq, cooc_count, cooc_avg, num])
                numbers.append(num)
            
            if len(features) < 6:  # Necesitamos al menos 6 números para clustering
                return {}
            
            # Normalizar características
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # K-means clustering con diferentes números de clusters
            cluster_results = {}
            
            for n_clusters in [3, 4, 5, 6]:
                if len(features) >= n_clusters:
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
                    cluster_labels = kmeans.fit_predict(features_scaled)
                    
                    # Organizar clusters
                    clusters = defaultdict(list)
                    for i, label in enumerate(cluster_labels):
                        clusters[label].append({
                            'number': numbers[i],
                            'frequency': features[i][0],
                            'cooccurrence_count': features[i][1]
                        })
                    
                    # Evaluar calidad del clustering
                    inertia = kmeans.inertia_
                    cluster_results[n_clusters] = {
                        'clusters': dict(clusters),
                        'inertia': float(inertia) if inertia is not None else 0.0,
                        'centroids': kmeans.cluster_centers_.tolist()
                    }
            
            # Seleccionar mejor número de clusters (método del codo simplificado)
            if cluster_results:
                inertias = [(k, v['inertia']) for k, v in cluster_results.items()]
                best_k = min(inertias, key=lambda x: x[1])[0]
                
                # Interpretar clusters del mejor modelo
                best_clusters = cluster_results[best_k]['clusters']
                cluster_interpretations = {}
                
                for cluster_id, cluster_nums in best_clusters.items():
                    avg_freq = np.mean([n['frequency'] for n in cluster_nums])
                    cluster_size = len(cluster_nums)
                    
                    if avg_freq > 0.02:
                        cluster_type = "Números Calientes"
                    elif avg_freq < 0.005:
                        cluster_type = "Números Fríos"
                    else:
                        cluster_type = "Números Normales"
                    
                    cluster_interpretations[cluster_id] = {
                        'type': cluster_type,
                        'size': cluster_size,
                        'avg_frequency': float(avg_freq),
                        'numbers': [n['number'] for n in cluster_nums]
                    }
                
                return {
                    'best_k_clusters': best_k,
                    'cluster_analysis': cluster_interpretations,
                    'all_k_results': cluster_results,
                    'total_numbers_analyzed': len(numbers)
                }
            
            return {}
            
        except Exception as e:
            print(f"Error en análisis de clustering: {e}")
            return {}
    
    def create_predictive_formula(self, days: int = 365) -> Dict[str, Any]:
        """
        Crea fórmulas predictivas basadas en todos los análisis estadísticos complejos
        """
        try:
            # Ejecutar todos los análisis complejos
            autocorr_results = self.analyze_autocorrelation(days)
            timeseries_results = self.analyze_time_series_patterns(days)
            randomness_results = self.test_randomness_quality(days)
            clustering_results = self.analyze_number_clustering(days)
            
            # Obtener datos base
            frequency_data = self.calculate_all_frequencies(days)
            ewma_trends = self.calculate_ewma_trends(days)
            
            if not frequency_data:
                return {}
            
            # Crear sistema de puntuación integrado
            formula_scores = {}
            
            for num, freq, rel_freq, classification in frequency_data:
                score = 0
                confidence_factors = []
                
                # 1. Factor de frecuencia base (peso: 30%)
                freq_score = rel_freq * 30
                score += freq_score
                confidence_factors.append(f"Frecuencia: {rel_freq:.3f}")
                
                # 2. Factor de tendencia EWMA (peso: 25%)
                if ewma_trends and num in ewma_trends:
                    ewma_score = min(ewma_trends[num] * 25, 25)  # Cap at 25
                    score += ewma_score
                    confidence_factors.append(f"Tendencia EWMA: {ewma_trends[num]:.3f}")
                
                # 3. Factor de clustering (peso: 20%)
                if clustering_results and 'cluster_analysis' in clustering_results:
                    for cluster_id, cluster_info in clustering_results['cluster_analysis'].items():
                        if num in cluster_info['numbers']:
                            if cluster_info['type'] == "Números Calientes":
                                cluster_score = 20
                            elif cluster_info['type'] == "Números Normales":
                                cluster_score = 10
                            else:  # Números Fríos
                                cluster_score = 5
                            score += cluster_score
                            confidence_factors.append(f"Cluster: {cluster_info['type']}")
                            break
                
                # 4. Factor de autocorrelación (peso: 15%)
                if autocorr_results and 'significant_lags' in autocorr_results:
                    if autocorr_results['randomness_assessment'] != "Aleatorio":
                        autocorr_score = 15 * (1 - autocorr_results['durbin_watson_stat']/4)
                        score += max(0, autocorr_score)
                        confidence_factors.append("Patrón no-aleatorio detectado")
                
                # 5. Factor de calidad de aleatoriedad (peso: 10%)
                if randomness_results and 'randomness_score' in randomness_results:
                    # Paradójicamente, menor aleatoriedad = mayor predictibilidad
                    randomness_score = (100 - randomness_results['randomness_score']) * 0.1
                    score += randomness_score
                    confidence_factors.append(f"Predictibilidad: {randomness_score:.1f}")
                
                formula_scores[num] = {
                    'total_score': score,
                    'confidence_factors': confidence_factors,
                    'classification': classification
                }
            
            # Ordenar por puntuación y crear recomendaciones
            sorted_scores = sorted(formula_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
            
            # Crear fórmula matemática textual
            formula_description = """
            FÓRMULA PREDICTIVA INTEGRADA:
            
            Puntuación_Total = (Frecuencia_Relativa × 30) + 
                             (Tendencia_EWMA × 25) + 
                             (Factor_Clustering × 20) + 
                             (Factor_Autocorrelación × 15) + 
                             (Factor_Predictibilidad × 10)
            
            Donde:
            - Frecuencia_Relativa: Probabilidad histórica de aparición
            - Tendencia_EWMA: Promedio móvil exponencial (detecta tendencias recientes)
            - Factor_Clustering: Tipo de cluster (Caliente=20, Normal=10, Frío=5)
            - Factor_Autocorrelación: Basado en test Durbin-Watson
            - Factor_Predictibilidad: Inverso de la calidad de aleatoriedad
            """
            
            # Estadísticas del modelo
            model_stats = {
                'total_numbers_evaluated': len(formula_scores),
                'autocorrelation_detected': autocorr_results.get('randomness_assessment', 'No disponible'),
                'randomness_quality': randomness_results.get('quality_assessment', 'No disponible'),
                'clustering_method': f"K-means con {clustering_results.get('best_k_clusters', 'N/A')} clusters",
                'time_series_trend': timeseries_results.get('trend_analysis', {}).get('trend_direction', 'No disponible')
            }
            
            return {
                'formula_description': formula_description,
                'top_predictions': sorted_scores[:15],
                'model_statistics': model_stats,
                'component_analyses': {
                    'autocorrelation': autocorr_results,
                    'time_series': timeseries_results,
                    'randomness': randomness_results,
                    'clustering': clustering_results
                },
                'formula_version': '1.0 - Análisis Estadístico Integrado'
            }
            
        except Exception as e:
            print(f"Error creando fórmula predictiva: {e}")
            return {}
