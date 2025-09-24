#!/usr/bin/env python3
"""
Sistema Científico de Predicciones - Quiniela Loteka
Implementa análisis probabilístico, machine learning y validación temporal rigurosa
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional, Union
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
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.calibration import CalibratedClassifierCV, calibration_curve
    from sklearn.metrics import brier_score_loss, log_loss, precision_score
    from sklearn.preprocessing import StandardScaler
    from scipy import stats
    from scipy.optimize import minimize
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ Librerías de ML no disponibles, usando métodos estadísticos básicos")

from database import DatabaseManager
from analyzer import StatisticalAnalyzer

@dataclass
class PredictionResult:
    """Resultado de predicción científica"""
    number: int
    probability: float
    confidence: float
    reasoning: str
    components: Dict[str, float]
    rank: int

@dataclass
class ValidationMetrics:
    """Métricas de validación científica"""
    brier_score: float
    log_loss: float
    precision_at_3: float
    hit_rate_weekly: float
    calibration_slope: float
    calibration_intercept: float
    sample_size: int

class ScientificPredictor:
    """Predictor científico con análisis probabilístico y ML"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.analyzer = StatisticalAnalyzer(db_manager)
        self.number_range = range(0, 100)
        
        # Configuración de modelos
        self.models = {}
        self.feature_importance = {}
        self.calibration_data = {}
        
        # Cache de features
        self._feature_cache = {}
        self._cache_timeout = 3600  # 1 hora
        
        # Configuración de validación
        self.validation_window_days = 90
        self.min_training_days = 365
        
    def create_feature_panel(self, days: int = 1825) -> pd.DataFrame:
        """
        Crea panel de datos con feature engineering avanzado
        
        Para cada fecha-sorteo crea 100 filas (números 0-99) con features predictivos
        """
        print(f"🔬 Creando panel de features para {days} días...")
        
        # Obtener datos históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        draws = self.db.get_draws_in_period(start_date, end_date)
        if not draws:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df_draws = pd.DataFrame(draws, columns=['date', 'number', 'position', 'prize'])
        df_draws['date'] = pd.to_datetime(df_draws['date'])
        df_draws = df_draws.sort_values('date')
        
        # Crear panel base
        dates = df_draws['date'].dt.date.unique()
        numbers = list(self.number_range)
        
        # Panel completo: fecha x número
        panel_data = []
        
        for date in dates:
            date_draws = df_draws[df_draws['date'].dt.date == date]
            winning_numbers = set(date_draws['number'].tolist())
            
            for number in numbers:
                panel_data.append({
                    'date': date,
                    'number': number,
                    'hit': 1 if number in winning_numbers else 0
                })
        
        panel_df = pd.DataFrame(panel_data)
        panel_df['date'] = pd.to_datetime(panel_df['date'])
        panel_df = panel_df.sort_values(['date', 'number'])
        
        # Feature engineering
        panel_df = self._add_frequency_features(panel_df)
        panel_df = self._add_gap_features(panel_df)
        panel_df = self._add_trend_features(panel_df)
        panel_df = self._add_pattern_features(panel_df)
        panel_df = self._add_temporal_features(panel_df)
        
        return panel_df
    
    def _add_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade features de frecuencia con EWMA y SMA"""
        print("📊 Calculando features de frecuencia...")
        
        # Ventanas de análisis
        windows = [7, 30, 90, 180, 365]
        
        for number in self.number_range:
            number_mask = df['number'] == number
            number_data = df[number_mask].copy()
            
            if len(number_data) == 0:
                continue
                
            # Frecuencias en ventanas móviles
            for window in windows:
                window_size = min(window, len(number_data))
                
                # SMA (Simple Moving Average)
                sma_col = f'freq_sma_{window}'
                number_data[sma_col] = number_data['hit'].rolling(
                    window=window_size, min_periods=1
                ).mean()
                
                # EWMA (Exponentially Weighted Moving Average)
                ewma_col = f'freq_ewma_{window}'
                alpha = 2.0 / (window + 1)
                number_data[ewma_col] = number_data['hit'].ewm(alpha=alpha).mean()
                
                # Z-score de frecuencia
                zscore_col = f'freq_zscore_{window}'
                rolling_stats = number_data['hit'].rolling(
                    window=window_size, min_periods=1
                )
                mean_freq = rolling_stats.mean()
                std_freq = rolling_stats.std().fillna(0)
                number_data[zscore_col] = (
                    (number_data['hit'] - mean_freq) / (std_freq + 1e-8)
                )
            
            # Actualizar DataFrame principal
            df.loc[number_mask, [col for col in number_data.columns if col.startswith('freq_')]] = \
                number_data[[col for col in number_data.columns if col.startswith('freq_')]]
        
        return df
    
    def _add_gap_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade features de gaps con análisis Weibull"""
        print("⏱️ Calculando features de gaps...")
        
        for number in self.number_range:
            number_mask = df['number'] == number
            number_data = df[number_mask].copy()
            
            # Calcular gaps (días entre apariciones)
            hit_rows = number_data[number_data['hit'] == 1]
            hit_dates = hit_rows['date'].tolist()
            gaps = []
            
            if len(hit_dates) > 1:
                for i in range(1, len(hit_dates)):
                    gap_days = (hit_dates[i] - hit_dates[i-1]).days
                    gaps.append(gap_days)
            
            # Features de gaps
            last_gap = 0
            gap_mean = np.mean(gaps) if gaps else 30
            gap_median = np.median(gaps) if gaps else 30
            gap_std = np.std(gaps) if len(gaps) > 1 else 15
            
            # Días desde última aparición
            hit_rows = number_data[number_data['hit'] == 1]
            last_hit_indices = hit_rows.index.tolist()
            
            for i, idx in enumerate(number_data.index):
                if len(last_hit_indices) > 0:
                    recent_hits = [h for h in last_hit_indices if h <= idx]
                    if len(recent_hits) > 0:
                        days_since_last = i - (recent_hits[-1] - number_data.index[0])
                    else:
                        days_since_last = i
                else:
                    days_since_last = i
                
                # Hazard empírico (probabilidad condicional de aparecer)
                if gaps:
                    hazard_rate = 1.0 / (gap_mean + 1)
                    weibull_hazard = self._calculate_weibull_hazard(days_since_last, gaps)
                else:
                    hazard_rate = 0.01  # Default
                    weibull_hazard = 0.01
                
                # Asignar features usando iloc para evitar problemas de indexado
                row_position = list(number_data.index).index(idx)
                number_data.iloc[row_position, number_data.columns.get_loc('gap_last') if 'gap_last' in number_data.columns else len(number_data.columns)] = last_gap
                
            # Asignar features restantes después del loop
            for col_name, default_val in [('gap_last', 0), ('gap_mean', gap_mean), ('gap_median', gap_median), 
                                         ('gap_std', gap_std), ('hazard_empirical', 1.0/gap_mean if gap_mean > 0 else 0.01)]:
                if col_name not in number_data.columns:
                    number_data[col_name] = default_val
                    
            # Calcular días desde última aparición para cada fila
            days_since_vals = []
            last_hit_pos = -1
            for i, hit_val in enumerate(number_data['hit']):
                if hit_val == 1:
                    last_hit_pos = i
                    days_since_vals.append(0)
                else:
                    days_since_vals.append(i - last_hit_pos if last_hit_pos >= 0 else i)
                    
            number_data['days_since_last'] = days_since_vals
            number_data['hazard_weibull'] = [self._calculate_weibull_hazard(d, gaps) for d in days_since_vals]
        
        return df
    
    def _calculate_weibull_hazard(self, days_since: int, gaps: List[int]) -> float:
        """Calcula hazard rate usando distribución Weibull"""
        if not gaps or len(gaps) < 3:
            return 0.01
        
        try:
            # Ajustar Weibull a los gaps observados
            shape, loc, scale = stats.weibull_min.fit(gaps, floc=0)
            
            # Calcular hazard rate: h(t) = f(t) / S(t)
            # donde f(t) es PDF y S(t) es survival function
            pdf_val = stats.weibull_min.pdf(days_since, shape, loc, scale)
            survival_val = stats.weibull_min.sf(days_since, shape, loc, scale)
            
            if survival_val > 0:
                hazard = pdf_val / survival_val
            else:
                hazard = 0.0
                
            return min(hazard, 1.0)  # Cap at 1.0
        except:
            return 0.01
    
    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade features de tendencias y momentum"""
        print("📈 Calculando features de tendencias...")
        
        for number in self.number_range:
            number_mask = df['number'] == number
            number_data = df[number_mask].copy()
            
            # Momentum de apariciones (diferencia entre EWMA corta y larga)
            if len(number_data) > 0:
                ewma_short = number_data['hit'].ewm(span=7).mean()
                ewma_long = number_data['hit'].ewm(span=30).mean()
                momentum = ewma_short - ewma_long
            else:
                momentum = pd.Series([0] * len(number_data), index=number_data.index)
            
            # Tendencia en frecuencia
            window = min(30, len(number_data))
            if window > 5 and len(number_data) >= window:
                x = np.arange(window)
                recent_hits = number_data['hit'].tail(window).values
                if len(recent_hits) == window:
                    from scipy import stats
                    slope, _, _, _, _ = stats.linregress(x, recent_hits)
                else:
                    slope = 0.0
            else:
                slope = 0.0
            
            # Volatilidad de apariciones
            if len(number_data) > 0:
                volatility = number_data['hit'].rolling(window=14, min_periods=1).std()
            else:
                volatility = pd.Series([0] * len(number_data), index=number_data.index)
            
            # Asignar features
            df.loc[number_mask, 'momentum'] = momentum
            df.loc[number_mask, 'trend_slope'] = slope
            df.loc[number_mask, 'volatility'] = volatility.fillna(0)
        
        return df
    
    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade features de patrones matemáticos"""
        print("🔢 Calculando features de patrones...")
        
        # Features por número
        df['digit_units'] = df['number'] % 10
        df['digit_tens'] = df['number'] // 10
        df['is_even'] = (df['number'] % 2 == 0).astype(int)
        df['digital_root'] = df['number'].apply(lambda x: x if x < 10 else sum(int(d) for d in str(x)))
        
        # Rangos de números
        df['range_0_9'] = (df['number'] <= 9).astype(int)
        df['range_10_19'] = ((df['number'] >= 10) & (df['number'] <= 19)).astype(int)
        df['range_20_49'] = ((df['number'] >= 20) & (df['number'] <= 49)).astype(int)
        df['range_50_79'] = ((df['number'] >= 50) & (df['number'] <= 79)).astype(int)
        df['range_80_99'] = (df['number'] >= 80).astype(int)
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade features temporales"""
        print("📅 Calculando features temporales...")
        
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['day_of_month'] = df['date'].dt.day
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Encoding cíclico para temporales
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def implement_bayesian_baseline(self, panel_df: pd.DataFrame) -> Dict[str, Any]:
        """Implementa modelo Bayesiano base con Beta-Binomial"""
        print("🧮 Implementando modelo Bayesiano Beta-Binomial...")
        
        bayesian_probs = {}
        
        for number in self.number_range:
            number_data = panel_df[panel_df['number'] == number]
            
            if len(number_data) == 0:
                bayesian_probs[number] = 0.01
                continue
            
            # Prior Beta: asumimos distribución uniforme inicialmente
            alpha_prior = 1.0
            beta_prior = 1.0
            
            # Datos observados
            hits = number_data['hit'].sum()
            total = len(number_data)
            
            # Posterior Beta
            alpha_post = alpha_prior + hits
            beta_post = beta_prior + (total - hits)
            
            # Probabilidad Bayesiana (media del posterior)
            prob = alpha_post / (alpha_post + beta_post)
            
            bayesian_probs[number] = prob
        
        return bayesian_probs
    
    def train_ml_models(self, panel_df: pd.DataFrame) -> Dict[str, Any]:
        """Entrena modelos de ML con validación temporal"""
        if not ML_AVAILABLE:
            print("⚠️ Modelos ML no disponibles, usando baseline estadístico")
            return {}
        
        print("🤖 Entrenando modelos de Machine Learning...")
        
        # Preparar features
        feature_cols = [col for col in panel_df.columns 
                       if col not in ['date', 'number', 'hit'] and not col.startswith('temp_')]
        
        X = panel_df[feature_cols].fillna(0)
        y = panel_df['hit']
        dates = panel_df['date']
        
        # Validación temporal (walk-forward)
        models = {}
        validation_results = []
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=3)
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Normalizar features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # Entrenar modelos
            # 1. Regresión Logística
            log_reg = LogisticRegression(random_state=42, max_iter=1000)
            log_reg.fit(X_train_scaled, y_train)
            
            # 2. Random Forest
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_train, y_train)
            
            # Predicciones
            log_reg_probs = log_reg.predict_proba(X_val_scaled)[:, 1]
            rf_probs = rf.predict_proba(X_val)[:, 1]
            
            # Métricas
            val_metrics = {
                'brier_log_reg': brier_score_loss(y_val, log_reg_probs),
                'brier_rf': brier_score_loss(y_val, rf_probs),
                'log_loss_log_reg': log_loss(y_val, log_reg_probs),
                'log_loss_rf': log_loss(y_val, rf_probs)
            }
            
            validation_results.append(val_metrics)
        
        # Entrenar modelos finales en todos los datos
        scaler_final = StandardScaler()
        X_scaled_final = scaler_final.fit_transform(X)
        
        final_log_reg = LogisticRegression(random_state=42, max_iter=1000)
        final_log_reg.fit(X_scaled_final, y)
        
        final_rf = RandomForestClassifier(n_estimators=100, random_state=42)
        final_rf.fit(X, y)
        
        models = {
            'logistic_regression': final_log_reg,
            'random_forest': final_rf,
            'scaler': scaler_final,
            'feature_cols': feature_cols,
            'validation_results': validation_results
        }
        
        return models
    
    def create_ensemble_predictions(
        self, 
        bayesian_probs: Dict[int, float],
        ml_models: Dict[str, Any],
        panel_df: pd.DataFrame
    ) -> Dict[int, Dict[str, float]]:
        """Crea predicciones ensemble con calibración"""
        print("🎯 Creando predicciones ensemble...")
        
        ensemble_results = {}
        
        # Obtener último estado para predicciones
        latest_date = panel_df['date'].max()
        latest_data = panel_df[panel_df['date'] == latest_date]
        
        for number in self.number_range:
            number_data = latest_data[latest_data['number'] == number]
            
            if len(number_data) == 0:
                ensemble_results[number] = {
                    'bayesian': bayesian_probs.get(number, 0.01),
                    'ml_logistic': 0.01,
                    'ml_rf': 0.01,
                    'ensemble': 0.01,
                    'confidence': 0.1
                }
                continue
            
            # Predicción Bayesiana
            bayes_prob = bayesian_probs.get(number, 0.01)
            
            # Predicciones ML
            ml_logistic_prob = 0.01
            ml_rf_prob = 0.01
            
            if ML_AVAILABLE and ml_models:
                try:
                    feature_cols = ml_models['feature_cols']
                    features = number_data[feature_cols].fillna(0).values
                    
                    if len(features) > 0:
                        features_scaled = ml_models['scaler'].transform(features.reshape(1, -1))
                        ml_logistic_prob = ml_models['logistic_regression'].predict_proba(features_scaled)[0][1]
                        ml_rf_prob = ml_models['random_forest'].predict_proba(features.reshape(1, -1))[0][1]
                except Exception as e:
                    pass
            
            # Ensemble con pesos optimizados
            weights = {
                'bayesian': 0.30,
                'logistic': 0.35,
                'rf': 0.35
            }
            
            ensemble_prob = (
                weights['bayesian'] * bayes_prob +
                weights['logistic'] * ml_logistic_prob +
                weights['rf'] * ml_rf_prob
            )
            
            # Calcular confianza basada en acuerdo entre modelos
            probs = [bayes_prob, ml_logistic_prob, ml_rf_prob]
            prob_std = np.std(probs)
            confidence = max(0.1, 1.0 - (prob_std * 5))  # Invertir dispersión
            
            ensemble_results[number] = {
                'bayesian': bayes_prob,
                'ml_logistic': ml_logistic_prob,
                'ml_rf': ml_rf_prob,
                'ensemble': ensemble_prob,
                'confidence': confidence
            }
        
        return ensemble_results
    
    def generate_scientific_predictions(
        self,
        days: int = 1825,
        num_predictions: int = 10,
        confidence_threshold: float = 0.3
    ) -> List[PredictionResult]:
        """Genera predicciones científicas completas"""
        print(f"🔬 Generando predicciones científicas con {days} días de datos...")
        
        # 1. Crear panel de features
        panel_df = self.create_feature_panel(days)
        
        if panel_df.empty:
            return []
        
        # 2. Modelo Bayesiano baseline
        bayesian_probs = self.implement_bayesian_baseline(panel_df)
        
        # 3. Entrenar modelos ML
        ml_models = self.train_ml_models(panel_df)
        
        # 4. Crear ensemble
        ensemble_results = self.create_ensemble_predictions(bayesian_probs, ml_models, panel_df)
        
        # 5. Filtrar y ordenar predicciones
        predictions = []
        
        for number, results in ensemble_results.items():
            prob = results['ensemble']
            confidence = results['confidence']
            
            if confidence >= confidence_threshold:
                # Generar reasoning
                reasoning_parts = []
                if results['bayesian'] > 0.05:
                    reasoning_parts.append("frecuencia histórica favorable")
                if results['ml_logistic'] > 0.05:
                    reasoning_parts.append("patrón estadístico positivo")
                if results['ml_rf'] > 0.05:
                    reasoning_parts.append("características predictivas fuertes")
                
                reasoning = "Basado en: " + ", ".join(reasoning_parts) if reasoning_parts else "Análisis estadístico básico"
                
                pred = PredictionResult(
                    number=number,
                    probability=prob,
                    confidence=confidence,
                    reasoning=reasoning,
                    components=results,
                    rank=0  # Se asignará después
                )
                predictions.append(pred)
        
        # Ordenar por probabilidad y asignar ranks
        predictions.sort(key=lambda x: x.probability, reverse=True)
        for i, pred in enumerate(predictions[:num_predictions]):
            pred.rank = i + 1
        
        return predictions[:num_predictions]
    
    def get_daily_recommendation(self, days: int = 1825) -> List[PredictionResult]:
        """Obtiene recomendación diaria (top 3 números)"""
        predictions = self.generate_scientific_predictions(days, num_predictions=20, confidence_threshold=0.2)
        
        # Seleccionar top 3 con mayor probabilidad calibrada
        daily_picks = predictions[:3]
        
        return daily_picks
    
    def get_weekly_recommendation(self, days: int = 1825) -> List[PredictionResult]:
        """Obtiene recomendación semanal (3 números estables)"""
        # Generar predicciones para últimos 7 días
        weekly_probs = {}
        
        for day_offset in range(7):
            day_predictions = self.generate_scientific_predictions(days - day_offset, num_predictions=10)
            
            for pred in day_predictions:
                if pred.number not in weekly_probs:
                    weekly_probs[pred.number] = []
                weekly_probs[pred.number].append(pred.probability)
        
        # Calcular estabilidad (menor varianza es mejor)
        stable_numbers = []
        
        for number, probs in weekly_probs.items():
            if len(probs) >= 3:  # Al menos 3 apariciones en la semana
                mean_prob = np.mean(probs)
                std_prob = np.std(probs)
                stability_score = mean_prob / (1 + std_prob)  # Tipo Sharpe ratio
                
                stable_numbers.append({
                    'number': number,
                    'mean_prob': mean_prob,
                    'stability': stability_score,
                    'appearances': len(probs)
                })
        
        # Ordenar por estabilidad
        stable_numbers.sort(key=lambda x: x['stability'], reverse=True)
        
        # Crear resultados
        weekly_picks = []
        for i, data in enumerate(stable_numbers[:3]):
            pred = PredictionResult(
                number=data['number'],
                probability=data['mean_prob'],
                confidence=min(0.9, data['stability']),
                reasoning=f"Estable durante la semana ({data['appearances']} apariciones, baja varianza)",
                components={'stability': data['stability'], 'mean_prob': data['mean_prob']},
                rank=i + 1
            )
            weekly_picks.append(pred)
        
        return weekly_picks

def main():
    """Función de prueba"""
    db = DatabaseManager()
    predictor = ScientificPredictor(db)
    
    print("🧪 === SISTEMA CIENTÍFICO DE PREDICCIONES ===")
    
    # Recomendación diaria
    print("\n🎯 JUGADA DEL DÍA (Top 3):")
    daily_picks = predictor.get_daily_recommendation()
    
    for pick in daily_picks:
        print(f"  #{pick.rank} - Número {pick.number:02d}")
        print(f"      Probabilidad: {pick.probability:.3f}")
        print(f"      Confianza: {pick.confidence:.3f}")
        print(f"      Razón: {pick.reasoning}")
        print()
    
    # Recomendación semanal
    print("📅 NÚMEROS PARA LA SEMANA (Top 3 estables):")
    weekly_picks = predictor.get_weekly_recommendation()
    
    for pick in weekly_picks:
        print(f"  #{pick.rank} - Número {pick.number:02d}")
        print(f"      Probabilidad media: {pick.probability:.3f}")
        print(f"      Estabilidad: {pick.confidence:.3f}")
        print(f"      Razón: {pick.reasoning}")
        print()

if __name__ == "__main__":
    main()