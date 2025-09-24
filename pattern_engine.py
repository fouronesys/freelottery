#!/usr/bin/env python3
"""
Pattern Engine - Sistema Avanzado de Análisis de Patrones para Quiniela Loteka
Identifica patrones secuenciales, cíclicos y de correlaciones en datos históricos
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter
import statistics
import math
import uuid
from scipy import stats
from scipy.fft import fft, fftfreq
import sqlite3
from database import DatabaseManager

class PatternEngine:
    """Motor de análisis de patrones avanzado para datos de quiniela"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.number_range = range(0, 100)
        
        # Configuración de detectores
        self.detectors = {
            'sequential': SequentialPatternDetector(db_manager),
            'cyclical': CyclicalPatternDetector(db_manager),
            'correlation': CorrelationPatternDetector(db_manager)
        }
        
        # Cache para optimización
        self._pattern_cache = {}
        self._cache_ttl = 3600  # 1 hora
        
        # Ventanas canónicas de análisis (como sugirió el architect)
        self.canonical_windows = [180, 365, 730, 1825]  # 5 años
        
    def compute_patterns(self, days: int = 1825) -> Dict[str, Any]:
        """
        Computa todos los tipos de patrones para una ventana de días
        
        Args:
            days: Días hacia atrás para análisis
            
        Returns:
            Dict con patrones identificados y sus métricas
        """
        
        cache_key = f"patterns_{days}"
        if self._is_cache_valid(cache_key):
            return self._pattern_cache[cache_key]['data']
        
        print(f"🔍 Analizando patrones en {days} días de datos...")
        
        # Generar batch ID único para esta ejecución
        batch_id = str(uuid.uuid4())
        
        # Obtener datos históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = {
            'window_days': days,
            'period_start': start_date.date().isoformat(),
            'period_end': end_date.date().isoformat(),
            'batch_id': batch_id,
            'patterns': {},
            'summary_stats': {}
        }
        
        # Desactivar patrones obsoletos antes de computar nuevos
        self._deactivate_old_patterns(days)
        
        # Ejecutar cada detector
        for pattern_type, detector in self.detectors.items():
            print(f"  🔬 Ejecutando detector {pattern_type}...")
            
            try:
                pattern_results = detector.detect_patterns(start_date, end_date)
                results['patterns'][pattern_type] = pattern_results
                
                # Persistir patrones identificados con batch_id
                self._persist_patterns(pattern_type, pattern_results, days, batch_id)
                
            except Exception as e:
                print(f"  ❌ Error en detector {pattern_type}: {e}")
                results['patterns'][pattern_type] = {'error': str(e)}
        
        # Calcular estadísticas de resumen
        results['summary_stats'] = self._calculate_summary_stats(results['patterns'])
        
        # Guardar batch_id para score_numbers
        results['current_batch_id'] = batch_id
        
        # Guardar en cache
        self._pattern_cache[cache_key] = {
            'data': results,
            'timestamp': datetime.now()
        }
        
        return results
    
    def score_numbers(self, days: int = 1825) -> Dict[int, Dict[str, Any]]:
        """
        Calcula puntuaciones basadas en patrones para todos los números
        
        Args:
            days: Días de análisis
            
        Returns:
            Dict {número: {score, confidence, details}}
        """
        
        # NO ejecutar compute_patterns automáticamente - usar patrones existentes
        # pattern_results = self.compute_patterns(days)  # DESHABILITADO para evitar bloqueo en CapRover
        # current_batch_id = pattern_results.get('current_batch_id')
        current_batch_id = None  # Se determinará de los patrones existentes
        
        # Obtener patrones activos del batch actual únicamente
        active_patterns = self.get_active_patterns(days, min_score=0.1, batch_id=current_batch_id)
        
        scores = {}
        
        # Inicializar todas las puntuaciones
        for number in self.number_range:
            scores[number] = {
                'score': 0.0,
                'confidence': 0.0,
                'pattern_contributions': {},
                'details': {}
            }
        
        # Combinar puntuaciones de todos los patrones activos
        for pattern_id, pattern_data in active_patterns.items():
            pattern_type = pattern_data['type']
            pattern_scores = pattern_data.get('number_scores', {})
            pattern_weight = self._get_pattern_weight(pattern_type, pattern_data)
            
            for number_str, number_score in pattern_scores.items():
                number = int(number_str)
                if number in scores:
                    contribution = number_score['score'] * pattern_weight
                    scores[number]['score'] += contribution
                    scores[number]['confidence'] += number_score['confidence'] * pattern_weight
                    scores[number]['pattern_contributions'][pattern_id] = contribution
                    
                    # Agregar detalles específicos del patrón
                    if pattern_type not in scores[number]['details']:
                        scores[number]['details'][pattern_type] = []
                    
                    scores[number]['details'][pattern_type].append({
                        'pattern_id': pattern_id,
                        'score': number_score['score'],
                        'confidence': number_score['confidence'],
                        'reasoning': number_score.get('reasoning', '')
                    })
        
        # Normalizar puntuaciones finales
        self._normalize_scores(scores)
        
        return scores
    
    def get_active_patterns(self, days: int = 1825, min_score: float = 0.1, batch_id: Optional[str] = None) -> Dict[int, Dict[str, Any]]:
        """
        Obtiene patrones activos con puntuación mínima del batch específico
        
        Args:
            days: Ventana de análisis
            min_score: Puntuación mínima para considerar patrón activo
            batch_id: ID del batch específico (si None, usa el más reciente)
            
        Returns:
            Dict con patrones activos
        """
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                if batch_id:
                    # Usar batch específico
                    cursor.execute("""
                    SELECT p.id, p.type, p.signature, p.window_days, p.strength_score, 
                           p.support_count, p.batch_id, p.created_at
                    FROM patterns p
                    WHERE p.status = 'active' 
                      AND p.window_days = ? 
                      AND p.strength_score >= ?
                      AND p.batch_id = ?
                    ORDER BY p.strength_score DESC
                    """, (days, min_score, batch_id))
                else:
                    # Usar el batch más reciente para esta ventana
                    cursor.execute("""
                    SELECT p.id, p.type, p.signature, p.window_days, p.strength_score, 
                           p.support_count, p.batch_id, p.created_at
                    FROM patterns p
                    WHERE p.status = 'active' 
                      AND p.window_days = ? 
                      AND p.strength_score >= ?
                      AND p.batch_id = (
                          SELECT batch_id FROM patterns 
                          WHERE window_days = ? AND status = 'active'
                          ORDER BY updated_at DESC LIMIT 1
                      )
                    ORDER BY p.strength_score DESC
                    """, (days, min_score, days))
                
                active_patterns = {}
                pattern_signatures = set()  # Para evitar duplicados por firma
                
                for row in cursor.fetchall():
                    pattern_id = row[0]
                    signature_json = row[2]
                    
                    # Evitar duplicados por firma
                    if signature_json in pattern_signatures:
                        continue
                    pattern_signatures.add(signature_json)
                    
                    pattern_data = {
                        'id': pattern_id,
                        'type': row[1],
                        'signature': json.loads(signature_json) if signature_json else {},
                        'window_days': row[3],
                        'strength_score': row[4],
                        'support_count': row[5],
                        'batch_id': row[6],
                        'created_at': row[7]
                    }
                    
                    # Obtener puntuaciones por número para este patrón
                    pattern_data['number_scores'] = self._get_pattern_number_scores(pattern_id)
                    
                    active_patterns[pattern_id] = pattern_data
                
                return active_patterns
                
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo patrones activos: {e}")
            return {}
    
    def _persist_patterns(self, pattern_type: str, pattern_results: Dict, window_days: int, batch_id: str):
        """Persiste patrones identificados en la base de datos"""
        
        if 'patterns' not in pattern_results:
            return
            
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                for pattern in pattern_results['patterns']:
                    signature_json = json.dumps(pattern.get('signature', {}))
                    
                    # Usar INSERT OR REPLACE para evitar duplicados
                    # Primero verificar si el patrón existe
                    cursor.execute("""
                    SELECT id FROM patterns 
                    WHERE type = ? AND signature = ? AND window_days = ?
                    """, (pattern_type, signature_json, window_days))
                    
                    existing_pattern = cursor.fetchone()
                    
                    if existing_pattern:
                        # Actualizar patrón existente
                        pattern_id = existing_pattern[0]
                        cursor.execute("""
                        UPDATE patterns 
                        SET strength_score = ?, support_count = ?, batch_id = ?, 
                            status = 'active', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """, (
                            pattern.get('strength', 0.0),
                            pattern.get('support', 0),
                            batch_id,
                            pattern_id
                        ))
                    else:
                        # Insertar nuevo patrón
                        cursor.execute("""
                        INSERT INTO patterns 
                        (type, signature, window_days, params, strength_score, support_count, 
                         batch_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            pattern_type,
                            signature_json,
                            window_days,
                            json.dumps(pattern.get('params', {})),
                            pattern.get('strength', 0.0),
                            pattern.get('support', 0),
                            batch_id
                        ))
                        pattern_id = cursor.lastrowid
                    
                    # El pattern_id ya está definido arriba
                    
                    # Limpiar puntuaciones anteriores para este patrón
                    cursor.execute("""
                    DELETE FROM pattern_scores WHERE pattern_id = ?
                    """, (pattern_id,))
                    
                    # Insertar nuevas puntuaciones por número
                    if 'number_scores' in pattern:
                        period_start = (datetime.now() - timedelta(days=window_days)).date()
                        period_end = datetime.now().date()
                        
                        for number_str, score_data in pattern['number_scores'].items():
                            cursor.execute("""
                            INSERT INTO pattern_scores
                            (pattern_id, number, score, confidence, period_start, period_end, 
                             details, computed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """, (
                                pattern_id,
                                int(number_str),
                                score_data.get('score', 0.0),
                                score_data.get('confidence', 0.0),
                                period_start,
                                period_end,
                                json.dumps(score_data.get('details', {}))
                            ))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"❌ Error persistiendo patrones {pattern_type}: {e}")
    
    def _deactivate_old_patterns(self, window_days: int):
        """Desactiva patrones obsoletos antes de computar nuevos"""
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Desactivar patrones antiguos (más de 24 horas)
                cursor.execute("""
                UPDATE patterns 
                SET status = 'inactive'
                WHERE window_days = ? 
                  AND status = 'active'
                  AND datetime(updated_at, '+24 hours') < datetime('now')
                """, (window_days,))
                
                deactivated_count = cursor.rowcount
                if deactivated_count > 0:
                    print(f"  🧹 Desactivados {deactivated_count} patrones obsoletos")
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"❌ Error desactivando patrones obsoletos: {e}")
    
    def _get_pattern_number_scores(self, pattern_id: int) -> Dict[str, Dict[str, Any]]:
        """Obtiene puntuaciones por número para un patrón específico"""
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT number, score, confidence, details
                FROM pattern_scores
                WHERE pattern_id = ?
                ORDER BY score DESC
                """, (pattern_id,))
                
                number_scores = {}
                for number, score, confidence, details_json in cursor.fetchall():
                    details = json.loads(details_json) if details_json else {}
                    number_scores[str(number)] = {
                        'score': score,
                        'confidence': confidence,
                        'details': details,
                        'reasoning': details.get('reasoning', '')
                    }
                
                return number_scores
                
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo puntuaciones del patrón {pattern_id}: {e}")
            return {}
    
    def _get_pattern_weight(self, pattern_type: str, pattern_data: Dict) -> float:
        """Calcula peso para un tipo de patrón basado en su efectividad"""
        
        base_weights = {
            'sequential': 0.4,  # Patrones de Markov son muy predictivos
            'cyclical': 0.3,   # Patrones temporales moderadamente útiles
            'correlation': 0.3 # Correlaciones útiles pero menos consistentes
        }
        
        base_weight = base_weights.get(pattern_type, 0.25)
        
        # Ajustar peso por fuerza del patrón
        strength_multiplier = min(1.5, 1.0 + pattern_data.get('strength_score', 0.0))
        
        # Ajustar peso por soporte (número de ocurrencias)
        support_count = pattern_data.get('support_count', 0)
        support_multiplier = min(1.3, 1.0 + support_count / 100)
        
        return base_weight * strength_multiplier * support_multiplier
    
    def _normalize_scores(self, scores: Dict[int, Dict[str, Any]]):
        """Normaliza las puntuaciones finales al rango [0, 100]"""
        
        all_scores = [data['score'] for data in scores.values()]
        if not all_scores or max(all_scores) == 0:
            return
        
        max_score = max(all_scores)
        
        for number in scores:
            # Normalizar puntuación principal
            scores[number]['score'] = (scores[number]['score'] / max_score) * 100
            
            # Limitar confianza al rango [0, 1]
            scores[number]['confidence'] = min(1.0, scores[number]['confidence'])
    
    def _calculate_summary_stats(self, patterns: Dict) -> Dict[str, Any]:
        """Calcula estadísticas de resumen para los patrones"""
        
        stats = {
            'total_patterns_detected': 0,
            'patterns_by_type': {},
            'average_strength': 0.0,
            'total_support': 0
        }
        
        all_strengths = []
        
        for pattern_type, pattern_results in patterns.items():
            if 'patterns' in pattern_results:
                type_count = len(pattern_results['patterns'])
                stats['patterns_by_type'][pattern_type] = type_count
                stats['total_patterns_detected'] += type_count
                
                # Recopilar fortalezas
                for pattern in pattern_results['patterns']:
                    strength = pattern.get('strength', 0.0)
                    support = pattern.get('support', 0)
                    all_strengths.append(strength)
                    stats['total_support'] += support
        
        if all_strengths:
            stats['average_strength'] = statistics.mean(all_strengths)
        
        return stats
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido"""
        if cache_key not in self._pattern_cache:
            return False
        
        cache_time = self._pattern_cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).seconds < self._cache_ttl
    
    def clear_cache(self):
        """Limpia el cache de patrones"""
        self._pattern_cache.clear()


class SequentialPatternDetector:
    """Detector de patrones secuenciales usando análisis de Markov"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.smoothing_factor = 0.01  # Suavizado de Laplace
    
    def detect_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Detecta patrones secuenciales en los datos"""
        
        # Obtener secuencias de números ganadores
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 100:  # Mínimo de datos requerido
            return {'patterns': [], 'error': 'Datos insuficientes'}
        
        # Construir cadenas de Markov de primer orden
        markov_matrix = self._build_markov_matrix(draws)
        
        # Identificar transiciones significativas
        patterns = self._identify_markov_patterns(markov_matrix, draws)
        
        return {
            'patterns': patterns,
            'markov_matrix_stats': {
                'non_zero_transitions': np.count_nonzero(markov_matrix),
                'total_possible_transitions': 100 * 100
            }
        }
    
    def _build_markov_matrix(self, draws: List[Tuple]) -> np.ndarray:
        """Construye matriz de transición de Markov"""
        
        # Organizar números por fecha
        daily_numbers = defaultdict(list)
        for draw in draws:
            date_str = str(draw[0])
            number = draw[1]
            daily_numbers[date_str].append(number)
        
        # Construir matriz de transiciones 100x100
        transition_counts = np.zeros((100, 100))
        
        # Obtener fechas ordenadas
        sorted_dates = sorted(daily_numbers.keys())
        
        # Contar transiciones entre días consecutivos
        for i in range(len(sorted_dates) - 1):
            current_date = sorted_dates[i]
            next_date = sorted_dates[i + 1]
            
            current_numbers = daily_numbers[current_date]
            next_numbers = daily_numbers[next_date]
            
            # Todas las transiciones posibles entre los números del día actual y siguiente
            for curr_num in current_numbers:
                for next_num in next_numbers:
                    transition_counts[curr_num][next_num] += 1
        
        # Aplicar suavizado de Laplace y normalizar
        transition_matrix = transition_counts + self.smoothing_factor
        
        # Normalizar filas para obtener probabilidades
        row_sums = transition_matrix.sum(axis=1, keepdims=True)
        transition_matrix = np.divide(transition_matrix, row_sums, 
                                    out=np.zeros_like(transition_matrix), 
                                    where=row_sums!=0)
        
        return transition_matrix
    
    def _identify_markov_patterns(self, markov_matrix: np.ndarray, draws: List[Tuple]) -> List[Dict[str, Any]]:
        """Identifica patrones significativos en la matriz de Markov"""
        
        patterns = []
        
        # Obtener números recientes para contexto
        recent_draws = draws[-7:]  # Últimos 7 sorteos
        recent_numbers = set(draw[1] for draw in recent_draws)
        
        # Encontrar transiciones con alta probabilidad
        for from_num in range(100):
            if from_num in recent_numbers:  # Solo considerar números recientes como contexto
                
                # Obtener probabilidades de transición desde este número
                transition_probs = markov_matrix[from_num]
                
                # Encontrar números con probabilidad significativamente alta
                mean_prob = np.mean(transition_probs)
                std_prob = np.std(transition_probs)
                threshold = mean_prob + 1.5 * std_prob  # Umbral estadístico
                
                high_prob_indices = np.where(transition_probs > threshold)[0]
                
                if len(high_prob_indices) > 0 and threshold > mean_prob * 1.2:
                    
                    # Crear patrón para esta transición
                    number_scores = {}
                    for to_num in high_prob_indices:
                        prob = transition_probs[to_num]
                        z_score = (prob - mean_prob) / std_prob if std_prob > 0 else 0
                        
                        number_scores[str(to_num)] = {
                            'score': prob * 100,  # Convertir a escala 0-100
                            'confidence': min(0.9, 0.3 + z_score * 0.1),
                            'details': {
                                'transition_probability': prob,
                                'z_score': z_score,
                                'from_number': from_num
                            },
                            'reasoning': f'Alta prob. transición desde {from_num} (p={prob:.3f})'
                        }
                    
                    pattern = {
                        'signature': {
                            'type': 'markov_transition',
                            'from_number': from_num,
                            'transition_count': len(high_prob_indices)
                        },
                        'strength': float(np.mean([transition_probs[i] for i in high_prob_indices])),
                        'support': int(np.sum(markov_matrix[from_num] > 0) * 100),  # Estimación del soporte
                        'number_scores': number_scores,
                        'params': {
                            'threshold': threshold,
                            'mean_prob': mean_prob
                        }
                    }
                    
                    patterns.append(pattern)
        
        return patterns


class CyclicalPatternDetector:
    """Detector de patrones cíclicos (días de la semana, meses, estacionalidad)"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def detect_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Detecta patrones cíclicos en los datos"""
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 200:
            return {'patterns': [], 'error': 'Datos insuficientes para análisis cíclico'}
        
        patterns = []
        
        # Detectar patrones de día de la semana
        weekday_patterns = self._detect_weekday_patterns(draws)
        patterns.extend(weekday_patterns)
        
        # Detectar patrones mensuales
        monthly_patterns = self._detect_monthly_patterns(draws)
        patterns.extend(monthly_patterns)
        
        return {'patterns': patterns}
    
    def _detect_weekday_patterns(self, draws: List[Tuple]) -> List[Dict[str, Any]]:
        """Detecta sesgos por día de la semana"""
        
        # Organizar por día de la semana
        weekday_numbers = defaultdict(list)
        
        for draw in draws:
            try:
                date_obj = datetime.strptime(str(draw[0]), '%Y-%m-%d')
                weekday = date_obj.weekday()  # 0 = Lunes, 6 = Domingo
                number = draw[1]
                weekday_numbers[weekday].append(number)
            except:
                continue
        
        patterns = []
        
        # Analizar cada número para sesgos de día de la semana
        for number in range(100):
            weekday_counts = {day: 0 for day in range(7)}
            weekday_totals = {day: 0 for day in range(7)}
            
            # Contar apariciones por día de la semana
            for weekday, numbers in weekday_numbers.items():
                weekday_totals[weekday] = len(numbers)
                weekday_counts[weekday] = numbers.count(number)
            
            # Calcular tasas por día de la semana
            weekday_rates = {}
            for day in range(7):
                if weekday_totals[day] > 0:
                    weekday_rates[day] = weekday_counts[day] / weekday_totals[day]
                else:
                    weekday_rates[day] = 0
            
            # Test chi-cuadrado para significancia estadística
            if sum(weekday_counts.values()) >= 10:  # Mínimo de apariciones
                
                # Calcular tasa global esperada
                total_appearances = sum(weekday_counts.values())
                total_draws = sum(weekday_totals.values())
                expected_rate = total_appearances / total_draws if total_draws > 0 else 0
                
                # Encontrar días con desviación significativa
                significant_days = []
                for day, rate in weekday_rates.items():
                    if weekday_totals[day] > 0 and rate > 0:
                        # Z-score para proporción
                        z_score = (rate - expected_rate) / math.sqrt(expected_rate * (1 - expected_rate) / weekday_totals[day])
                        
                        if abs(z_score) > 1.96:  # p < 0.05
                            significant_days.append({
                                'day': day,
                                'rate': rate,
                                'z_score': z_score,
                                'count': weekday_counts[day],
                                'total': weekday_totals[day]
                            })
                
                # Crear patrón si hay días significativos
                if significant_days:
                    # Calcular puntuación basada en el sesgo más fuerte
                    max_abs_z = max(abs(day['z_score']) for day in significant_days)
                    pattern_strength = min(1.0, max_abs_z / 3.0)  # Normalizar
                    
                    number_scores = {
                        str(number): {
                            'score': pattern_strength * 50,  # Escala 0-100
                            'confidence': min(0.8, 0.4 + pattern_strength * 0.4),
                            'details': {
                                'significant_days': significant_days,
                                'expected_rate': expected_rate,
                                'max_z_score': max_abs_z
                            },
                            'reasoning': f'Sesgo día semana (Z={max_abs_z:.2f})'
                        }
                    }
                    
                    pattern = {
                        'signature': {
                            'type': 'weekday_bias',
                            'number': number,
                            'significant_days': len(significant_days)
                        },
                        'strength': pattern_strength,
                        'support': total_appearances,
                        'number_scores': number_scores
                    }
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_monthly_patterns(self, draws: List[Tuple]) -> List[Dict[str, Any]]:
        """Detecta patrones estacionales por mes"""
        
        # Organizar por mes
        monthly_numbers = defaultdict(list)
        
        for draw in draws:
            try:
                date_obj = datetime.strptime(str(draw[0]), '%Y-%m-%d')
                month = date_obj.month
                number = draw[1]
                monthly_numbers[month].append(number)
            except:
                continue
        
        patterns = []
        
        # Analizar cada número para patrones mensuales
        for number in range(100):
            month_counts = {month: 0 for month in range(1, 13)}
            month_totals = {month: 0 for month in range(1, 13)}
            
            # Contar apariciones por mes
            for month, numbers in monthly_numbers.items():
                month_totals[month] = len(numbers)
                month_counts[month] = numbers.count(number)
            
            # Verificar si hay suficientes datos
            total_appearances = sum(month_counts.values())
            if total_appearances < 12:  # Mínimo de apariciones
                continue
            
            # Analizar variabilidad mensual usando coeficiente de variación
            month_rates = []
            for month in range(1, 13):
                if month_totals[month] > 0:
                    rate = month_counts[month] / month_totals[month]
                    month_rates.append(rate)
                else:
                    month_rates.append(0)
            
            if len(month_rates) > 0 and max(month_rates) > 0:
                cv = statistics.stdev(month_rates) / statistics.mean(month_rates) if statistics.mean(month_rates) > 0 else 0
                
                # Patrón significativo si coeficiente de variación es alto
                if cv > 0.5:  # Umbral para variabilidad significativa
                    
                    # Encontrar meses pico
                    max_rate = max(month_rates)
                    peak_months = [i+1 for i, rate in enumerate(month_rates) if rate > max_rate * 0.8]
                    
                    pattern_strength = min(1.0, cv)
                    
                    number_scores = {
                        str(number): {
                            'score': pattern_strength * 40,  # Escala más conservadora para patrones mensuales
                            'confidence': min(0.7, 0.3 + pattern_strength * 0.4),
                            'details': {
                                'coefficient_variation': cv,
                                'peak_months': peak_months,
                                'month_rates': {str(i+1): rate for i, rate in enumerate(month_rates)}
                            },
                            'reasoning': f'Patrón estacional (CV={cv:.2f})'
                        }
                    }
                    
                    pattern = {
                        'signature': {
                            'type': 'monthly_seasonal',
                            'number': number,
                            'peak_months': peak_months,
                            'coefficient_variation': cv
                        },
                        'strength': pattern_strength,
                        'support': total_appearances,
                        'number_scores': number_scores
                    }
                    
                    patterns.append(pattern)
        
        return patterns


class CorrelationPatternDetector:
    """Detector de patrones de correlación entre números"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def detect_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Detecta correlaciones entre números que aparecen juntos"""
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if len(draws) < 300:
            return {'patterns': [], 'error': 'Datos insuficientes para análisis de correlación'}
        
        patterns = []
        
        # Detectar co-ocurrencias en el mismo día
        cooccurrence_patterns = self._detect_cooccurrence_patterns(draws)
        patterns.extend(cooccurrence_patterns)
        
        return {'patterns': patterns}
    
    def _detect_cooccurrence_patterns(self, draws: List[Tuple]) -> List[Dict[str, Any]]:
        """Detecta números que tienden a aparecer juntos"""
        
        # Organizar números por fecha
        daily_numbers = defaultdict(set)
        
        for draw in draws:
            date_str = str(draw[0])
            number = draw[1]
            daily_numbers[date_str].add(number)
        
        # Calcular PMI (Pointwise Mutual Information) para pares de números
        total_days = len(daily_numbers)
        number_frequencies = Counter()
        pair_frequencies = Counter()
        
        # Contar frecuencias individuales y de pares
        for numbers in daily_numbers.values():
            numbers_list = list(numbers)
            
            # Contar números individuales
            for num in numbers_list:
                number_frequencies[num] += 1
            
            # Contar pares de números
            for i, num1 in enumerate(numbers_list):
                for num2 in numbers_list[i+1:]:
                    pair = tuple(sorted([num1, num2]))
                    pair_frequencies[pair] += 1
        
        patterns = []
        
        # Identificar correlaciones significativas
        for pair, joint_freq in pair_frequencies.items():
            if joint_freq >= 5:  # Mínimo de co-ocurrencias
                
                num1, num2 = pair
                freq1 = number_frequencies[num1]
                freq2 = number_frequencies[num2]
                
                # Calcular PMI
                prob_joint = joint_freq / total_days
                prob1 = freq1 / total_days
                prob2 = freq2 / total_days
                
                if prob1 > 0 and prob2 > 0:
                    pmi = math.log(prob_joint / (prob1 * prob2))
                    
                    # Solo considerar correlaciones positivas significativas
                    if pmi > 0.5:  # Umbral para correlación significativa
                        
                        # Test de significancia estadística
                        expected_joint = prob1 * prob2 * total_days
                        chi_square = ((joint_freq - expected_joint) ** 2) / expected_joint if expected_joint > 0 else 0
                        
                        if chi_square > 3.84:  # p < 0.05 para 1 grado de libertad
                            
                            strength = min(1.0, pmi / 2.0)  # Normalizar PMI
                            
                            # Crear puntuaciones para ambos números
                            number_scores = {}
                            
                            for target_num in [num1, num2]:
                                other_num = num2 if target_num == num1 else num1
                                
                                number_scores[str(target_num)] = {
                                    'score': strength * 35,  # Escala conservadora
                                    'confidence': min(0.75, 0.4 + strength * 0.35),
                                    'details': {
                                        'correlated_with': other_num,
                                        'pmi_score': pmi,
                                        'joint_frequency': joint_freq,
                                        'chi_square': chi_square
                                    },
                                    'reasoning': f'Correlación con {other_num} (PMI={pmi:.2f})'
                                }
                            
                            pattern = {
                                'signature': {
                                    'type': 'number_correlation',
                                    'numbers': list(pair),
                                    'pmi_score': pmi
                                },
                                'strength': strength,
                                'support': joint_freq,
                                'number_scores': number_scores,
                                'params': {
                                    'chi_square': chi_square,
                                    'p_value_estimate': 1 - stats.chi2.cdf(chi_square, 1)
                                }
                            }
                            
                            patterns.append(pattern)
        
        return patterns