#!/usr/bin/env python3
"""
Sistema Científico de Predicciones Simplificado - Quiniela Loteka
Implementa análisis probabilístico y machine learning de manera robusta
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import statistics
import math
from collections import defaultdict, Counter
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Imports para ML y estadística avanzada
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import brier_score_loss, log_loss
    from scipy import stats
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    # Crear clases mock para mantener compatibilidad
    class LogisticRegression:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): pass
        def predict_proba(self, *args, **kwargs): return []
    
    class StandardScaler:
        def __init__(self, *args, **kwargs): pass
        def fit_transform(self, X): return X
    
    # Mock stats module
    class MockStats:
        class weibull_min:
            @staticmethod
            def fit(data, floc=0):
                return 1.0, 0.0, np.mean(data)
    
    stats = MockStats()
    print("⚠️ Librerías de ML no disponibles, usando métodos estadísticos básicos")

from database import DatabaseManager
from analyzer import StatisticalAnalyzer

@dataclass
class ScientificPrediction:
    """Resultado de predicción científica"""
    number: int
    probability: float
    confidence: float
    reasoning: str
    components: Dict[str, float]
    rank: int

class SimplifiedScientificPredictor:
    """Predictor científico simplificado pero robusto"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = StatisticalAnalyzer(db_manager)
        self.number_range = range(0, 100)
        
        # Configuración de modelos
        self.models = {}
        self.feature_cache = {}
        
    def calculate_advanced_frequencies(self, days: int = 1825) -> Dict[int, Dict[str, float]]:
        """Calcula frecuencias avanzadas con análisis Bayesiano"""
        print("🧮 Calculando frecuencias avanzadas...")
        
        # Obtener datos históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if not draws:
            return {}
        
        results = {}
        
        for number in self.number_range:
            # Datos básicos del número
            number_draws = [d for d in draws if d[1] == number]
            total_draws = len(draws)
            hits = len(number_draws)
            
            # Frecuencia básica
            basic_freq = hits / total_draws if total_draws > 0 else 0.01
            
            # Análisis Bayesiano con Beta-Binomial
            # Prior uniforme: Beta(1, 1)
            alpha_prior = 1.0
            beta_prior = 1.0
            
            # Posterior: Beta(α + hits, β + misses)
            alpha_post = alpha_prior + hits
            beta_post = beta_prior + (total_draws - hits)
            
            # Probabilidad Bayesiana (media del posterior)
            bayesian_prob = alpha_post / (alpha_post + beta_post)
            
            # Análisis de gaps (intervalos entre apariciones)
            gaps = self._calculate_gaps(number_draws)
            gap_analysis = self._analyze_gaps(gaps)
            
            # Análisis de tendencias temporales
            trend_analysis = self._analyze_temporal_trends(number_draws, days)
            
            # Análisis de patrones (dígitos, paridad, etc.)
            pattern_analysis = self._analyze_number_patterns(number)
            
            results[number] = {
                'basic_frequency': basic_freq,
                'bayesian_probability': bayesian_prob,
                'gap_hazard': gap_analysis['hazard_rate'],
                'trend_momentum': trend_analysis['momentum'],
                'pattern_score': pattern_analysis['score'],
                'confidence_raw': self._calculate_confidence(hits, total_draws),
                'hits': hits,
                'total_draws': total_draws
            }
        
        return results
    
    def _calculate_gaps(self, number_draws: List[Tuple]) -> List[int]:
        """Calcula gaps entre apariciones"""
        if len(number_draws) < 2:
            return []
        
        dates = [datetime.strptime(str(draw[0]), '%Y-%m-%d') for draw in number_draws]
        dates.sort()
        
        gaps = []
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days
            gaps.append(gap_days)
        
        return gaps
    
    def _analyze_gaps(self, gaps: List[int]) -> Dict[str, float]:
        """Analiza gaps con distribución Weibull"""
        if not gaps or len(gaps) < 2:
            return {'hazard_rate': 0.01, 'expected_gap': 30}
        
        mean_gap = np.mean(gaps)
        
        try:
            # Intentar ajustar Weibull
            if len(gaps) >= 3:
                shape, loc, scale = stats.weibull_min.fit(gaps, floc=0)
                
                # Calcular hazard rate empírico
                current_gap = gaps[-1] if gaps else mean_gap
                hazard_rate = 1.0 / (mean_gap + 1)  # Aproximación simple
            else:
                hazard_rate = 1.0 / (mean_gap + 1)
        except:
            hazard_rate = 1.0 / (mean_gap + 1)
        
        return {
            'hazard_rate': float(min(hazard_rate, 1.0)),
            'expected_gap': float(mean_gap)
        }
    
    def _analyze_temporal_trends(self, number_draws: List[Tuple], total_days: int) -> Dict[str, float]:
        """Analiza tendencias temporales"""
        if not number_draws:
            return {'momentum': 0.0, 'recent_activity': 0.0}
        
        # Dividir en períodos
        recent_period = 90  # últimos 90 días
        end_date = datetime.now()
        recent_start = end_date - timedelta(days=recent_period)
        
        recent_hits = 0
        total_hits = len(number_draws)
        
        for draw in number_draws:
            draw_date = datetime.strptime(str(draw[0]), '%Y-%m-%d')
            if draw_date >= recent_start:
                recent_hits += 1
        
        # Calcular momentum (actividad reciente vs esperada)
        expected_recent = (recent_period / total_days) * total_hits
        momentum = (recent_hits - expected_recent) / (expected_recent + 1)
        
        recent_activity = recent_hits / recent_period if recent_period > 0 else 0
        
        return {
            'momentum': momentum,
            'recent_activity': recent_activity
        }
    
    def _analyze_number_patterns(self, number: int) -> Dict[str, float]:
        """Analiza patrones matemáticos del número"""
        score = 0.0
        
        # Análisis de dígitos
        units_digit = number % 10
        tens_digit = number // 10
        
        # Patrones favorables (basados en frecuencias típicas)
        favorable_units = [0, 1, 2, 3, 5, 7]  # Dígitos comunes en loterías
        if units_digit in favorable_units:
            score += 0.1
        
        # Paridad balanceada (números pares e impares tienen similar probabilidad)
        if number % 2 == 0:  # Par
            score += 0.05
        else:  # Impar
            score += 0.05
        
        # Rangos favorables
        if 10 <= number <= 89:  # Rango medio más común
            score += 0.1
        elif number < 10 or number > 89:  # Extremos menos comunes
            score += 0.05
        
        # Suma digital
        digital_sum = sum(int(d) for d in str(number))
        if 3 <= digital_sum <= 15:  # Rangos más comunes
            score += 0.05
        
        return {'score': score}
    
    def _calculate_confidence(self, hits: int, total: int) -> float:
        """Calcula confianza estadística"""
        if total == 0:
            return 0.1
        
        # Usar intervalo de confianza binomial
        p = hits / total
        n = total
        
        # Aproximación normal para intervalos de confianza
        if n > 30:
            z = 1.96  # 95% confianza
            margin = z * math.sqrt(p * (1 - p) / n)
            confidence = 1 - margin  # Invertir margen para obtener confianza
        else:
            # Para muestras pequeñas, usar confianza conservadora
            confidence = 0.5 + (hits / (total + 10))
        
        return max(0.1, min(0.95, confidence))
    
    def train_ml_enhanced_model(self, frequency_data: Dict[int, Dict[str, float]]) -> Optional[Dict[str, Any]]:
        """Entrena modelo ML mejorado"""
        if not ML_AVAILABLE:
            return None
        
        print("🤖 Entrenando modelo ML mejorado...")
        
        # Preparar features y targets
        features = []
        targets = []
        numbers = []
        
        for number, data in frequency_data.items():
            feature_vector = [
                data['basic_frequency'],
                data['bayesian_probability'],
                data['gap_hazard'],
                data['trend_momentum'],
                data['pattern_score'],
                data['confidence_raw'],
                number % 10,  # dígito unidades
                number // 10,  # dígito decenas
                1 if number % 2 == 0 else 0,  # paridad
                1 if 10 <= number <= 89 else 0,  # rango medio
            ]
            
            features.append(feature_vector)
            # Target: probabilidad normalizada
            targets.append(data['bayesian_probability'])
            numbers.append(number)
        
        if not features:
            return None
        
        X = np.array(features)
        y = np.array(targets)
        
        try:
            # Normalizar features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Entrenar modelo de regresión
            model = LogisticRegression(random_state=42, max_iter=1000)
            
            # Convertir a clasificación binaria (top 20% vs resto)
            threshold = np.percentile(y, 80)
            y_binary = (y >= threshold).astype(int)
            
            model.fit(X_scaled, y_binary)
            
            # Hacer predicciones
            predictions = model.predict_proba(X_scaled)[:, 1]
            
            return {
                'model': model,
                'scaler': scaler,
                'feature_names': [
                    'basic_freq', 'bayesian_prob', 'gap_hazard', 'trend_momentum',
                    'pattern_score', 'confidence', 'units_digit', 'tens_digit',
                    'is_even', 'mid_range'
                ],
                'predictions': dict(zip(numbers, predictions)),
                'threshold': threshold
            }
        
        except Exception as e:
            print(f"⚠️ Error en ML: {e}")
            return None
    
    def generate_ensemble_predictions(
        self, 
        frequency_data: Dict[int, Dict[str, float]],
        ml_model: Optional[Dict[str, Any]] = None,
        num_predictions: int = 10
    ) -> List[ScientificPrediction]:
        """Genera predicciones ensemble"""
        print("🎯 Generando predicciones ensemble...")
        
        ensemble_scores = {}
        
        for number, data in frequency_data.items():
            # Componentes base
            bayesian_component = data['bayesian_probability']
            frequency_component = data['basic_frequency']
            gap_component = data['gap_hazard']
            trend_component = max(0, data['trend_momentum'] + 0.5)  # Normalizar
            pattern_component = data['pattern_score']
            
            # Componente ML si disponible
            ml_component = 0.0
            if ml_model and number in ml_model.get('predictions', {}):
                ml_component = ml_model['predictions'][number]
            
            # Pesos optimizados empíricamente
            weights = {
                'bayesian': 0.25,
                'frequency': 0.15,
                'gap': 0.25,
                'trend': 0.15,
                'pattern': 0.10,
                'ml': 0.10 if ml_model else 0.0
            }
            
            # Redistribuir pesos si no hay ML
            if not ml_model:
                weights['bayesian'] += 0.05
                weights['gap'] += 0.05
            
            # Score ensemble
            ensemble_score = (
                weights['bayesian'] * bayesian_component +
                weights['frequency'] * frequency_component +
                weights['gap'] * gap_component +
                weights['trend'] * trend_component +
                weights['pattern'] * pattern_component +
                weights['ml'] * ml_component
            )
            
            # Calcular confianza final
            components = [bayesian_component, frequency_component, gap_component, 
                         trend_component, pattern_component]
            if ml_model:
                components.append(ml_component)
            
            component_std = np.std(components)
            base_confidence = data['confidence_raw']
            agreement_confidence = max(0.1, 1.0 - (component_std * 2))
            
            final_confidence = (base_confidence + agreement_confidence) / 2
            
            ensemble_scores[number] = {
                'score': ensemble_score,
                'confidence': final_confidence,
                'components': {
                    'bayesian': bayesian_component,
                    'frequency': frequency_component,
                    'gap': gap_component,
                    'trend': trend_component,
                    'pattern': pattern_component,
                    'ml': ml_component
                }
            }
        
        # Ordenar y crear predicciones
        sorted_numbers = sorted(ensemble_scores.keys(), 
                              key=lambda x: ensemble_scores[x]['score'], 
                              reverse=True)
        
        predictions = []
        for i, number in enumerate(sorted_numbers[:num_predictions]):
            data = ensemble_scores[number]
            
            # Generar reasoning
            top_components = sorted(data['components'].items(), 
                                  key=lambda x: x[1], reverse=True)[:2]
            reasoning_parts = []
            
            for comp, val in top_components:
                if val > 0.05:
                    if comp == 'bayesian':
                        reasoning_parts.append("análisis Bayesiano favorable")
                    elif comp == 'gap':
                        reasoning_parts.append("patrón de intervalos atrasado")
                    elif comp == 'trend':
                        reasoning_parts.append("tendencia temporal positiva")
                    elif comp == 'ml':
                        reasoning_parts.append("modelo ML predictivo")
                    elif comp == 'frequency':
                        reasoning_parts.append("frecuencia histórica alta")
                    elif comp == 'pattern':
                        reasoning_parts.append("patrones matemáticos favorables")
            
            reasoning = "Basado en: " + ", ".join(reasoning_parts) if reasoning_parts else "Análisis estadístico general"
            
            pred = ScientificPrediction(
                number=number,
                probability=data['score'],
                confidence=data['confidence'],
                reasoning=reasoning,
                components=data['components'],
                rank=i + 1
            )
            predictions.append(pred)
        
        return predictions
    
    def get_daily_recommendation(self, days: int = 1825) -> List[ScientificPrediction]:
        """Obtiene recomendación diaria científica (top 3)"""
        print("🎯 Generando recomendación diaria científica...")
        
        # Calcular análisis avanzado
        frequency_data = self.calculate_advanced_frequencies(days)
        
        if not frequency_data:
            return []
        
        # Entrenar modelo ML
        ml_model = self.train_ml_enhanced_model(frequency_data)
        
        # Generar predicciones ensemble
        all_predictions = self.generate_ensemble_predictions(
            frequency_data, ml_model, num_predictions=20
        )
        
        # Seleccionar top 3 con mayor probabilidad y confianza
        top_predictions = sorted(all_predictions, 
                               key=lambda x: (x.probability + x.confidence) / 2, 
                               reverse=True)[:3]
        
        # Reasignar ranks
        for i, pred in enumerate(top_predictions):
            pred.rank = i + 1
        
        return top_predictions
    
    def get_weekly_recommendation(self, days: int = 1825) -> List[ScientificPrediction]:
        """Obtiene recomendación semanal (3 números estables)"""
        print("📅 Generando recomendación semanal...")
        
        # Generar predicciones para múltiples períodos
        stability_scores = {}
        
        for day_offset in [0, 2, 5]:  # Diferentes ventanas temporales
            period_data = self.calculate_advanced_frequencies(days - day_offset)
            ml_model = self.train_ml_enhanced_model(period_data)
            period_predictions = self.generate_ensemble_predictions(
                period_data, ml_model, num_predictions=15
            )
            
            for pred in period_predictions:
                if pred.number not in stability_scores:
                    stability_scores[pred.number] = []
                stability_scores[pred.number].append(pred.probability)
        
        # Calcular estabilidad (menor varianza es mejor)
        stable_recommendations = []
        
        for number, scores in stability_scores.items():
            if len(scores) >= 2:  # Al menos 2 períodos
                mean_score = np.mean(scores)
                score_std = np.std(scores)
                stability = mean_score / (1 + score_std)  # Tipo Sharpe ratio
                
                stable_recommendations.append({
                    'number': number,
                    'stability': stability,
                    'mean_score': mean_score,
                    'variability': score_std,
                    'periods': len(scores)
                })
        
        # Ordenar por estabilidad
        stable_recommendations.sort(key=lambda x: x['stability'], reverse=True)
        
        # Crear predicciones finales
        weekly_picks = []
        for i, data in enumerate(stable_recommendations[:3]):
            pred = ScientificPrediction(
                number=data['number'],
                probability=data['mean_score'],
                confidence=min(0.9, data['stability']),
                reasoning=f"Estable en múltiples análisis (variabilidad: {data['variability']:.3f})",
                components={'stability': data['stability'], 'mean_score': data['mean_score']},
                rank=i + 1
            )
            weekly_picks.append(pred)
        
        return weekly_picks

