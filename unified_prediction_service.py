#!/usr/bin/env python3
"""
Servicio de Predicciones Unificado - Quiniela Loteka
Combina toda la funcionalidad de predicción en un solo servicio configurable
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import statistics
import math
from collections import defaultdict, Counter
from database import DatabaseManager
from analyzer import StatisticalAnalyzer

class UnifiedPredictionService:
    """Servicio unificado de predicciones con múltiples estrategias"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = StatisticalAnalyzer(db_manager)
        self.number_range = (0, 99)
        
        # Estrategias de predicción disponibles
        self.strategies = {
            'balanced': {
                'name': 'Equilibrado',
                'description': 'Balance entre frecuencia, tendencias y patrones',
                'weights': {
                    'frequency': 0.30,
                    'gaps': 0.25,
                    'trends': 0.25,
                    'patterns': 0.20
                }
            },
            'conservative': {
                'name': 'Conservador',
                'description': 'Basado principalmente en frecuencia histórica',
                'weights': {
                    'frequency': 0.50,
                    'gaps': 0.20,
                    'trends': 0.20,
                    'patterns': 0.10
                }
            },
            'aggressive': {
                'name': 'Agresivo',
                'description': 'Enfocado en tendencias recientes y gaps',
                'weights': {
                    'frequency': 0.15,
                    'gaps': 0.40,
                    'trends': 0.35,
                    'patterns': 0.10
                }
            }
        }
        
        # Cache para optimizar rendimiento
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos
    
    def generate_predictions(
        self,
        strategy: str = 'balanced',
        days: int = 1825,  # ~5 años por defecto
        num_predictions: int = 10,
        confidence_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Genera predicciones usando la estrategia especificada
        
        Returns:
            Dict con predicciones, estadísticas y metadatos
        """
        
        if strategy not in self.strategies:
            strategy = 'balanced'
        
        strategy_config = self.strategies[strategy]
        weights = strategy_config['weights']
        
        # Cache key
        cache_key = f"{strategy}_{days}_{num_predictions}_{confidence_threshold}"
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        print(f"🎯 Generando predicciones con estrategia '{strategy_config['name']}'...")
        
        # Calcular puntuaciones por componente
        component_scores = {}
        
        # 1. Análisis de frecuencia
        if weights['frequency'] > 0:
            freq_scores = self._calculate_frequency_component(days)
            component_scores['frequency'] = freq_scores
        
        # 2. Análisis de gaps (intervalos)
        if weights['gaps'] > 0:
            gap_scores = self._calculate_gap_component(days)
            component_scores['gaps'] = gap_scores
        
        # 3. Análisis de tendencias
        if weights['trends'] > 0:
            trend_scores = self._calculate_trend_component(days)
            component_scores['trends'] = trend_scores
        
        # 4. Análisis de patrones
        if weights['patterns'] > 0:
            pattern_scores = self._calculate_pattern_component(days)
            component_scores['patterns'] = pattern_scores
        
        # Combinar puntuaciones
        final_scores = self._combine_component_scores(component_scores, weights)
        
        # Filtrar y ordenar predicciones
        predictions = self._finalize_predictions(
            final_scores, num_predictions, confidence_threshold
        )
        
        # Generar resultado completo
        result = {
            'predictions': predictions,
            'strategy': strategy_config,
            'statistics': self._calculate_statistics(predictions),
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period_days': days,
                'total_candidates': len(final_scores),
                'confidence_threshold': confidence_threshold
            },
            'component_contributions': self._analyze_component_contributions(
                component_scores, weights, predictions
            )
        }
        
        # Guardar en cache
        self._cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        return result
    
    def _calculate_frequency_component(self, days: int) -> Dict[int, Dict[str, float]]:
        """Calcula puntuaciones basadas en frecuencia histórica"""
        
        all_frequencies = self.db.get_all_numbers_frequency(days)
        if not all_frequencies:
            return {}
        
        scores = {}
        frequencies = [freq for _, freq, _ in all_frequencies]
        mean_freq = statistics.mean(frequencies)
        std_freq = statistics.stdev(frequencies) if len(frequencies) > 1 else 0
        
        for number, abs_freq, rel_freq in all_frequencies:
            # Puntuación base normalizada
            base_score = (rel_freq * 100)
            
            # Bonus por estar por encima del promedio
            if abs_freq > mean_freq and std_freq > 0:
                z_score = (abs_freq - mean_freq) / std_freq
                base_score += z_score * 10
            
            # Confianza basada en consistencia
            confidence = min(0.9, rel_freq * 8 + 0.4)
            
            scores[number] = {
                'score': max(base_score, 0),
                'confidence': confidence,
                'details': {
                    'appearances': abs_freq,
                    'relative_frequency': rel_freq,
                    'z_score': (abs_freq - mean_freq) / std_freq if std_freq > 0 else 0
                }
            }
        
        return scores
    
    def _calculate_gap_component(self, days: int) -> Dict[int, Dict[str, float]]:
        """Calcula puntuaciones basadas en análisis de gaps"""
        
        # Obtener datos de gaps
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 50:
            return {}
        
        # Calcular gaps para cada número
        number_appearances = defaultdict(list)
        for draw in draws:
            try:
                draw_date = datetime.strptime(str(draw[0]), '%Y-%m-%d')
                number = draw[1]
                number_appearances[number].append(draw_date)
            except:
                continue
        
        scores = {}
        
        for number, dates in number_appearances.items():
            if len(dates) >= 2:
                dates.sort()
                gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                
                if gaps:
                    avg_gap = statistics.mean(gaps)
                    gap_std = statistics.stdev(gaps) if len(gaps) > 1 else avg_gap * 0.5
                    days_since_last = (datetime.now() - dates[-1]).days
                    
                    # Puntuación basada en retraso vs promedio
                    if avg_gap > 0:
                        delay_ratio = days_since_last / avg_gap
                        
                        # Números muy atrasados obtienen alta puntuación
                        if delay_ratio > 1.5:
                            base_score = min(delay_ratio * 20, 100)
                            confidence = min(0.8, 0.4 + (delay_ratio - 1) * 0.3)
                        # Números cerca del tiempo esperado obtienen puntuación media
                        elif 0.7 <= delay_ratio <= 1.3:
                            base_score = 30 - abs(delay_ratio - 1) * 20
                            confidence = 0.6
                        # Números que aparecieron muy recientemente obtienen baja puntuación
                        else:
                            base_score = max(10 - delay_ratio * 5, 0)
                            confidence = 0.3
                        
                        scores[number] = {
                            'score': base_score,
                            'confidence': confidence,
                            'details': {
                                'days_since_last': days_since_last,
                                'average_gap': avg_gap,
                                'delay_ratio': delay_ratio,
                                'appearances': len(dates)
                            }
                        }
        
        return scores
    
    def _calculate_trend_component(self, days: int) -> Dict[int, Dict[str, float]]:
        """Calcula puntuaciones basadas en tendencias recientes"""
        
        # Analizar múltiples ventanas temporales
        windows = [
            (min(30, days // 4), 'reciente'),
            (min(90, days // 2), 'medio'),
            (days, 'base')
        ]
        
        window_data = {}
        for window_days, window_name in windows:
            if window_days > 0:
                freqs = self.db.get_all_numbers_frequency(window_days)
                window_data[window_name] = {num: rel_freq for num, _, rel_freq in freqs}
        
        scores = {}
        
        for number in set().union(*[data.keys() for data in window_data.values()]):
            recent_freq = window_data.get('reciente', {}).get(number, 0)
            medium_freq = window_data.get('medio', {}).get(number, 0)
            base_freq = window_data.get('base', {}).get(number, 0)
            
            # Calcular momentum (tendencia)
            if base_freq > 0:
                momentum = (recent_freq - base_freq) / base_freq
            else:
                momentum = recent_freq * 2  # Números nuevos obtienen bonus
            
            # Puntuación basada en momentum y frecuencia reciente
            base_score = recent_freq * 50 + momentum * 30
            confidence = min(0.8, recent_freq * 5 + 0.3)
            
            if base_score > 0:
                scores[number] = {
                    'score': base_score,
                    'confidence': confidence,
                    'details': {
                        'recent_frequency': recent_freq,
                        'momentum': momentum,
                        'trend_direction': 'up' if momentum > 0.1 else 'down' if momentum < -0.1 else 'stable'
                    }
                }
        
        return scores
    
    def _calculate_pattern_component(self, days: int) -> Dict[int, Dict[str, float]]:
        """Calcula puntuaciones basadas en patrones (dígitos, correlaciones)"""
        
        # Obtener números recientes para correlaciones
        recent_date = datetime.now() - timedelta(days=30)
        recent_draws = self.db.get_draws_in_period(recent_date, datetime.now())
        recent_numbers = set(draw[1] for draw in recent_draws)
        
        # Obtener todos los números para análisis de dígitos
        all_draws = self.db.get_draws_in_period(
            datetime.now() - timedelta(days=days), datetime.now()
        )
        all_numbers = [draw[1] for draw in all_draws]
        
        scores = {}
        
        # Análisis de dígitos favorables
        if all_numbers:
            units_digits = [num % 10 for num in all_numbers]
            tens_digits = [num // 10 for num in all_numbers]
            
            units_freq = Counter(units_digits)
            tens_freq = Counter(tens_digits)
            
            # Identificar dígitos más frecuentes
            top_units = set(digit for digit, _ in units_freq.most_common(4))
            top_tens = set(digit for digit, _ in tens_freq.most_common(4))
            
            for number in range(0, 100):
                unit_digit = number % 10
                ten_digit = number // 10
                
                pattern_score = 0
                
                # Bonus por dígitos favorables
                if unit_digit in top_units:
                    pattern_score += 15
                if ten_digit in top_tens:
                    pattern_score += 15
                
                # Bonus adicional por combinación favorable
                if unit_digit in top_units and ten_digit in top_tens:
                    pattern_score += 10
                
                if pattern_score > 0:
                    scores[number] = {
                        'score': pattern_score,
                        'confidence': min(0.7, pattern_score / 40 + 0.3),
                        'details': {
                            'favorable_unit': unit_digit in top_units,
                            'favorable_ten': ten_digit in top_tens,
                            'digit_pattern_strength': pattern_score / 40
                        }
                    }
        
        return scores
    
    def _combine_component_scores(
        self, 
        component_scores: Dict[str, Dict], 
        weights: Dict[str, float]
    ) -> Dict[int, Dict[str, float]]:
        """Combina las puntuaciones de todos los componentes"""
        
        final_scores = {}
        all_numbers = set()
        
        # Recopilar todos los números
        for component, scores in component_scores.items():
            all_numbers.update(scores.keys())
        
        for number in all_numbers:
            total_score = 0
            total_confidence = 0
            active_components = []
            component_details = {}
            
            for component, weight in weights.items():
                if component in component_scores and number in component_scores[component]:
                    comp_data = component_scores[component][number]
                    total_score += comp_data['score'] * weight
                    total_confidence += comp_data['confidence'] * weight
                    active_components.append(component)
                    component_details[component] = comp_data['details']
            
            if active_components:
                final_scores[number] = {
                    'score': total_score,
                    'confidence': min(total_confidence, 1.0),
                    'active_components': active_components,
                    'component_details': component_details
                }
        
        return final_scores
    
    def _finalize_predictions(
        self, 
        final_scores: Dict[int, Dict], 
        num_predictions: int, 
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Finaliza y ordena las predicciones"""
        
        # Filtrar por confianza y ordenar por puntuación
        candidates = [
            (number, data) for number, data in final_scores.items()
            if data['confidence'] >= confidence_threshold
        ]
        
        candidates.sort(key=lambda x: x[1]['score'], reverse=True)
        
        predictions = []
        for i, (number, data) in enumerate(candidates[:num_predictions]):
            prediction = {
                'rank': i + 1,
                'number': number,
                'score': round(data['score'], 2),
                'confidence': round(data['confidence'], 3),
                'confidence_level': self._get_confidence_level(data['confidence']),
                'active_components': data['active_components'],
                'reasoning': self._generate_reasoning(number, data),
                'component_details': data['component_details']
            }
            predictions.append(prediction)
        
        return predictions
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convierte confianza numérica a nivel descriptivo"""
        if confidence >= 0.8:
            return 'Alta'
        elif confidence >= 0.6:
            return 'Media'
        elif confidence >= 0.4:
            return 'Moderada'
        else:
            return 'Baja'
    
    def _generate_reasoning(self, number: int, data: Dict) -> str:
        """Genera explicación textual de la predicción"""
        
        reasons = []
        components = data['active_components']
        details = data['component_details']
        
        if 'frequency' in components and 'frequency' in details:
            freq_data = details['frequency']
            reasons.append(f"Frecuencia: {freq_data['appearances']} apariciones")
        
        if 'gaps' in components and 'gaps' in details:
            gap_data = details['gaps']
            if gap_data['delay_ratio'] > 1.5:
                reasons.append(f"Atrasado: {gap_data['days_since_last']}d vs {gap_data['average_gap']:.1f}d promedio")
            else:
                reasons.append(f"Gap regular: {gap_data['days_since_last']}d")
        
        if 'trends' in components and 'trends' in details:
            trend_data = details['trends']
            if trend_data['trend_direction'] != 'stable':
                reasons.append(f"Tendencia {trend_data['trend_direction']}")
        
        if 'patterns' in components and 'patterns' in details:
            pattern_data = details['patterns']
            if pattern_data['favorable_unit'] or pattern_data['favorable_ten']:
                reasons.append("Patrón de dígitos favorable")
        
        return " | ".join(reasons) if reasons else "Análisis combinado"
    
    def _calculate_statistics(self, predictions: List[Dict]) -> Dict[str, Any]:
        """Calcula estadísticas de las predicciones"""
        
        if not predictions:
            return {}
        
        scores = [p['score'] for p in predictions]
        confidences = [p['confidence'] for p in predictions]
        
        return {
            'total_predictions': len(predictions),
            'score_stats': {
                'average': round(statistics.mean(scores), 2),
                'min': round(min(scores), 2),
                'max': round(max(scores), 2),
                'median': round(statistics.median(scores), 2)
            },
            'confidence_stats': {
                'average': round(statistics.mean(confidences), 3),
                'min': round(min(confidences), 3),
                'max': round(max(confidences), 3)
            },
            'confidence_distribution': {
                'alta': len([c for c in confidences if c >= 0.8]),
                'media': len([c for c in confidences if 0.6 <= c < 0.8]),
                'moderada': len([c for c in confidences if 0.4 <= c < 0.6]),
                'baja': len([c for c in confidences if c < 0.4])
            }
        }
    
    def _analyze_component_contributions(
        self, 
        component_scores: Dict, 
        weights: Dict, 
        predictions: List[Dict]
    ) -> Dict[str, Any]:
        """Analiza la contribución de cada componente"""
        
        contributions = {}
        
        for component, weight in weights.items():
            if component in component_scores:
                component_numbers = set(component_scores[component].keys())
                predicted_numbers = set(p['number'] for p in predictions)
                
                overlap = len(component_numbers.intersection(predicted_numbers))
                
                contributions[component] = {
                    'weight': weight,
                    'numbers_found': len(component_numbers),
                    'numbers_in_predictions': overlap,
                    'effectiveness': overlap / len(predicted_numbers) if predicted_numbers else 0
                }
        
        return contributions
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido"""
        if cache_key not in self._cache:
            return False
        
        cache_time = self._cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).seconds < self._cache_timeout
    
    def get_available_strategies(self) -> Dict[str, Dict[str, str]]:
        """Obtiene las estrategias disponibles"""
        return {
            key: {
                'name': config['name'],
                'description': config['description']
            }
            for key, config in self.strategies.items()
        }
    
    def clear_cache(self):
        """Limpia el cache"""
        self._cache.clear()

def main():
    """Función de prueba"""
    print("🚀 SERVICIO DE PREDICCIONES UNIFICADO")
    print("="*50)
    
    db = DatabaseManager()
    service = UnifiedPredictionService(db)
    
    # Probar diferentes estrategias
    for strategy in ['conservative', 'balanced', 'aggressive']:
        print(f"\n🎯 Probando estrategia: {strategy}")
        result = service.generate_predictions(
            strategy=strategy,
            num_predictions=5,
            confidence_threshold=0.3
        )
        
        print(f"   Predicciones generadas: {len(result['predictions'])}")
        for pred in result['predictions'][:3]:
            print(f"   {pred['rank']}. Número {pred['number']} - Score: {pred['score']} - {pred['reasoning']}")

if __name__ == "__main__":
    main()