#!/usr/bin/env python3
"""
Servicio de Predicciones Unificado - Quiniela Loteka
Combina toda la funcionalidad de predicción en un solo servicio configurable
"""

import time
import sys

def log_timing(message):
    timestamp = time.time()
    print(f"[PREDICTION-SERVICE {timestamp:.3f}] {message}", flush=True)
    sys.stdout.flush()

log_timing("🔄 INICIO: Importando librerías para UnifiedPredictionService...")

import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import statistics
import math
from collections import defaultdict, Counter

log_timing("🔄 INICIO: Importando servicios pesados...")
from database import DatabaseManager
log_timing("🔄 INICIO: Importando StatisticalAnalyzer...")
from analyzer import StatisticalAnalyzer
log_timing("🔄 INICIO: Importando SimplifiedScientificPredictor...")
from scientific_predictor_simple import SimplifiedScientificPredictor
log_timing("🔄 INICIO: Importando PatternEngine...")
from pattern_engine import PatternEngine
log_timing("✅ COMPLETADO: Todas las importaciones de UnifiedPredictionService")

class ComponentResult:
    """Resultado estandarizado de un componente de predicción con validación robusta"""
    def __init__(self, score: float, confidence: float, details: Dict[str, Any]):
        # Validación y normalización robusta de score
        try:
            raw_score = float(score)
            if math.isnan(raw_score) or math.isinf(raw_score):
                self.score = 0.0
            else:
                self.score = max(0.0, min(100.0, raw_score))
        except (ValueError, TypeError):
            self.score = 0.0
        
        # Validación y normalización robusta de confidence  
        try:
            raw_confidence = float(confidence)
            if math.isnan(raw_confidence) or math.isinf(raw_confidence):
                self.confidence = 0.0
            else:
                self.confidence = max(0.0, min(1.0, raw_confidence))
        except (ValueError, TypeError):
            self.confidence = 0.0
        
        # Validación de details
        self.details = details if isinstance(details, dict) else {}
        
        # Verificar coherencia score-confidence
        if self.score > 0 and self.confidence == 0:
            self.confidence = 0.1  # Confianza mínima si hay score
        elif self.score == 0 and self.confidence > 0:
            self.confidence = 0.0  # Sin confianza si no hay score

class PredictionComponent:
    """Clase base para componentes de predicción estandarizados"""
    
    def __init__(self, name: str, weight_factor: float = 1.0):
        self.name = name
        self.weight_factor = weight_factor
    
    def calculate(self, days: int) -> Dict[int, ComponentResult]:
        """Calcula puntuaciones para todos los números"""
        raise NotImplementedError
    
    def validate_data(self, data: Any) -> bool:
        """Valida que los datos sean suficientes"""
        return data is not None

class FrequencyComponent(PredictionComponent):
    """Componente de análisis de frecuencia"""
    
    def __init__(self, db_manager):
        super().__init__("frequency")
        self.db = db_manager
    
    def calculate(self, days: int) -> Dict[int, ComponentResult]:
        """Calcula scores basados en frecuencia histórica"""
        try:
            frequencies = self.db.get_all_numbers_frequency(days)
            if not frequencies:
                return {}
            
            results = {}
            for number, abs_freq, rel_freq in frequencies:
                score = rel_freq * 100  # Normalizar a 0-100
                confidence = min(0.9, abs_freq / 10)  # Más apariciones = más confianza
                
                results[number] = ComponentResult(
                    score=score,
                    confidence=confidence,
                    details={
                        'absolute_frequency': abs_freq,
                        'relative_frequency': rel_freq,
                        'total_appearances': abs_freq
                    }
                )
            return results
        except Exception as e:
            print(f"⚠️ Error en FrequencyComponent: {e}")
            return {}

class GapsComponent(PredictionComponent):
    """Componente de análisis de gaps"""
    
    def __init__(self, db_manager):
        super().__init__("gaps")
        self.db = db_manager
    
    def calculate(self, days: int) -> Dict[int, ComponentResult]:
        """Calcula scores basados en análisis de gaps"""
        try:
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
            
            results = {}
            for number, dates in number_appearances.items():
                if len(dates) >= 2:
                    dates.sort()
                    gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    
                    if gaps:
                        avg_gap = statistics.mean(gaps)
                        days_since_last = (datetime.now() - dates[-1]).days
                        
                        if avg_gap > 0:
                            delay_ratio = days_since_last / avg_gap
                            
                            # Normalizar score a 0-100
                            if delay_ratio > 1.5:
                                score = min(delay_ratio * 20, 100)
                                confidence = min(0.8, 0.4 + (delay_ratio - 1) * 0.3)
                            elif 0.7 <= delay_ratio <= 1.3:
                                score = 50 - abs(delay_ratio - 1) * 30
                                confidence = 0.6
                            else:
                                score = max(20 - delay_ratio * 10, 0)
                                confidence = 0.3
                            
                            results[number] = ComponentResult(
                                score=score,
                                confidence=confidence,
                                details={
                                    'days_since_last': days_since_last,
                                    'average_gap': avg_gap,
                                    'delay_ratio': delay_ratio,
                                    'appearances': len(dates)
                                }
                            )
            return results
        except Exception as e:
            print(f"⚠️ Error en GapsComponent: {e}")
            return {}