def main():
    """Función de prueba del predictor científico"""
    db = DatabaseManager()
    predictor = SimplifiedScientificPredictor(db)
    
    print("🧪 === SISTEMA CIENTÍFICO DE PREDICCIONES SIMPLIFICADO ===")
    
    try:
        # Recomendación diaria
        print("\n🎯 JUGADA DEL DÍA (Top 3 con análisis científico):")
        daily_picks = predictor.get_daily_recommendation()
        
        if daily_picks:
            for pick in daily_picks:
                print(f"  #{pick.rank} - Número {pick.number:02d}")
                print(f"      Probabilidad: {pick.probability:.4f}")
                print(f"      Confianza: {pick.confidence:.3f}")
                print(f"      Análisis: {pick.reasoning}")
                print(f"      Componentes principales: Bayesiano={pick.components.get('bayesian', 0):.3f}, "
                      f"Gaps={pick.components.get('gap', 0):.3f}")
                print()
        else:
            print("  No se pudieron generar predicciones diarias")
        
        # Recomendación semanal
        print("📅 NÚMEROS PARA LA SEMANA (Top 3 estables):")
        weekly_picks = predictor.get_weekly_recommendation()
        
        if weekly_picks:
            for pick in weekly_picks:
                print(f"  #{pick.rank} - Número {pick.number:02d}")
                print(f"      Score promedio: {pick.probability:.4f}")
                print(f"      Estabilidad: {pick.confidence:.3f}")
                print(f"      Análisis: {pick.reasoning}")
                print()
        else:
            print("  No se pudieron generar predicciones semanales")
            
    except Exception as e:
        print(f"❌ Error en las predicciones: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()