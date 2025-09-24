#!/usr/bin/env python3
"""
Sistema de predicciones mejorado basado en el análisis avanzado de patrones
Integra múltiples factores predictivos para mayor precisión
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

class EnhancedLotteryPredictor:
    """Sistema de predicciones mejorado con análisis avanzado de patrones"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = StatisticalAnalyzer(db_manager)
        self.number_range = (0, 99)
        
        # Cargar patrones pre-analizados
        self.patterns = self._load_pattern_analysis()
        
        # Pesos mejorados basados en efectividad de patrones
        self.prediction_weights = {
            'frequency': 0.25,      # Reducido, frecuencia sola no es tan predictiva
            'gap_analysis': 0.30,   # Aumentado, números atrasados son buenos predictores
            'correlations': 0.25,   # Nuevo, correlaciones entre números
            'temporal': 0.10,       # Nuevo, patrones temporales
            'mathematical': 0.10    # Nuevo, patrones matemáticos/dígitos
        }
        
    def _load_pattern_analysis(self) -> Dict[str, Any]:
        """Carga los resultados del análisis de patrones"""
        try:
            with open('pattern_analysis_results.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Archivo de patrones no encontrado, usando análisis básico")
            return {}
    
    def generate_enhanced_predictions(
        self,
        days: int = 1825,  # ~5 años por defecto
        num_predictions: int = 10,
        confidence_threshold: float = 0.3
    ) -> List[Tuple[int, float, float, str]]:
        """
        Genera predicciones mejoradas usando múltiples factores
        
        Returns:
            List[Tuple]: [(numero, puntuacion, confianza, razon), ...]
        """
        
        print(f"🎯 Generando predicciones mejoradas con {days} días de datos...")
        
        # Obtener puntuaciones de diferentes métodos
        scores = defaultdict(float)
        confidence_scores = defaultdict(float)
        reasoning = defaultdict(list)
        
        # 1. Análisis de frecuencia tradicional (peso reducido)
        frequency_scores = self._calculate_frequency_scores(days)
        for number, score, confidence, reason in frequency_scores:
            scores[number] += score * self.prediction_weights['frequency']
            confidence_scores[number] += confidence * self.prediction_weights['frequency']
            reasoning[number].append(f"Freq: {reason[:30]}")
        
        # 2. Análisis de gaps (números atrasados) - NUEVO Y POTENTE
        gap_scores = self._calculate_gap_scores(days)
        for number, score, confidence, reason in gap_scores:
            scores[number] += score * self.prediction_weights['gap_analysis']
            confidence_scores[number] += confidence * self.prediction_weights['gap_analysis']
            reasoning[number].append(f"Gap: {reason[:30]}")
        
        # 3. Análisis de correlaciones - NUEVO
        correlation_scores = self._calculate_correlation_scores(days)
        for number, score, confidence, reason in correlation_scores:
            scores[number] += score * self.prediction_weights['correlations']
            confidence_scores[number] += confidence * self.prediction_weights['correlations']
            reasoning[number].append(f"Corr: {reason[:30]}")
        
        # 4. Análisis temporal - NUEVO
        temporal_scores = self._calculate_temporal_scores(days)
        for number, score, confidence, reason in temporal_scores:
            scores[number] += score * self.prediction_weights['temporal']
            confidence_scores[number] += confidence * self.prediction_weights['temporal']
            reasoning[number].append(f"Temp: {reason[:25]}")
        
        # 5. Análisis matemático/dígitos - NUEVO
        math_scores = self._calculate_mathematical_scores(days)
        for number, score, confidence, reason in math_scores:
            scores[number] += score * self.prediction_weights['mathematical']
            confidence_scores[number] += confidence * self.prediction_weights['mathematical']
            reasoning[number].append(f"Math: {reason[:25]}")
        
        # Compilar predicciones finales
        final_predictions = []
        for number in scores:
            final_score = scores[number]
            final_confidence = min(confidence_scores[number], 1.0)
            combined_reason = " | ".join(reasoning[number][:3])  # Top 3 razones
            
            if final_confidence >= confidence_threshold:
                final_predictions.append((number, final_score, final_confidence, combined_reason))
        
        # Ordenar por puntuación y limitar resultados
        final_predictions.sort(key=lambda x: x[1], reverse=True)
        
        print(f"✅ Generadas {len(final_predictions)} predicciones con confianza ≥ {confidence_threshold}")
        return final_predictions[:num_predictions]
    
    def _calculate_frequency_scores(self, days: int) -> List[Tuple[int, float, float, str]]:
        """Calcula puntuaciones basadas en frecuencia histórica"""
        
        all_frequencies = self.db.get_all_numbers_frequency(days)
        if not all_frequencies:
            return []
        
        scores = []
        frequencies = [freq for _, freq, _ in all_frequencies]
        mean_freq = statistics.mean(frequencies)
        std_freq = statistics.stdev(frequencies) if len(frequencies) > 1 else 0
        
        for number, abs_freq, rel_freq in all_frequencies:
            # Puntuación basada en frecuencia relativa
            base_score = rel_freq * 50
            
            # Bonus por estar por encima del promedio
            if abs_freq > mean_freq and std_freq > 0:
                z_score = (abs_freq - mean_freq) / std_freq
                base_score += z_score * 10
            
            # Confianza basada en consistencia
            confidence = min(0.8, rel_freq * 10 + 0.4)
            
            reason = f"{abs_freq} apariciones ({rel_freq:.1%})"
            scores.append((number, max(base_score, 0), confidence, reason))
        
        return scores
    
    def _calculate_gap_scores(self, days: int) -> List[Tuple[int, float, float, str]]:
        """Calcula puntuaciones basadas en análisis de gaps (intervalos)"""
        
        if 'gaps' not in self.patterns.get('patterns', {}):
            return []
        
        gap_data = self.patterns['patterns']['gaps']
        if 'error' in gap_data:
            return []
        
        scores = []
        overdue_numbers = gap_data.get('overdue_numbers', [])
        gap_statistics = gap_data.get('gap_statistics', {})
        
        # Procesar números atrasados (alta prioridad)
        for number, days_since, avg_gap in overdue_numbers:
            # Puntuación proporcional al retraso
            delay_ratio = days_since / avg_gap if avg_gap > 0 else 1
            base_score = min(delay_ratio * 30, 100)  # Máximo 100
            
            # Confianza basada en consistencia del patrón
            if number in gap_statistics:
                gap_stats = gap_statistics[str(number)]
                consistency = 1.0 / (1.0 + gap_stats.get('gap_std', 10) / gap_stats.get('average_gap', 10))
                confidence = min(0.9, consistency + 0.3)
            else:
                confidence = 0.7
            
            reason = f"Atrasado {days_since}d (prom: {avg_gap:.1f}d)"
            scores.append((number, base_score, confidence, reason))
        
        # Procesar números con patrones regulares (prioridad media)
        for number_str, stats in gap_statistics.items():
            try:
                number = int(number_str)
                if number not in [n for n, _, _ in overdue_numbers]:  # No duplicar atrasados
                    avg_gap = stats.get('average_gap', 0)
                    days_since = stats.get('days_since_last', 0)
                    
                    # Puntuación para números que están cerca de su tiempo normal
                    if avg_gap > 0:
                        proximity_score = max(0, 20 - abs(days_since - avg_gap))
                        confidence = 0.5 + min(0.3, proximity_score / 20 * 0.3)
                        
                        reason = f"Regular {days_since}d vs {avg_gap:.1f}d prom"
                        scores.append((number, proximity_score, confidence, reason))
            except:
                continue
        
        return scores
    
    def _calculate_correlation_scores(self, days: int) -> List[Tuple[int, float, float, str]]:
        """Calcula puntuaciones basadas en correlaciones entre números"""
        
        if 'correlations' not in self.patterns.get('patterns', {}):
            return []
        
        corr_data = self.patterns['patterns']['correlations']
        if 'error' in corr_data:
            return []
        
        strong_correlations = corr_data.get('strong_correlations', {})
        scores = []
        
        # Obtener números que han aparecido recientemente
        recent_days = min(30, days // 10)  # Últimos 30 días o 10% del período
        recent_date = datetime.now() - timedelta(days=recent_days)
        recent_draws = self.db.get_draws_in_period(recent_date, datetime.now())
        recent_numbers = set(draw[1] for draw in recent_draws)
        
        # Para cada correlación fuerte, dar puntuación a números correlacionados
        for pair_str, data in strong_correlations.items():
            try:
                num1, num2 = map(int, pair_str.split('-'))
                correlation = data['correlation']
                
                # Si uno de los números apareció recientemente, dar puntuación al otro
                if num1 in recent_numbers and num2 not in recent_numbers:
                    score = correlation * 40  # Escalado
                    confidence = min(0.8, correlation + 0.4)
                    reason = f"Correlación con {num1} (r={correlation:.2f})"
                    scores.append((num2, score, confidence, reason))
                
                elif num2 in recent_numbers and num1 not in recent_numbers:
                    score = correlation * 40
                    confidence = min(0.8, correlation + 0.4)
                    reason = f"Correlación con {num2} (r={correlation:.2f})"
                    scores.append((num1, score, confidence, reason))
                    
            except:
                continue
        
        return scores
    
    def _calculate_temporal_scores(self, days: int) -> List[Tuple[int, float, float, str]]:
        """Calcula puntuaciones basadas en patrones temporales"""
        
        if 'temporal' not in self.patterns.get('patterns', {}):
            return []
        
        temporal_data = self.patterns['patterns']['temporal']
        if 'error' in temporal_data:
            return []
        
        scores = []
        current_weekday = datetime.now().weekday()
        current_month = datetime.now().month
        
        weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        # Patrones de día de la semana
        weekday_patterns = temporal_data.get('weekday_patterns', {})
        current_weekday_name = weekday_names[current_weekday]
        
        if current_weekday_name in weekday_patterns:
            pattern_data = weekday_patterns[current_weekday_name]
            most_common = pattern_data.get('most_common', [])
            
            for number, count in most_common[:5]:  # Top 5 números del día
                # Puntuación basada en frecuencia en este día específico
                sample_size = pattern_data.get('sample_size', 1)
                frequency = count / sample_size
                score = frequency * 25
                confidence = min(0.7, frequency * 2 + 0.4)
                
                reason = f"Patrón {current_weekday_name}: {count}/{sample_size}"
                scores.append((number, score, confidence, reason))
        
        # Patrones estacionales (mes actual)
        seasonal_patterns = temporal_data.get('seasonal_patterns', {})
        current_month_name = month_names[current_month - 1]
        
        if current_month_name in seasonal_patterns:
            pattern_data = seasonal_patterns[current_month_name]
            most_common = pattern_data.get('most_common', [])
            
            for number, count in most_common[:3]:  # Top 3 números del mes
                sample_size = pattern_data.get('sample_size', 1)
                frequency = count / sample_size
                score = frequency * 15  # Menos peso que día de semana
                confidence = min(0.6, frequency * 1.5 + 0.3)
                
                reason = f"Patrón {current_month_name}: {count}/{sample_size}"
                scores.append((number, score, confidence, reason))
        
        return scores
    
    def _calculate_mathematical_scores(self, days: int) -> List[Tuple[int, float, float, str]]:
        """Calcula puntuaciones basadas en patrones matemáticos"""
        
        if 'digits' not in self.patterns.get('patterns', {}):
            return []
        
        digit_data = self.patterns['patterns']['digits']
        if 'error' in digit_data:
            return []
        
        scores = []
        
        # Patrones de dígitos
        digit_patterns = digit_data.get('digit_patterns', {})
        math_patterns = digit_data.get('mathematical_patterns', {})
        
        # Análisis de unidades más comunes
        units_most_common = digit_patterns.get('units_most_common', [])
        tens_most_common = digit_patterns.get('tens_most_common', [])
        
        # Dar puntuación a números con dígitos favorables
        favorable_units = set(digit for digit, _ in units_most_common[:3])
        favorable_tens = set(digit for digit, _ in tens_most_common[:3])
        
        for number in range(0, 100):
            unit_digit = number % 10
            ten_digit = number // 10
            
            score = 0
            reasons = []
            
            # Bonus por dígito de unidad favorable
            if unit_digit in favorable_units:
                score += 8
                reasons.append(f"Unidad {unit_digit} frecuente")
            
            # Bonus por dígito de decena favorable
            if ten_digit in favorable_tens:
                score += 8
                reasons.append(f"Decena {ten_digit} frecuente")
            
            # Bonus por paridad favorable
            parity_data = math_patterns.get('parity', {})
            if parity_data:
                even_ratio = parity_data.get('even_ratio', 0.5)
                if number % 2 == 0 and even_ratio > 0.55:  # Números pares favorecidos
                    score += 5
                    reasons.append("Par favorecido")
                elif number % 2 == 1 and even_ratio < 0.45:  # Números impares favorecidos
                    score += 5
                    reasons.append("Impar favorecido")
            
            if score > 0:
                confidence = min(0.6, score / 20 + 0.3)
                reason = " + ".join(reasons)
                scores.append((number, score, confidence, reason))
        
        return scores
    
    def generate_prediction_report(self, predictions: List[Tuple[int, float, float, str]]) -> Dict[str, Any]:
        """Genera un reporte detallado de las predicciones"""
        
        if not predictions:
            return {'error': 'No hay predicciones para reportar'}
        
        report = {
            'generation_time': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'methodology': 'Análisis multifactor mejorado',
            'factors_used': list(self.prediction_weights.keys()),
            'predictions': []
        }
        
        for i, (number, score, confidence, reason) in enumerate(predictions, 1):
            pred_data = {
                'rank': i,
                'number': number,
                'score': round(score, 2),
                'confidence': round(confidence, 3),
                'confidence_level': 'Alta' if confidence > 0.8 else 'Media' if confidence > 0.6 else 'Baja',
                'reasoning': reason,
                'recommendation': 'Fuerte' if confidence > 0.8 and score > 50 else 
                               'Moderada' if confidence > 0.6 and score > 30 else 'Débil'
            }
            report['predictions'].append(pred_data)
        
        # Estadísticas del reporte
        scores = [p[1] for p in predictions]
        confidences = [p[2] for p in predictions]
        
        report['statistics'] = {
            'average_score': round(statistics.mean(scores), 2),
            'average_confidence': round(statistics.mean(confidences), 3),
            'high_confidence_count': len([c for c in confidences if c > 0.8]),
            'score_range': f"{min(scores):.1f} - {max(scores):.1f}"
        }
        
        return report

def main():
    """Función de prueba del sistema mejorado"""
    
    print("🚀 SISTEMA DE PREDICCIONES MEJORADO")
    print("="*50)
    
    # Inicializar
    db = DatabaseManager()
    predictor = EnhancedLotteryPredictor(db)
    
    # Generar predicciones
    predictions = predictor.generate_enhanced_predictions(
        days=1825,  # ~5 años
        num_predictions=15,
        confidence_threshold=0.3
    )
    
    if predictions:
        print(f"\n🎯 TOP {len(predictions)} PREDICCIONES MEJORADAS:")
        print("-" * 70)
        
        for i, (number, score, confidence, reason) in enumerate(predictions, 1):
            confidence_icon = "🔥" if confidence > 0.8 else "⭐" if confidence > 0.6 else "📊"
            print(f"{i:2d}. {confidence_icon} Número {number:2d} | "
                  f"Score: {score:5.1f} | Confianza: {confidence:.1%} | {reason}")
        
        # Generar reporte
        report = predictor.generate_prediction_report(predictions)
        
        print(f"\n📊 ESTADÍSTICAS:")
        stats = report['statistics']
        print(f"   Score promedio: {stats['average_score']}")
        print(f"   Confianza promedio: {stats['average_confidence']:.1%}")
        print(f"   Predicciones alta confianza: {stats['high_confidence_count']}")
        
        # Guardar reporte
        with open('enhanced_predictions.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: enhanced_predictions.json")
    else:
        print("❌ No se pudieron generar predicciones")

if __name__ == "__main__":
    main()