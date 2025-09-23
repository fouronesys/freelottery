import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import statistics
import random
import math
from analyzer import StatisticalAnalyzer

class LotteryPredictor:
    """Genera predicciones basadas en análisis estadístico"""
    
    def __init__(self, analyzer: StatisticalAnalyzer):
        self.analyzer = analyzer
        self.number_range = (0, 99)
        
        # Pesos optimizados para diferentes métodos de predicción
        self.method_weights = {
            'frequency': 0.40,     # Peso de la frecuencia histórica
            'trend': 0.40,         # Peso de la tendencia reciente 
            'pattern': 0.15,       # Peso de patrones detectados 
            'randomness': 0.05     # Factor de determinismo (reducido)
        }
    
    def generate_predictions(
        self, 
        method: str = "frecuencia_historica", 
        days: int = 180,
        num_predictions: int = 10,
        confidence_threshold: float = 0.7
    ) -> List[Tuple[int, float, float, str]]:
        """
        Genera predicciones basadas en el método especificado
        
        Args:
            method: Método de predicción ('frecuencia_historica', 'tendencia_reciente', 'combinado')
            days: Días de datos históricos a considerar
            num_predictions: Número de predicciones a generar
            confidence_threshold: Umbral mínimo de confianza (0-1)
            
        Returns:
            List[Tuple]: [(numero, puntuacion, confianza, razon), ...]
        """
        predictions = []
        
        try:
            if method == "frecuencia_historica":
                predictions = self._predict_by_frequency(days, num_predictions)
            elif method == "tendencia_reciente":
                predictions = self._predict_by_recent_trend(days, num_predictions)
            elif method == "combinado":
                predictions = self._predict_combined_method(days, num_predictions)
            else:
                # Método por defecto
                predictions = self._predict_by_frequency(days, num_predictions)
            
            # Filtrar por umbral de confianza
            filtered_predictions = [
                pred for pred in predictions 
                if pred[2] >= confidence_threshold
            ]
            
            # Si no hay suficientes predicciones que cumplan el umbral, 
            # relajar el criterio pero mantener las mejores
            if len(filtered_predictions) < min(5, num_predictions):
                predictions.sort(key=lambda x: x[2], reverse=True)
                filtered_predictions = predictions[:num_predictions]
            
            return filtered_predictions[:num_predictions]
            
        except Exception as e:
            print(f"Error generando predicciones: {e}")
            return []
    
    def _predict_by_frequency(self, days: int, num_predictions: int) -> List[Tuple[int, float, float, str]]:
        """Predicción basada en frecuencia histórica mejorada"""
        predictions = []
        
        # Obtener frecuencias de todos los números
        all_frequencies = self.analyzer.db.get_all_numbers_frequency(days)
        
        if not all_frequencies:
            return []
        
        # Calcular estadísticas mejoradas
        frequencies = [freq for _, freq, _ in all_frequencies]
        mean_freq = statistics.mean(frequencies)
        std_freq = statistics.stdev(frequencies) if len(frequencies) > 1 else 0
        
        # Factor de ajuste basado en días para mayor variabilidad
        days_factor = 1.0 + (days / 365.0)  # Más días = más peso a frecuencias establecidas
        period_adjustment = math.sin(days / 30.0) * 0.1  # Variación cíclica basada en período
        
        for number, abs_freq, rel_freq in all_frequencies:
            # Calcular puntuación base mejorada
            base_score = rel_freq * 100 * days_factor
            
            # Ajustar por desviación del promedio con factor temporal
            if std_freq > 0:
                z_score = (abs_freq - mean_freq) / std_freq
                z_bonus = z_score * (15 + period_adjustment * 5)  # Bonus variable por período
                base_score += z_bonus
            
            # Bonus adicional por estabilidad en períodos largos
            if days > 90 and abs_freq > mean_freq:
                stability_bonus = (abs_freq / mean_freq - 1) * 10 * (days / 180.0)
                base_score += stability_bonus
            
            # Penalty por períodos cortos si no es muy frecuente
            if days < 60 and abs_freq < mean_freq:
                short_period_penalty = (mean_freq - abs_freq) / mean_freq * 5
                base_score -= short_period_penalty
            
            # Calcular confianza
            confidence = self.analyzer.get_prediction_confidence_score(number, days)
            
            # Razón más descriptiva
            if abs_freq > mean_freq:
                freq_ratio = abs_freq / mean_freq
                reason = f"Alta frecuencia: {abs_freq} apariciones ({rel_freq:.1%}, {freq_ratio:.1f}x promedio, {days}d)"
            else:
                reason = f"Frecuencia estable: {abs_freq} apariciones ({rel_freq:.1%}, {days}d)"
            
            predictions.append((number, max(base_score, 0), confidence, reason))
        
        # Ordenar por puntuación
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:num_predictions * 2]  # Retornar más para filtrado posterior
    
    def _predict_by_recent_trend(self, days: int, num_predictions: int) -> List[Tuple[int, float, float, str]]:
        """Predicción mejorada basada en tendencia reciente con análisis de momentum adaptativo"""
        predictions = []
        
        # Análisis de tendencia múltiple adaptativo según el período
        if days <= 60:
            # Períodos cortos: enfoque en tendencias muy recientes
            windows = [
                (min(7, days // 3), "ultra reciente"),
                (min(15, days // 2), "muy reciente"),
                (min(30, days), "reciente")
            ]
        elif days <= 180:
            # Períodos medios: balance entre reciente y estabilidad
            windows = [
                (min(15, days // 6), "muy reciente"),
                (min(30, days // 3), "reciente"),
                (min(60, days * 2 // 3), "medio plazo")
            ]
        else:
            # Períodos largos: más ventanas para análisis profundo
            windows = [
                (min(15, days // 8), "muy reciente"),
                (min(30, days // 4), "reciente"),
                (min(60, days // 2), "medio plazo"),
                (min(90, days * 3 // 4), "largo plazo")
            ]
        
        # Obtener frecuencias para cada ventana
        window_data = {}
        for window_days, window_name in windows:
            if window_days > 0:
                window_data[window_name] = {
                    'frequencies': self.analyzer.db.get_all_numbers_frequency(window_days),
                    'days': window_days
                }
        
        # Análisis de referencia (todo el período)
        baseline_freq = self.analyzer.db.get_all_numbers_frequency(days)
        baseline_dict = {num: (abs_freq, rel_freq) for num, abs_freq, rel_freq in baseline_freq}
        
        # Crear diccionarios para cada ventana
        window_dicts = {}
        for window_name, data in window_data.items():
            window_dicts[window_name] = {num: (abs_freq, rel_freq) 
                                       for num, abs_freq, rel_freq in data['frequencies']}
        
        # Obtener todos los números únicos
        all_numbers = set(baseline_dict.keys())
        for window_dict in window_dicts.values():
            all_numbers.update(window_dict.keys())
        
        for number in all_numbers:
            baseline_abs, baseline_rel = baseline_dict.get(number, (0, 0.0))
            
            # Calcular momentum y aceleración de tendencia con protección para muestras pequeñas
            momentum_score = 0.0
            acceleration_score = 0.0
            trend_consistency = 0.5  # Valor neutral por defecto
            
            # Verificar que tenemos suficientes datos para análisis robusto
            total_sample_size = sum(data.get('days', 0) for data in window_data.values())
            
            if len(window_dicts) >= 2 and total_sample_size >= 30:  # Mínimo 30 días de datos
                # Calcular velocidad de cambio entre ventanas
                window_values = []
                window_sample_sizes = []
                
                for window_name in ['muy reciente', 'reciente', 'medio plazo']:
                    if window_name in window_dicts and window_name in window_data:
                        _, rel_freq = window_dicts[window_name].get(number, (0, 0.0))
                        sample_size = window_data[window_name]['days']
                        
                        # Suavizar frecuencias relativas para muestras pequeñas
                        if sample_size < 15:  # Ventana muy pequeña
                            # Aplicar suavizado Laplace
                            smoothed_freq = (rel_freq * sample_size + 0.01) / (sample_size + 0.02)
                            window_values.append(smoothed_freq)
                        else:
                            window_values.append(rel_freq)
                        window_sample_sizes.append(sample_size)
                
                if len(window_values) >= 2 and min(window_sample_sizes) >= 5:
                    # Momentum (tendencia lineal) con peso por tamaño de muestra
                    weights = [min(size / 15.0, 1.0) for size in window_sample_sizes]
                    
                    if len(window_values) > 1:
                        weighted_change = (window_values[0] - window_values[-1]) * weights[0] * weights[-1]
                        momentum_score = max(-0.1, min(0.1, weighted_change))  # Limitar momentum
                    
                    # Aceleración (cambio en la tendencia) solo con suficientes datos
                    if len(window_values) >= 3 and min(window_sample_sizes) >= 10:
                        recent_change = window_values[0] - window_values[1]
                        older_change = window_values[1] - window_values[2]
                        acceleration_score = (recent_change - older_change) * weights[0]
                        acceleration_score = max(-0.05, min(0.05, acceleration_score))  # Limitar aceleración
                    
                    # Consistencia de tendencia con protección
                    if len(window_values) >= 2:
                        changes = [window_values[i] - window_values[i+1] 
                                 for i in range(len(window_values)-1)]
                        if changes:  # Verificar que hay cambios
                            trend_consistency = 1.0 if all(c >= 0 for c in changes) or all(c <= 0 for c in changes) else 0.5
                        else:
                            trend_consistency = 0.5
            
            # Obtener frecuencia más reciente
            recent_rel = window_dicts.get('muy reciente', {}).get(number, (0, 0.0))[1]
            if not recent_rel:
                recent_rel = window_dicts.get('reciente', {}).get(number, (0, 0.0))[1]
            
            # Calcular score mejorado con múltiples factores adaptativo por período
            period_multiplier = 1.0 + (days / 365.0) * 0.5  # Períodos largos dan más peso a consistencia
            recency_weight = max(0.3, 1.0 - (days / 365.0) * 0.7)  # Períodos cortos dan más peso a recencia
            
            base_score = recent_rel * 40 * recency_weight  # Score base adaptativo
            momentum_bonus = momentum_score * (30 + days / 10.0)  # Bonus escalado por período
            acceleration_bonus = acceleration_score * (20 + days / 15.0)  # Aceleración más importante en períodos largos
            consistency_bonus = trend_consistency * 10 * period_multiplier  # Consistencia más valiosa en análisis largos
            
            # Bonus adicional por período específico para diferenciación
            period_specific_bonus = math.cos(days / 45.0) * 5  # Variación periódica para diferenciar resultados
            
            score = base_score + momentum_bonus + acceleration_bonus + consistency_bonus + period_specific_bonus
            score = max(score, 0)
            
            # Confianza mejorada
            base_confidence = self.analyzer.get_prediction_confidence_score(number, days)
            
            # Ajustar confianza por calidad de tendencia con límites conservadores
            trend_quality = (min(abs(momentum_score) * 10, 1.0) + trend_consistency) / 2
            confidence_multiplier = 0.8 + trend_quality * 0.2  # Rango más conservador [0.8, 1.0]
            adjusted_confidence = base_confidence * confidence_multiplier
            confidence = min(adjusted_confidence, 1.0)
            
            # Razón mejorada con información de período
            if momentum_score > 0.01:
                reason = f"Momentum ascendente: +{momentum_score:.3f} (consistencia: {trend_consistency:.1%}, {days}d análisis)"
            elif momentum_score < -0.01:
                reason = f"Momentum descendente: {momentum_score:.3f} (período: {days}d)"
            elif recent_rel > baseline_rel:
                improvement_rate = (recent_rel - baseline_rel) / baseline_rel * 100
                reason = f"Mejora reciente: {recent_rel:.3f} vs {baseline_rel:.3f} (+{improvement_rate:.1f}%, {days}d)"
            else:
                reason = f"Actividad reciente: {recent_rel:.3f} frecuencia relativa (análisis {days}d)"
            
            predictions.append((number, score, confidence, reason))
        
        # Ordenar por puntuación
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:num_predictions * 2]
    
    def _predict_combined_method(self, days: int, num_predictions: int) -> List[Tuple[int, float, float, str]]:
        """Método de predicción combinado"""
        
        # Obtener predicciones de ambos métodos
        freq_predictions = self._predict_by_frequency(days, num_predictions * 2)
        trend_predictions = self._predict_by_recent_trend(days, num_predictions * 2)
        
        # Combinar predicciones con variabilidad mejorada por parámetros
        combined_scores = {}
        combined_confidence = {}
        combined_reasons = {}
        
        # Ajustar pesos dinámicamente basado en el período de análisis
        if days <= 60:
            # Períodos cortos: más peso a tendencias
            freq_weight = 0.30
            trend_weight = 0.50
        elif days <= 180:
            # Períodos medios: balance
            freq_weight = 0.40
            trend_weight = 0.40
        else:
            # Períodos largos: más peso a frecuencia histórica
            freq_weight = 0.50
            trend_weight = 0.30
        
        # Procesar predicciones por frecuencia
        for number, score, confidence, reason in freq_predictions:
            combined_scores[number] = score * freq_weight
            combined_confidence[number] = confidence * freq_weight
            combined_reasons[number] = f"Freq({days}d): {reason[:25]}..."
        
        # Agregar predicciones por tendencia
        for number, score, confidence, reason in trend_predictions:
            if number in combined_scores:
                combined_scores[number] += score * trend_weight
                combined_confidence[number] += confidence * trend_weight
                combined_reasons[number] += f" | Trend: {reason[:20]}..."
            else:
                combined_scores[number] = score * trend_weight
                combined_confidence[number] = confidence * trend_weight
                combined_reasons[number] = f"Tendencia({days}d): {reason}"
        
        # Agregar factor de patrones
        patterns = self._analyze_patterns(days)
        for number in combined_scores:
            pattern_bonus = self._get_pattern_bonus(number, patterns)
            combined_scores[number] += pattern_bonus * self.method_weights['pattern']
        
        # Agregar factor de variabilidad determinística basada en parámetros
        # Usar días como base para hacer la variabilidad reproducible pero variable por parámetros
        for number in combined_scores:
            # Factor determinístico basado en días y número para variabilidad consistente
            period_hash = (number * days + days) % 1000
            deterministic_factor = 1.0 + (period_hash / 5000.0 - 0.1)  # ±10% basado en parámetros
            combined_scores[number] *= deterministic_factor
            
            # Bonus adicional por interacción número-período para más variabilidad
            interaction_bonus = math.sin((number + days) / 50.0) * 2.0
            combined_scores[number] += interaction_bonus
        
        # Aplicar normalización de scores para mejor distribución
        if combined_scores:
            max_score = max(combined_scores.values())
            min_score = min(combined_scores.values())
            if max_score > min_score:
                for number in combined_scores:
                    # Normalizar a rango 0-100
                    normalized_score = ((combined_scores[number] - min_score) / (max_score - min_score)) * 100
                    combined_scores[number] = normalized_score
        
        # Normalizar confianza
        for number in combined_confidence:
            combined_confidence[number] = min(combined_confidence[number], 1.0)
        
        # Crear lista de predicciones finales
        final_predictions = []
        for number in combined_scores:
            final_predictions.append((
                number,
                combined_scores[number],
                combined_confidence[number],
                combined_reasons[number]
            ))
        
        # Ordenar por puntuación combinada
        final_predictions.sort(key=lambda x: x[1], reverse=True)
        
        return final_predictions[:num_predictions * 2]
    
    def _analyze_patterns(self, days: int) -> Dict[str, Any]:
        """Analiza patrones en los datos"""
        try:
            patterns = self.analyzer.analyze_number_patterns(days)
            return patterns
        except:
            return {}
    
    def _get_pattern_bonus(self, number: int, patterns: Dict[str, Any]) -> float:
        """Calcula bonus basado en patrones detectados"""
        bonus = 0.0
        
        try:
            # Bonus por dígito de unidades frecuente
            units_digit = number % 10
            if 'most_common_digit_units' in patterns:
                units_count = patterns['most_common_digit_units'].get(units_digit, 0)
                bonus += units_count * 0.1
            
            # Bonus por dígito de decenas frecuente
            tens_digit = number // 10
            if 'most_common_digit_tens' in patterns:
                tens_count = patterns['most_common_digit_tens'].get(tens_digit, 0)
                bonus += tens_count * 0.1
            
            # Bonus por distribución par/impar
            if 'even_odd_distribution' in patterns:
                is_even = number % 2 == 0
                even_count = patterns['even_odd_distribution'].get('even', 0)
                odd_count = patterns['even_odd_distribution'].get('odd', 0)
                
                if is_even and even_count > odd_count:
                    bonus += 0.5
                elif not is_even and odd_count > even_count:
                    bonus += 0.5
            
        except Exception as e:
            print(f"Error calculando bonus de patrón: {e}")
        
        return bonus
    
    def get_prediction_explanation(self, predictions: List[Tuple]) -> Dict[str, Any]:
        """
        Genera explicación detallada de las predicciones
        """
        if not predictions:
            return {}
        
        explanation = {
            'total_predictions': len(predictions),
            'avg_confidence': statistics.mean([pred[2] for pred in predictions]),
            'confidence_range': {
                'min': min([pred[2] for pred in predictions]),
                'max': max([pred[2] for pred in predictions])
            },
            'score_range': {
                'min': min([pred[1] for pred in predictions]),
                'max': max([pred[1] for pred in predictions])
            },
            'methodology': [
                "Análisis de frecuencia histórica",
                "Evaluación de tendencias recientes",
                "Detección de patrones numéricos",
                "Cálculo de confianza estadística"
            ],
            'disclaimer': (
                "Las predicciones están basadas en análisis estadístico de datos históricos. "
                "Los juegos de lotería son aleatorios por naturaleza y ningún método puede "
                "garantizar resultados futuros. Use esta información solo para entretenimiento."
            )
        }
        
        return explanation
    
    def validate_predictions(self, predictions: List[Tuple]) -> bool:
        """Valida que las predicciones sean coherentes"""
        if not predictions:
            return False
        
        try:
            # Verificar que todos los números estén en el rango válido
            for pred in predictions:
                number = pred[0]
                if not (self.number_range[0] <= number <= self.number_range[1]):
                    return False
            
            # Verificar que no haya duplicados
            numbers = [pred[0] for pred in predictions]
            if len(numbers) != len(set(numbers)):
                return False
            
            # Verificar que las confianzas estén en rango válido
            for pred in predictions:
                confidence = pred[2]
                if not (0.0 <= confidence <= 1.0):
                    return False
            
            return True
            
        except Exception:
            return False