class TrendsComponent(PredictionComponent):
    """Componente de análisis de tendencias"""
    
    def __init__(self, db_manager):
        super().__init__("trends")
        self.db = db_manager
    
    def calculate(self, days: int) -> Dict[int, ComponentResult]:
        """Calcula scores basados en tendencias recientes"""
        try:
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
            
            results = {}
            for number in set().union(*[data.keys() for data in window_data.values()]):
                recent_freq = window_data.get('reciente', {}).get(number, 0)
                medium_freq = window_data.get('medio', {}).get(number, 0)
                base_freq = window_data.get('base', {}).get(number, 0)
                
                # Calcular momentum (tendencia)
                if base_freq > 0:
                    momentum = (recent_freq - base_freq) / base_freq
                else:
                    momentum = recent_freq * 2
                
                # Normalizar score a 0-100
                score = (recent_freq * 50 + momentum * 30)
                score = max(0, min(100, score))
                confidence = min(0.8, recent_freq * 5 + 0.3)
                
                if score > 0:
                    results[number] = ComponentResult(
                        score=score,
                        confidence=confidence,
                        details={
                            'recent_frequency': recent_freq,
                            'momentum': momentum,
                            'trend_direction': 'up' if momentum > 0.1 else 'down' if momentum < -0.1 else 'stable'
                        }
                    )
            return results
        except Exception as e:
            print(f"⚠️ Error en TrendsComponent: {e}")
            return {}

