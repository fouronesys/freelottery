import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter
import statistics
from database import DatabaseManager
import calendar

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
        
        # Umbrales para clasificación
        hot_threshold = mean_freq + (0.5 * std_freq)
        cold_threshold = mean_freq - (0.5 * std_freq)
        
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
        Calcula correlaciones entre números
        
        Returns:
            List[Tuple]: [(num1, num2, correlacion, significancia), ...]
        """
        # Obtener datos del período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws_data = self.db.get_numbers_by_date_range(start_date, end_date)
        
        if len(draws_data) < 10:  # Necesitamos datos suficientes
            return []
        
        # Organizar datos por fecha
        dates_numbers = {}
        for date_str, number in draws_data:
            if date_str not in dates_numbers:
                dates_numbers[date_str] = []
            dates_numbers[date_str].append(number)
        
        # Calcular correlaciones simples (apariciones conjuntas)
        correlations = []
        unique_numbers = sorted(set(num for _, num in draws_data))
        
        for i, num1 in enumerate(unique_numbers):
            for num2 in unique_numbers[i+1:]:
                # Contar apariciones conjuntas
                joint_appearances = 0
                total_dates = len(dates_numbers)
                
                for date_numbers in dates_numbers.values():
                    if num1 in date_numbers and num2 in date_numbers:
                        joint_appearances += 1
                
                # Calcular correlación simple
                correlation = joint_appearances / total_dates if total_dates > 0 else 0
                
                # Determinar significancia
                if correlation > 0.1:
                    significance = "Alta"
                elif correlation > 0.05:
                    significance = "Media"
                else:
                    significance = "Baja"
                
                correlations.append((num1, num2, correlation, significance))
        
        # Ordenar por correlación descendente
        correlations.sort(key=lambda x: x[2], reverse=True)
        
        return correlations[:20]  # Top 20 correlaciones
    
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
        Calcula un puntaje de confianza para la predicción de un número
        
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
            mean_freq = statistics.mean(frequencies)
            max_freq = max(frequencies)
            
            # Calcular puntaje base en frecuencia relativa
            base_score = rel_freq
            
            # Ajustar por frecuencia en relación al promedio
            if mean_freq > 0:
                frequency_factor = abs_freq / mean_freq
                frequency_factor = min(frequency_factor, 2.0)  # Limitar factor
            else:
                frequency_factor = 0.0
            
            # Calcular puntaje final (combinación de factores)
            confidence_score = (base_score * 0.6) + (frequency_factor * 0.4 / 2.0)
            
            # Normalizar entre 0 y 1
            confidence_score = min(max(confidence_score, 0.0), 1.0)
            
            return confidence_score
            
        except Exception as e:
            print(f"Error calculando confianza para número {number}: {e}")
            return 0.0
    
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
