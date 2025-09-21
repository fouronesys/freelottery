import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import statistics
import random
from analyzer import StatisticalAnalyzer

class LotteryPredictor:
    """Genera predicciones basadas en análisis estadístico"""
    
    def __init__(self, analyzer: StatisticalAnalyzer):
        self.analyzer = analyzer
        self.number_range = (0, 99)
        
        # Pesos para diferentes métodos de predicción
        self.method_weights = {
            'frequency': 0.4,      # Peso de la frecuencia histórica
            'trend': 0.3,          # Peso de la tendencia reciente
            'pattern': 0.2,        # Peso de patrones detectados
            'randomness': 0.1      # Factor de aleatoriedad
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
        """Predicción basada en frecuencia histórica"""
        predictions = []
        
        # Obtener frecuencias de todos los números
        all_frequencies = self.analyzer.db.get_all_numbers_frequency(days)
        
        if not all_frequencies:
            return []
        
        # Calcular estadísticas
        frequencies = [freq for _, freq, _ in all_frequencies]
        mean_freq = statistics.mean(frequencies)
        std_freq = statistics.stdev(frequencies) if len(frequencies) > 1 else 0
        
        for number, abs_freq, rel_freq in all_frequencies:
            # Calcular puntuación basada en frecuencia
            score = rel_freq * 100  # Convertir a porcentaje base
            
            # Ajustar por desviación del promedio
            if std_freq > 0:
                z_score = (abs_freq - mean_freq) / std_freq
                score += z_score * 10  # Bonus por estar sobre el promedio
            
            # Calcular confianza
            confidence = self.analyzer.get_prediction_confidence_score(number, days)
            
            # Razón de la predicción
            if abs_freq > mean_freq:
                reason = f"Número caliente: {abs_freq} apariciones ({rel_freq:.1%})"
            else:
                reason = f"Frecuencia: {abs_freq} apariciones ({rel_freq:.1%})"
            
            predictions.append((number, max(score, 0), confidence, reason))
        
        # Ordenar por puntuación
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:num_predictions * 2]  # Retornar más para filtrado posterior
    
    def _predict_by_recent_trend(self, days: int, num_predictions: int) -> List[Tuple[int, float, float, str]]:
        """Predicción basada en tendencia reciente"""
        predictions = []
        
        # Analizar tendencia reciente (últimos 30 días vs. período anterior)
        recent_days = min(30, days // 2)
        previous_days = days - recent_days
        
        recent_freq = self.analyzer.db.get_all_numbers_frequency(recent_days)
        previous_freq = self.analyzer.db.get_all_numbers_frequency(previous_days)
        
        # Crear diccionarios para comparación
        recent_dict = {num: (abs_freq, rel_freq) for num, abs_freq, rel_freq in recent_freq}
        previous_dict = {num: (abs_freq, rel_freq) for num, abs_freq, rel_freq in previous_freq}
        
        # Obtener todos los números únicos
        all_numbers = set(recent_dict.keys()) | set(previous_dict.keys())
        
        for number in all_numbers:
            recent_abs, recent_rel = recent_dict.get(number, (0, 0.0))
            previous_abs, previous_rel = previous_dict.get(number, (0, 0.0))
            
            # Calcular tendencia
            if previous_rel > 0:
                trend_factor = (recent_rel - previous_rel) / previous_rel
            else:
                trend_factor = 1.0 if recent_rel > 0 else 0.0
            
            # Puntuación basada en tendencia positiva
            score = (recent_rel * 50) + (trend_factor * 25)
            score = max(score, 0)
            
            # Confianza basada en datos recientes
            confidence = self.analyzer.get_prediction_confidence_score(number, recent_days)
            
            # Ajustar confianza por tendencia
            if trend_factor > 0:
                confidence = min(confidence * 1.2, 1.0)
            
            # Razón
            if trend_factor > 0.2:
                reason = f"Tendencia ascendente: {trend_factor:.1%} de incremento"
            elif recent_abs > 0:
                reason = f"Actividad reciente: {recent_abs} apariciones"
            else:
                reason = f"Patrón emergente detectado"
            
            predictions.append((number, score, confidence, reason))
        
        # Ordenar por puntuación
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:num_predictions * 2]
    
    def _predict_combined_method(self, days: int, num_predictions: int) -> List[Tuple[int, float, float, str]]:
        """Método de predicción combinado"""
        
        # Obtener predicciones de ambos métodos
        freq_predictions = self._predict_by_frequency(days, num_predictions * 2)
        trend_predictions = self._predict_by_recent_trend(days, num_predictions * 2)
        
        # Combinar predicciones
        combined_scores = {}
        combined_confidence = {}
        combined_reasons = {}
        
        # Procesar predicciones por frecuencia
        for number, score, confidence, reason in freq_predictions:
            combined_scores[number] = score * self.method_weights['frequency']
            combined_confidence[number] = confidence * self.method_weights['frequency']
            combined_reasons[number] = f"Frecuencia: {reason[:30]}..."
        
        # Agregar predicciones por tendencia
        for number, score, confidence, reason in trend_predictions:
            if number in combined_scores:
                combined_scores[number] += score * self.method_weights['trend']
                combined_confidence[number] += confidence * self.method_weights['trend']
                combined_reasons[number] += f" | Tendencia: {reason[:20]}..."
            else:
                combined_scores[number] = score * self.method_weights['trend']
                combined_confidence[number] = confidence * self.method_weights['trend']
                combined_reasons[number] = f"Tendencia: {reason}"
        
        # Agregar factor de patrones
        patterns = self._analyze_patterns(days)
        for number in combined_scores:
            pattern_bonus = self._get_pattern_bonus(number, patterns)
            combined_scores[number] += pattern_bonus * self.method_weights['pattern']
        
        # Agregar factor de aleatoriedad controlada
        for number in combined_scores:
            randomness_factor = random.uniform(0.8, 1.2)
            combined_scores[number] *= randomness_factor
        
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