class PatternsComponent(PredictionComponent):
    """Componente de análisis de patrones"""
    
    def __init__(self, db_manager, pattern_engine):
        super().__init__("patterns")
        self.db = db_manager
        self.pattern_engine = pattern_engine
    
    def calculate(self, days: int) -> Dict[int, ComponentResult]:
        """Calcula scores basados en patrones avanzados"""
        try:
            # Usar el PatternEngine para obtener puntuaciones basadas en patrones
            pattern_scores = self.pattern_engine.score_numbers(days)
            
            results = {}
            for number, pattern_data in pattern_scores.items():
                if pattern_data['score'] > 0:
                    # Normalizar score a 0-100 si no lo está ya
                    normalized_score = max(0, min(100, pattern_data['score']))
                    
                    results[number] = ComponentResult(
                        score=normalized_score,
                        confidence=pattern_data['confidence'],
                        details={
                            'pattern_types': list(pattern_data['details'].keys()),
                            'pattern_contributions': pattern_data['pattern_contributions'],
                            'advanced_patterns': True,
                            'total_patterns': len(pattern_data['pattern_contributions'])
                        }
                    )
            
            print(f"  🎯 PatternEngine encontró patrones para {len(results)} números")
            return results
            
        except Exception as e:
            print(f"  ⚠️ Error en PatternEngine, usando análisis básico: {e}")
            # Fallback al análisis básico de dígitos
            return self._calculate_basic_digit_patterns(days)
    
    def _calculate_basic_digit_patterns(self, days: int) -> Dict[int, ComponentResult]:
        """Análisis básico de patrones de dígitos como fallback"""
        try:
            all_draws = self.db.get_draws_in_period(
                datetime.now() - timedelta(days=days), datetime.now()
            )
            all_numbers = [draw[1] for draw in all_draws]
            
            if not all_numbers:
                return {}
            
            units_digits = [num % 10 for num in all_numbers]
            tens_digits = [num // 10 for num in all_numbers]
            
            units_freq = Counter(units_digits)
            tens_freq = Counter(tens_digits)
            
            # Identificar dígitos más frecuentes
            top_units = set(digit for digit, _ in units_freq.most_common(4))
            top_tens = set(digit for digit, _ in tens_freq.most_common(4))
            
            results = {}
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
                    results[number] = ComponentResult(
                        score=pattern_score,
                        confidence=min(0.7, pattern_score / 40 + 0.3),
                        details={
                            'favorable_unit': unit_digit in top_units,
                            'favorable_ten': ten_digit in top_tens,
                            'digit_pattern_strength': pattern_score / 40,
                            'fallback_mode': True
                        }
                    )
            return results
        except Exception as e:
            print(f"⚠️ Error en análisis básico de patrones: {e}")
            return {}

class UnifiedPredictionService:
    """Servicio unificado de predicciones con múltiples estrategias"""
    
    def __init__(self, db_manager: DatabaseManager):
        log_timing("🔄 INICIO: Constructor UnifiedPredictionService...")
        self.db = db_manager
        log_timing("🔄 INICIO: Inicializando StatisticalAnalyzer...")
        self.analyzer = StatisticalAnalyzer(db_manager)
        log_timing("🔄 INICIO: Inicializando SimplifiedScientificPredictor...")
        self.scientific_predictor = SimplifiedScientificPredictor(db_manager)
        log_timing("🔄 INICIO: Inicializando PatternEngine...")
        self.pattern_engine = PatternEngine(db_manager)
        log_timing("✅ COMPLETADO: Constructor UnifiedPredictionService")
        self.number_range = (0, 99)
        
        # Componentes estandarizados
        self.components = {
            'frequency': FrequencyComponent(self.db),
            'gaps': GapsComponent(self.db),
            'trends': TrendsComponent(self.db),
            'patterns': PatternsComponent(self.db, self.pattern_engine)
        }
        
        # Estrategias de predicción mejoradas con ponderación adaptativa
        self.base_strategies = {
            'balanced': {
                'name': 'Equilibrado',
                'description': 'Balance dinámico entre todos los componentes',
                'base_weights': {
                    'frequency': 0.30,  # Base sólida - datos históricos
                    'gaps': 0.25,      # Teoría de intervalos matemática
                    'trends': 0.25,    # Momentum reciente
                    'patterns': 0.20   # Patrones complejos
                },
                'adaptability': 0.3  # 30% de adaptabilidad
            },
            'conservative': {
                'name': 'Conservador',
                'description': 'Basado en evidencia histórica sólida',
                'base_weights': {
                    'frequency': 0.50,  # Prioriza historial
                    'gaps': 0.25,      # Intervalos matemáticos
                    'trends': 0.15,    # Menos peso a tendencias
                    'patterns': 0.10   # Mínimo en patrones complejos
                },
                'adaptability': 0.1  # 10% de adaptabilidad
            },
            'aggressive': {
                'name': 'Agresivo',
                'description': 'Enfocado en señales recientes y oportunidades',
                'base_weights': {
                    'frequency': 0.15,  # Menos historial
                    'gaps': 0.35,      # Alta prioridad a números atrasados
                    'trends': 0.35,    # Alta prioridad a momentum
                    'patterns': 0.15   # Patrones emergentes
                },
                'adaptability': 0.5  # 50% de adaptabilidad
            },
            'scientific': {
                'name': 'Científico Avanzado',
                'description': 'Análisis probabilístico con ML, Bayesiano y ensemble',
                'base_weights': {
                    'bayesian': 0.25,
                    'ml': 0.25,
                    'gaps': 0.25,
                    'trends': 0.15,
                    'patterns': 0.10
                },
                'adaptability': 0.0  # Estrategia especial sin adaptación
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
        
        if strategy not in self.base_strategies:
            strategy = 'balanced'
        
        # Usar predictor científico si se selecciona esa estrategia
        if strategy == 'scientific':
            return self._generate_scientific_predictions(days, num_predictions, confidence_threshold)
        
        strategy_config = self.base_strategies[strategy]
        
        # Calcular pesos adaptativos basados en calidad de datos
        adaptive_weights = self._calculate_adaptive_weights(strategy_config, days)
        strategy_config_with_weights = {
            **strategy_config,
            'weights': adaptive_weights
        }
        weights = adaptive_weights
        
        # Cache key
        cache_key = f"{strategy}_{days}_{num_predictions}_{confidence_threshold}"
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        print(f"🎯 Generando predicciones con estrategia '{strategy_config['name']}'...")
        
        # Calcular puntuaciones por componente usando la nueva arquitectura
        component_results = {}
        
        # Verificar disponibilidad de datos básicos
        try:
            sample_data = self.db.get_draws_in_period(
                datetime.now() - timedelta(days=30), datetime.now()
            )
            if not sample_data or len(sample_data) < 10:
                print("⚠️ Datos insuficientes para predicciones confiables")
                return self._generate_fallback_result(strategy_config_with_weights)
        except Exception as e:
            print(f"❌ Error verificando datos: {e}")
            return self._generate_fallback_result(strategy_config_with_weights)
        
        # Usar componentes estandarizados con validación robusta
        for component_name, weight in weights.items():
            if weight > 0 and component_name in self.components:
                try:
                    print(f"  📊 Calculando {component_name}...")
                    results = self.components[component_name].calculate(days)
                    
                    # APLICAR VALIDACIÓN - esto es lo que faltaba
                    if results and self._validate_component_results(results, component_name):
                        component_results[component_name] = results
                        print(f"    ✅ {component_name}: {len(results)} números válidos")
                    else:
                        print(f"    ⚠️ {component_name}: Resultados no válidos o insuficientes")
                        
                except Exception as e:
                    print(f"    ❌ Error en {component_name}: {e}")
        
        # Verificar que tenemos al menos un componente válido
        if not component_results:
            print("❌ No hay componentes válidos disponibles")
            return self._generate_fallback_result(strategy_config_with_weights)
        
        # Combinar resultados usando ponderación inteligente
        try:
            final_scores = self._combine_component_results_v2(component_results, weights)
            
            if not final_scores:
                print("⚠️ No se generaron scores válidos")
                return self._generate_fallback_result(strategy_config_with_weights)
                
        except Exception as e:
            print(f"❌ Error combinando resultados: {e}")
            return self._generate_fallback_result(strategy_config_with_weights)
        
        # Filtrar y ordenar predicciones con fallback
        try:
            predictions = self._finalize_predictions_v2(
                final_scores, num_predictions, confidence_threshold
            )
            
            if not predictions or len(predictions) < max(1, num_predictions // 2):
                print(f"⚠️ Muy pocas predicciones válidas ({len(predictions) if predictions else 0})")
                # Intentar con umbral más bajo
                predictions = self._finalize_predictions_v2(
                    final_scores, num_predictions, max(0.1, confidence_threshold - 0.2)
                )
                
                if not predictions:
                    print("❌ No se encontraron predicciones válidas, usando fallback")
                    return self._generate_fallback_result(strategy_config_with_weights)
                
        except Exception as e:
            print(f"❌ Error finalizando predicciones: {e}")
            return self._generate_fallback_result(strategy_config_with_weights)
        
        # Generar resultado completo con validación
        try:
            statistics = self._calculate_statistics(predictions)
            contributions = self._analyze_component_contributions_v2(
                component_results, weights, predictions
            )
            
            result = {
                'predictions': predictions,
                'strategy': strategy_config_with_weights,
                'statistics': statistics,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_period_days': days,
                    'total_candidates': len(final_scores),
                    'confidence_threshold': confidence_threshold,
                    'components_used': list(component_results.keys()),
                    'validation_passed': True
                },
                'component_contributions': contributions
            }
            
            # Guardar en cache solo si el resultado es válido
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error generando resultado final: {e}")
            return self._generate_fallback_result(strategy_config_with_weights)
    
    def _combine_component_results_v2(
        self, 
        component_results: Dict[str, Dict[int, ComponentResult]], 
        weights: Dict[str, float]
    ) -> Dict[int, Dict[str, Any]]:
        """Combina resultados de componentes con validación y normalización robusta"""
        
        final_scores = {}
        all_numbers = set()
        
        # Recopilar todos los números de todos los componentes
        for component_name, results in component_results.items():
            all_numbers.update(results.keys())
        
        print(f"  🔄 Combinando {len(all_numbers)} números únicos...")
        
        for number in all_numbers:
            total_score = 0.0
            weighted_confidence = 0.0
            total_weight = 0.0
            active_components = []
            component_details = {}
            
            # Combinar scores de cada componente activo
            for component_name, weight in weights.items():
                if weight > 0 and component_name in component_results:
                    if number in component_results[component_name]:
                        comp_result = component_results[component_name][number]
                        
                        # Validar que ComponentResult tiene los atributos necesarios
                        if hasattr(comp_result, 'score') and hasattr(comp_result, 'confidence'):
                            # Scores ya están normalizados a 0-100 por ComponentResult
                            normalized_score = comp_result.score
                            confidence = comp_result.confidence
                            
                            # Aplicar peso
                            weighted_score = normalized_score * weight
                            total_score += weighted_score
                            weighted_confidence += confidence * weight
                            total_weight += weight
                            
                            active_components.append(component_name)
                            component_details[component_name] = comp_result.details
            
            # Solo incluir números con al menos un componente activo
            if active_components and total_weight > 0:
                # Normalizar confianza por peso total
                avg_confidence = weighted_confidence / total_weight
                
                final_scores[number] = {
                    'score': total_score,
                    'confidence': min(1.0, avg_confidence),
                    'active_components': active_components,
                    'component_details': component_details,
                    'weight_total': total_weight
                }
        
        print(f"  ✅ {len(final_scores)} números con predicciones válidas")
        return final_scores
    
    def _finalize_predictions_v2(
        self, 
        final_scores: Dict[int, Dict[str, Any]], 
        num_predictions: int, 
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Finaliza y ordena las predicciones con validación mejorada"""
        
        if not final_scores:
            return []
        
        # Filtrar por confianza y validar datos
        valid_candidates = []
        for number, data in final_scores.items():
            if (data.get('confidence', 0) >= confidence_threshold and 
                data.get('score', 0) > 0 and 
                data.get('active_components')):
                valid_candidates.append((number, data))
        
        # Ordenar por puntuación (mayor a menor)
        valid_candidates.sort(key=lambda x: x[1]['score'], reverse=True)
        
        predictions = []
        for i, (number, data) in enumerate(valid_candidates[:num_predictions]):
            prediction = {
                'rank': i + 1,
                'number': number,
                'score': round(data['score'], 2),
                'confidence': round(data['confidence'], 3),
                'confidence_level': self._get_confidence_level(data['confidence']),
                'active_components': data['active_components'],
                'reasoning': self._generate_reasoning_v2(number, data),
                'component_details': data['component_details']
            }
            predictions.append(prediction)
        
        return predictions
    
    def _generate_reasoning_v2(self, number: int, data: Dict[str, Any]) -> str:
        """Genera explicación textual mejorada de la predicción"""
        
        reasons = []
        components = data['active_components']
        details = data['component_details']
        
        # Analizar cada componente activo
        for component_name in components:
            if component_name in details:
                comp_details = details[component_name]
                
                if component_name == 'frequency':
                    freq = comp_details.get('relative_frequency', 0)
                    reasons.append(f"Frecuencia: {freq:.3f}")
                
                elif component_name == 'gaps':
                    delay_ratio = comp_details.get('delay_ratio', 1)
                    if delay_ratio > 1.5:
                        days = comp_details.get('days_since_last', 0)
                        avg = comp_details.get('average_gap', 0)
                        reasons.append(f"Atrasado: {days}d vs {avg:.1f}d promedio")
                    else:
                        reasons.append("Gap normal")
                
                elif component_name == 'trends':
                    direction = comp_details.get('trend_direction', 'stable')
                    if direction != 'stable':
                        reasons.append(f"Tendencia {direction}")
                
                elif component_name == 'patterns':
                    if comp_details.get('advanced_patterns'):
                        total = comp_details.get('total_patterns', 0)
                        reasons.append(f"Patrones avanzados ({total})")
                    elif comp_details.get('fallback_mode'):
                        reasons.append("Patrón de dígitos favorable")
        
        return " | ".join(reasons) if reasons else f"Análisis combinado ({len(components)} componentes)"
    
    def _analyze_component_contributions_v2(
        self, 
        component_results: Dict[str, Dict[int, ComponentResult]], 
        weights: Dict[str, float], 
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analiza las contribuciones de cada componente con métricas mejoradas"""
        
        contributions = {}
        
        for component_name, weight in weights.items():
            if component_name in component_results and weight > 0:
                results = component_results[component_name]
                
                # Métricas del componente
                scores = [r.score for r in results.values()]
                confidences = [r.confidence for r in results.values()]
                
                # Contar cuántas predicciones finales incluyen este componente
                predictions_with_component = sum(
                    1 for p in predictions 
                    if component_name in p['active_components']
                )
                
                contributions[component_name] = {
                    'weight': weight,
                    'numbers_analyzed': len(results),
                    'average_score': round(statistics.mean(scores), 2) if scores else 0,
                    'average_confidence': round(statistics.mean(confidences), 3) if confidences else 0,
                    'predictions_influenced': predictions_with_component,
                    'influence_rate': round(predictions_with_component / len(predictions) if predictions else 0, 2)
                }
        
        return contributions
    
    def _calculate_adaptive_weights(self, strategy_config: Dict, days: int) -> Dict[str, float]:
        """Calcula pesos adaptativos basados en la calidad y disponibilidad de datos"""
        
        base_weights = strategy_config['base_weights']
        adaptability = strategy_config['adaptability']
        
        # Si no hay adaptabilidad, usar pesos base
        if adaptability == 0:
            return base_weights.copy()
        
        print(f"  🧮 Calculando pesos adaptativos (adaptabilidad: {adaptability:.1%})...")
        
        # Evaluar calidad de datos por componente
        component_quality = {}
        
        for component_name in base_weights.keys():
            if component_name in self.components:
                quality_score = self._evaluate_component_data_quality(component_name, days)
                component_quality[component_name] = quality_score
                print(f"    📊 {component_name}: calidad {quality_score:.2f}")
        
        # Ajustar pesos basado en calidad de datos
        adjusted_weights = {}
        total_adjustment = 0
        
        for component_name, base_weight in base_weights.items():
            if component_name in component_quality:
                quality = component_quality[component_name]
                
                # Factor de ajuste: calidad alta (+), calidad baja (-)
                # quality de 0.5 = neutro, >0.5 = bonus, <0.5 = penalización
                quality_factor = (quality - 0.5) * 2  # Rango [-1, 1]
                adjustment = quality_factor * adaptability * base_weight
                
                adjusted_weight = base_weight + adjustment
                adjusted_weights[component_name] = max(0.05, adjusted_weight)  # Mínimo 5%
                total_adjustment += adjustment
        
        # Normalizar para que sumen 1.0
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            normalized_weights = {
                name: weight / total_weight 
                for name, weight in adjusted_weights.items()
            }
        else:
            normalized_weights = base_weights.copy()
        
        # Mostrar ajustes significativos
        for name, weight in normalized_weights.items():
            if abs(weight - base_weights[name]) > 0.05:  # Cambio >5%
                change = weight - base_weights[name]
                print(f"    ⚖️ {name}: {base_weights[name]:.2f} → {weight:.2f} ({change:+.2f})")
        
        return normalized_weights
    
    def _validate_component_results(self, results: Dict[int, ComponentResult], component_name: str) -> bool:
        """Valida que los resultados de un componente sean coherentes y utilizables"""
        
        if not results:
            return False
        
        # Verificar que tiene un mínimo de números válidos
        if len(results) < 5:  # Mínimo 5 números para ser útil
            print(f"    ⚠️ {component_name}: Muy pocos resultados ({len(results)})")
            return False
        
        valid_results = 0
        total_score = 0
        total_confidence = 0
        
        for number, result in results.items():
            # Verificar que sea ComponentResult válido
            if not isinstance(result, ComponentResult):
                print(f"    ⚠️ {component_name}: Resultado no es ComponentResult para número {number}")
                continue
            
            # Verificar coherencia de valores
            if result.score < 0 or result.score > 100:
                print(f"    ⚠️ {component_name}: Score fuera de rango para número {number}: {result.score}")
                continue
                
            if result.confidence < 0 or result.confidence > 1:
                print(f"    ⚠️ {component_name}: Confianza fuera de rango para número {number}: {result.confidence}")
                continue
            
            # Verificar coherencia score-confidence
            if result.score > 50 and result.confidence < 0.1:
                print(f"    ⚠️ {component_name}: Score alto pero confianza muy baja para número {number}")
                continue
            
            valid_results += 1
            total_score += result.score
            total_confidence += result.confidence
        
        # Verificar que tenemos suficientes resultados válidos
        if valid_results < len(results) * 0.8:  # Al menos 80% de resultados válidos
            print(f"    ⚠️ {component_name}: Demasiados resultados inválidos ({valid_results}/{len(results)})")
            return False
        
        # Verificar que no todos los scores son iguales (diversidad)
        avg_score = total_score / valid_results if valid_results > 0 else 0
        score_variance = sum((r.score - avg_score) ** 2 for r in results.values() if isinstance(r, ComponentResult))
        
        if score_variance < 0.1:  # Muy poca variación
            print(f"    ⚠️ {component_name}: Muy poca variación en scores")
            return False
        
        return True
    
    def _generate_fallback_result(self, strategy_config: Dict) -> Dict[str, Any]:
        """Genera un resultado de fallback cuando falla la predicción normal"""
        
        print("🔄 Generando resultado de fallback...")
        
        # Intentar obtener frecuencias básicas como fallback
        try:
            basic_frequencies = self.db.get_all_numbers_frequency(365)  # Último año
            if basic_frequencies:
                # Generar predicciones básicas basadas solo en frecuencia
                predictions = []
                for i, (number, abs_freq, rel_freq) in enumerate(basic_frequencies[:10]):
                    predictions.append({
                        'rank': i + 1,
                        'number': number,
                        'score': round(rel_freq * 100, 2),
                        'confidence': 0.3,  # Confianza baja para fallback
                        'confidence_level': 'Baja',
                        'active_components': ['frequency_fallback'],
                        'reasoning': f"Fallback: Frecuencia {rel_freq:.3f}",
                        'component_details': {'frequency_fallback': {'relative_frequency': rel_freq}}
                    })
            else:
                # Último recurso: números aleatorios con información
                predictions = []
                import random
                numbers = list(range(0, 100))
                random.shuffle(numbers)
                for i in range(10):
                    predictions.append({
                        'rank': i + 1,
                        'number': numbers[i],
                        'score': 1.0,
                        'confidence': 0.1,
                        'confidence_level': 'Muy Baja',
                        'active_components': ['random_fallback'],
                        'reasoning': "Fallback: Selección aleatoria por falta de datos",
                        'component_details': {}
                    })
                    
        except Exception as e:
            print(f"❌ Error en fallback: {e}")
            predictions = []
        
        return {
            'predictions': predictions,
            'strategy': strategy_config,
            'statistics': {},
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period_days': 0,
                'total_candidates': len(predictions),
                'confidence_threshold': 0.0,
                'components_used': [],
                'validation_passed': False,
                'fallback_mode': True
            },
            'component_contributions': {}
        }
    
    def _evaluate_component_data_quality(self, component_name: str, days: int) -> float:
        """Evalúa la calidad de datos disponibles para un componente específico"""
        
        try:
            # Métricas básicas de disponibilidad de datos
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
            draws = self.db.get_draws_in_period(start_date, end_date)
            
            if not draws or len(draws) < 30:
                return 0.2  # Datos insuficientes
            
            total_draws = len(draws)
            unique_numbers = len(set(draw[1] for draw in draws))
            
            # Calidad base
            base_quality = min(1.0, total_draws / 365)  # 365 draws = calidad perfecta
            
            # Ajustes específicos por componente
            if component_name == 'frequency':
                # Frecuencia necesita muchos datos históricos
                coverage = unique_numbers / 100  # ¿Qué porcentaje de números han aparecido?
                quality = base_quality * 0.7 + coverage * 0.3
                
            elif component_name == 'gaps':
                # Gaps necesita secuencias consistentes
                # Evaluar consistencia temporal
                dates = [datetime.strptime(str(draw[0]), '%Y-%m-%d') for draw in draws]
                dates.sort()
                
                if len(dates) > 1:
                    avg_interval = (dates[-1] - dates[0]).days / len(dates)
                    consistency = min(1.0, 1.0 / (avg_interval + 1)) if avg_interval > 0 else 0.5
                    quality = base_quality * 0.8 + consistency * 0.2
                else:
                    quality = 0.3
                    
            elif component_name == 'trends':
                # Tendencias necesitan datos recientes
                recent_days = 90
                recent_draws = [
                    d for d in draws 
                    if (datetime.now() - datetime.strptime(str(d[0]), '%Y-%m-%d')).days <= recent_days
                ]
                recent_ratio = len(recent_draws) / min(recent_days, total_draws)
                quality = base_quality * 0.6 + recent_ratio * 0.4
                
            elif component_name == 'patterns':
                # Patrones necesitan diversidad y volumen
                diversity = unique_numbers / 100
                volume_score = min(1.0, total_draws / 1000)  # 1000+ draws ideales para patrones
                quality = base_quality * 0.5 + diversity * 0.3 + volume_score * 0.2
                
            else:
                quality = base_quality
            
            return max(0.1, min(1.0, quality))  # Rango [0.1, 1.0]
            
        except Exception as e:
            print(f"    ⚠️ Error evaluando calidad de {component_name}: {e}")
            return 0.5  # Calidad neutral por defecto
    
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
        """Calcula puntuaciones basadas en patrones avanzados usando PatternEngine"""
        
        try:
            # Usar el PatternEngine para obtener puntuaciones basadas en patrones
            pattern_scores = self.pattern_engine.score_numbers(days)
            
            # Convertir formato del PatternEngine al formato esperado
            scores = {}
            
            for number, pattern_data in pattern_scores.items():
                if pattern_data['score'] > 0:  # Solo incluir números con puntuaciones positivas
                    scores[number] = {
                        'score': pattern_data['score'],
                        'confidence': pattern_data['confidence'],
                        'details': {
                            'pattern_types': list(pattern_data['details'].keys()),
                            'pattern_contributions': pattern_data['pattern_contributions'],
                            'advanced_patterns': True,
                            'total_patterns': len(pattern_data['pattern_contributions'])
                        }
                    }
            
            print(f"  🎯 PatternEngine encontró patrones para {len(scores)} números")
            return scores
            
        except Exception as e:
            print(f"  ⚠️ Error en PatternEngine, usando análisis básico: {e}")
            
            # Fallback al análisis básico de dígitos si hay error
            return self._calculate_basic_digit_patterns(days)
    
    def _calculate_basic_digit_patterns(self, days: int) -> Dict[int, Dict[str, float]]:
        """Análisis básico de patrones de dígitos como fallback"""
        
        # Obtener todos los números para análisis de dígitos
        all_draws = self.db.get_draws_in_period(
            datetime.now() - timedelta(days=days), datetime.now()
        )
        all_numbers = [draw[1] for draw in all_draws]
        
        scores = {}
        
        # Análisis de dígitos favorables (versión simplificada)
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
                            'digit_pattern_strength': pattern_score / 40,
                            'fallback_mode': True
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
            # Handle both advanced patterns and basic fallback patterns
            if 'favorable_unit' in pattern_data and 'favorable_ten' in pattern_data:
                # Basic fallback pattern structure
                if pattern_data['favorable_unit'] or pattern_data['favorable_ten']:
                    reasons.append("Patrón de dígitos favorable")
            elif 'advanced_patterns' in pattern_data and pattern_data['advanced_patterns']:
                # Advanced PatternEngine structure
                total_patterns = pattern_data.get('total_patterns', 0)
                if total_patterns > 0:
                    reasons.append(f"Patrones avanzados detectados ({total_patterns})")
        
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
            for key, config in self.base_strategies.items()
        }
    
    def clear_cache(self):
        """Limpia el cache"""
        self._cache.clear()
    
    def _generate_scientific_predictions(
        self, 
        days: int, 
        num_predictions: int, 
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """Genera predicciones usando el sistema científico avanzado"""
        
        cache_key = f"scientific_{days}_{num_predictions}_{confidence_threshold}"
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        print(f"🔬 Generando predicciones científicas...")
        
        try:
            # Calcular frecuencias una sola vez (optimización de rendimiento)
            frequency_data = self.scientific_predictor.calculate_advanced_frequencies(days)
            
            # Entrenar modelo ML
            ml_model = self.scientific_predictor.train_ml_enhanced_model(frequency_data)
            
            # Obtener predicciones científicas
            scientific_predictions = self.scientific_predictor.generate_ensemble_predictions(
                frequency_data,
                ml_model,
                num_predictions=num_predictions
            )
            
            # Filtrar por umbral de confianza
            filtered_predictions = [
                pred for pred in scientific_predictions 
                if pred.confidence >= confidence_threshold
            ]
            
            # Convertir a formato estándar
            predictions = []
            for pred in filtered_predictions:
                predictions.append({
                    'number': pred.number,
                    'score': pred.probability,
                    'confidence': pred.confidence,
                    'confidence_level': self._get_confidence_level(pred.confidence),
                    'reasoning': pred.reasoning,
                    'rank': pred.rank,
                    'active_components': list(pred.components.keys())
                })
            
            # Estadísticas (corregir nombre del método)
            statistics = self._calculate_statistics(predictions)
            
            # Análisis de componentes científicos
            component_contributions = {
                'bayesian': {
                    'weight': 0.25,
                    'numbers_found': len([p for p in filtered_predictions if p.components.get('bayesian', 0) > 0.01]),
                    'numbers_in_predictions': len([p for p in filtered_predictions if p.components.get('bayesian', 0) > 0.05]),
                    'effectiveness': 0.8
                },
                'machine_learning': {
                    'weight': 0.25,
                    'numbers_found': len([p for p in filtered_predictions if p.components.get('ml', 0) > 0.01]),
                    'numbers_in_predictions': len([p for p in filtered_predictions if p.components.get('ml', 0) > 0.05]),
                    'effectiveness': 0.75
                },
                'gap_analysis': {
                    'weight': 0.25,
                    'numbers_found': len([p for p in filtered_predictions if p.components.get('gap', 0) > 0.01]),
                    'numbers_in_predictions': len([p for p in filtered_predictions if p.components.get('gap', 0) > 0.05]),
                    'effectiveness': 0.7
                }
            }
            
            result = {
                'predictions': predictions,
                'statistics': statistics,
                'component_contributions': component_contributions,
                'strategy': 'scientific',
                'total_analyzed': 100,
                'generation_time': datetime.now().isoformat(),
                'data_period_days': days
            }
            
            # Guardar en cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error en predicciones científicas: {e}")
            # Fallback a estrategia balanced
            return self.generate_predictions('balanced', days, num_predictions, confidence_threshold)
    
    def get_daily_recommendation(self, days: int = 1825) -> Dict[str, Any]:
        """Obtiene la recomendación diaria (jugada del día) con análisis científico"""
        
        print("🎯 Generando JUGADA DEL DÍA con análisis científico...")
        
        try:
            daily_picks = self.scientific_predictor.get_daily_recommendation(days)
            
            recommendations = []
            for pick in daily_picks:
                recommendations.append({
                    'number': pick.number,
                    'probability': pick.probability,
                    'confidence': pick.confidence,
                    'reasoning': pick.reasoning,
                    'components': pick.components,
                    'rank': pick.rank
                })
            
            return {
                'type': 'daily_recommendation',
                'recommendations': recommendations,
                'total_numbers': len(recommendations),
                'analysis_method': 'scientific_ensemble',
                'generation_time': datetime.now().isoformat(),
                'data_period_days': days
            }
            
        except Exception as e:
            print(f"❌ Error en recomendación diaria: {e}")
            # Fallback
            fallback = self.generate_predictions('balanced', days, 3, 0.2)
            return {
                'type': 'daily_recommendation_fallback',
                'recommendations': fallback['predictions'][:3],
                'total_numbers': 3,
                'analysis_method': 'balanced_fallback',
                'generation_time': datetime.now().isoformat()
            }
    
    def get_weekly_recommendation(self, days: int = 1825) -> Dict[str, Any]:
        """Obtiene recomendación semanal (números estables) con análisis científico"""
        
        print("📅 Generando NÚMEROS PARA LA SEMANA con análisis científico...")
        
        try:
            weekly_picks = self.scientific_predictor.get_weekly_recommendation(days)
            
            recommendations = []
            for pick in weekly_picks:
                recommendations.append({
                    'number': pick.number,
                    'stability_score': pick.probability,
                    'confidence': pick.confidence,
                    'reasoning': pick.reasoning,
                    'components': pick.components,
                    'rank': pick.rank
                })
            
            return {
                'type': 'weekly_recommendation',
                'recommendations': recommendations,
                'total_numbers': len(recommendations),
                'analysis_method': 'scientific_stability',
                'generation_time': datetime.now().isoformat(),
                'data_period_days': days
            }
            
        except Exception as e:
            print(f"❌ Error en recomendación semanal: {e}")
            # Fallback
            fallback = self.generate_predictions('conservative', days, 3, 0.3)
            return {
                'type': 'weekly_recommendation_fallback',
                'recommendations': fallback['predictions'][:3],
                'total_numbers': 3,
                'analysis_method': 'conservative_fallback',
                'generation_time': datetime.now().isoformat()
            }

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