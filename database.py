import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import os

class DatabaseManager:
    """Gestiona la base de datos SQLite para almacenar resultados de lotería"""
    
    def __init__(self, db_path: str = "quiniela_loteka.db"):
        self.db_path = db_path
        self.init_database()
        self._optimize_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Tabla principal de resultados
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS draw_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    number INTEGER NOT NULL,
                    position INTEGER,
                    draw_type TEXT DEFAULT 'quiniela',
                    prize_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, number, position)
                )
                """)
                
                # Tabla de metadatos
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Tabla de predicciones de usuarios
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    predicted_numbers TEXT NOT NULL,
                    prediction_method TEXT,
                    confidence_threshold REAL,
                    analysis_days INTEGER,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT
                )
                """)
                
                # Tabla de notificaciones
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    prediction_id INTEGER,
                    winning_number INTEGER NOT NULL,
                    winning_date DATE NOT NULL,
                    winning_position INTEGER,
                    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    notification_message TEXT,
                    FOREIGN KEY (prediction_id) REFERENCES user_predictions (id),
                    UNIQUE(user_id, prediction_id, winning_number, winning_date, winning_position)
                )
                """)
                
                # Índices para mejorar rendimiento
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date ON draw_results(date)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_number ON draw_results(number)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_number ON draw_results(date, number)
                """)
                
                # Índices para tablas de predicciones y notificaciones
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_predictions_user_id ON user_predictions(user_id)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_predictions_active ON user_predictions(is_active)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)
                """)
                
                # Crear índice único para prevenir duplicados en bases de datos existentes
                cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_notifications_unique 
                ON notifications(user_id, prediction_id, winning_number, winning_date, winning_position)
                """)
                
                # Tabla de predicciones del sistema
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    predicted_numbers TEXT NOT NULL,
                    prediction_method TEXT,
                    confidence_threshold REAL,
                    analysis_days INTEGER,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT
                )
                """)
                
                # Tabla de notificaciones generales del sistema
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    winning_number INTEGER NOT NULL,
                    winning_date DATE NOT NULL,
                    winning_position INTEGER,
                    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    notification_message TEXT,
                    success_rate REAL,
                    FOREIGN KEY (prediction_id) REFERENCES system_predictions (id),
                    UNIQUE(prediction_id, winning_number, winning_date, winning_position)
                )
                """)
                
                # Índices para las nuevas tablas del sistema
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_predictions_date ON system_predictions(prediction_date)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_predictions_active ON system_predictions(is_active)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_notifications_date ON system_notifications(matched_at)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_notifications_read ON system_notifications(is_read)
                """)
                
                # ===== NUEVAS TABLAS PARA ANÁLISIS DE PATRONES =====
                
                # Tabla de patrones identificados
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL, -- 'sequential', 'cyclical', 'correlation'
                    signature TEXT NOT NULL, -- JSON con detalles del patrón
                    window_days INTEGER NOT NULL,
                    params TEXT, -- JSON con parámetros de configuración
                    status TEXT DEFAULT 'active', -- 'active', 'inactive', 'testing'
                    strength_score REAL DEFAULT 0.0,
                    support_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Tabla de puntuaciones por patrón y número
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    details TEXT, -- JSON con información adicional
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES patterns (id),
                    UNIQUE(pattern_id, number, period_start, period_end)
                )
                """)
                
                # Tabla de métricas de evaluación de patrones
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    baseline_value REAL,
                    uplift REAL,
                    p_value REAL,
                    backtest_window_days INTEGER,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES patterns (id),
                    UNIQUE(pattern_id, metric_name, backtest_window_days)
                )
                """)
                
                # Tabla de ocurrencias de patrones
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    occurred_at DATE NOT NULL,
                    context TEXT, -- JSON con contexto de la ocurrencia
                    strength REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES patterns (id)
                )
                """)
                
                # Índices para optimizar consultas de patrones
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(type)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_window ON patterns(window_days)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_status ON patterns(status)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_scores_number ON pattern_scores(number)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_scores_period ON pattern_scores(period_start, period_end)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_metrics_pattern ON pattern_metrics(pattern_id)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_date ON pattern_occurrences(occurred_at)
                """)
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error inicializando base de datos: {e}")
            raise
    
    def _optimize_database(self):
        """Optimiza la configuración de SQLite para mejor rendimiento"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Configuraciones de rendimiento para SQLite
                conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging para mejor concurrencia
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance entre rendimiento y seguridad
                conn.execute("PRAGMA cache_size=10000")  # Cache más grande (10MB)
                conn.execute("PRAGMA temp_store=MEMORY")  # Usar memoria para temporales
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB de memory mapping
                conn.execute("PRAGMA foreign_keys=ON")  # Asegurar integridad referencial
                
        except sqlite3.Error as e:
            print(f"Error optimizando base de datos: {e}")
    
    def save_draw_result(self, result: Dict[str, Any]) -> bool:
        """
        Guarda un resultado de sorteo SOLO de Quiniela Loteka
        
        Args:
            result: Diccionario con 'date', 'number', 'position', 'prize_amount', 'draw_type'
        
        Returns:
            bool: True si se guardó exitosamente, False si ya existía o fue rechazado
        """
        try:
            # VALIDACIÓN CRÍTICA: Solo aceptar datos de Quiniela Loteka
            draw_type = result.get('draw_type', 'quiniela')
            if draw_type != 'quiniela':
                print(f"❌ RECHAZADO: Tipo de sorteo no permitido '{draw_type}'. Solo se acepta 'quiniela'")
                return False
                
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT OR IGNORE INTO draw_results 
                (date, number, position, draw_type, prize_amount)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    result['date'],
                    result['number'],
                    result.get('position', 1),
                    'quiniela',  # FORZAR siempre 'quiniela'
                    result.get('prize_amount', 0)
                ))
                
                # Actualizar metadatos de última actualización
                cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES ('last_update', ?, CURRENT_TIMESTAMP)
                """, (datetime.now().isoformat(),))
                
                conn.commit()
                was_inserted = cursor.rowcount > 0
                
                # Si se insertó un nuevo resultado, verificar coincidencias con predicciones
                if was_inserted:
                    self._check_new_draw_for_matches(result)
                    self._check_new_draw_for_system_matches(result)
                
                return was_inserted
                
        except sqlite3.Error as e:
            print(f"Error guardando resultado: {e}")
            return False
    
    def get_draws_in_period(self, start_date: datetime, end_date: datetime) -> List[Tuple]:
        """Obtiene todos los sorteos en un período específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT date, number, position, prize_amount
                FROM draw_results
                WHERE date BETWEEN ? AND ? AND draw_type = 'quiniela'
                ORDER BY date DESC, position
                """, (start_date.date(), end_date.date()))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            print(f"Error obteniendo sorteos: {e}")
            return []
    
    def save_multiple_draw_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Guarda múltiples resultados de sorteo de manera eficiente (batch saving)
        
        Args:
            results: Lista de diccionarios con datos de sorteos
            
        Returns:
            int: Número de registros guardados exitosamente
        """
        if not results:
            return 0
            
        saved_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Preparar datos para inserción batch
                batch_data = []
                for result in results:
                    # Validar que sea quiniela
                    draw_type = result.get('draw_type', 'quiniela')
                    if draw_type != 'quiniela':
                        print(f"⚠️ Omitiendo resultado no-quiniela: {draw_type}")
                        continue
                        
                    batch_data.append((
                        result['date'],
                        result['number'],
                        result.get('position', 1),
                        'quiniela',  # Forzar quiniela
                        result.get('prize_amount', 0)
                    ))
                
                if not batch_data:
                    print("❌ No hay datos válidos para guardar")
                    return 0
                
                # Inserción batch usando executemany
                cursor.executemany("""
                INSERT OR IGNORE INTO draw_results 
                (date, number, position, draw_type, prize_amount)
                VALUES (?, ?, ?, ?, ?)
                """, batch_data)
                
                saved_count = cursor.rowcount
                
                # Actualizar metadatos
                cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES ('last_update', ?, CURRENT_TIMESTAMP)
                """, (datetime.now().isoformat(),))
                
                cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at) 
                VALUES ('total_records', (SELECT COUNT(*) FROM draw_results), CURRENT_TIMESTAMP)
                """)
                
                conn.commit()
                
                print(f"✅ Guardados exitosamente {saved_count} de {len(batch_data)} registros")
                
        except sqlite3.Error as e:
            print(f"❌ Error guardando múltiples resultados: {e}")
            saved_count = 0
            
        return saved_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos
        
        Returns:
            Dict con estadísticas de datos disponibles
        """
        stats = {
            'total_records': 0,
            'unique_dates': 0,
            'date_range_days': 0,
            'earliest_date': None,
            'latest_date': None,
            'has_720_days': False
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de registros
                cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type = 'quiniela'")
                stats['total_records'] = cursor.fetchone()[0]
                
                if stats['total_records'] > 0:
                    # Fechas únicas
                    cursor.execute("SELECT COUNT(DISTINCT date) FROM draw_results WHERE draw_type = 'quiniela'")
                    stats['unique_dates'] = cursor.fetchone()[0]
                    
                    # Rango de fechas
                    cursor.execute("""
                    SELECT MIN(date), MAX(date) FROM draw_results WHERE draw_type = 'quiniela'
                    """)
                    earliest, latest = cursor.fetchone()
                    
                    if earliest and latest:
                        stats['earliest_date'] = earliest
                        stats['latest_date'] = latest
                        
                        # Calcular días entre fechas
                        start = datetime.strptime(earliest, '%Y-%m-%d')
                        end = datetime.strptime(latest, '%Y-%m-%d')
                        stats['date_range_days'] = (end - start).days
                        stats['has_720_days'] = stats['date_range_days'] >= 720
                        
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            
        return stats
    
    def get_number_frequency(self, number: int, days: int = 180) -> Tuple[int, float]:
        """
        Obtiene la frecuencia de un número específico
        
        Returns:
            Tuple[int, float]: (frecuencia_absoluta, frecuencia_relativa)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Frecuencia absoluta
                cursor.execute("""
                SELECT COUNT(*) FROM draw_results
                WHERE number = ? AND date >= ? AND draw_type = 'quiniela'
                """, (number, cutoff_date.date()))
                
                absolute_freq = cursor.fetchone()[0]
                
                # Total de sorteos
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ? AND draw_type = 'quiniela'
                """, (cutoff_date.date(),))
                
                total_draws = cursor.fetchone()[0]
                
                relative_freq = absolute_freq / total_draws if total_draws > 0 else 0
                
                return absolute_freq, relative_freq
                
        except sqlite3.Error as e:
            print(f"Error calculando frecuencia: {e}")
            return 0, 0.0
    
    def get_all_numbers_frequency(self, days: int = 180) -> List[Tuple[int, int, float]]:
        """
        Obtiene la frecuencia de todos los números
        
        Returns:
            List[Tuple]: [(numero, frecuencia_absoluta, frecuencia_relativa), ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Total de sorteos únicos en el período
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ? AND draw_type = 'quiniela'
                """, (cutoff_date.date(),))
                
                total_draws = cursor.fetchone()[0]
                
                if total_draws == 0:
                    return []
                
                # Frecuencia por número
                cursor.execute("""
                SELECT number, COUNT(*) as frequency
                FROM draw_results
                WHERE date >= ? AND draw_type = 'quiniela'
                GROUP BY number
                ORDER BY frequency DESC
                """, (cutoff_date.date(),))
                
                results = []
                for number, freq in cursor.fetchall():
                    relative_freq = freq / total_draws
                    results.append((number, freq, relative_freq))
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo frecuencias: {e}")
            return []
    
    def get_total_draws(self) -> int:
        """Obtiene el número total de registros de sorteos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type = 'quiniela'")
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def get_unique_dates_count(self) -> int:
        """Obtiene el número de días únicos con datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT date) FROM draw_results WHERE draw_type = 'quiniela'")
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def get_draws_count_last_days(self, days: int) -> int:
        """Obtiene el número de sorteos en los últimos N días"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ? AND draw_type = 'quiniela'
                """, (cutoff_date.date(),))
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def get_numbers_by_position(self, days: int = 180) -> List[Dict[str, Any]]:
        """
        Obtiene números organizados por posición (1ra, 2da, 3ra)
        
        Args:
            days: Número de días hacia atrás para el análisis
        
        Returns:
            List[Dict]: [{'date': str, 'number': int, 'position': int}, ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                SELECT date, number, position
                FROM draw_results
                WHERE date >= ? AND position IS NOT NULL AND draw_type = 'quiniela'
                ORDER BY date DESC, position
                """, (cutoff_date.date(),))
                
                results = []
                for date, number, position in cursor.fetchall():
                    results.append({
                        'date': date,
                        'number': number,
                        'position': position
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo números por posición: {e}")
            return []

    def get_data_coverage_days(self) -> int:
        """Obtiene el número de días cubiertos por los datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("""
                SELECT 
                    julianday(MAX(date)) - julianday(MIN(date)) + 1 as days_coverage
                FROM draw_results
                """)
                result = cursor.fetchone()[0]
                return int(result) if result else 0
        except sqlite3.Error:
            return 0
    
    def get_last_update_date(self) -> Optional[datetime]:
        """Obtiene la fecha de la última actualización"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("""
                SELECT value FROM metadata WHERE key = 'last_update'
                """)
                result = cursor.fetchone()
                if result:
                    return datetime.fromisoformat(result[0])
                return None
        except (sqlite3.Error, ValueError):
            return None
    
    def get_recent_draws(self, limit: int = 10) -> List[Tuple]:
        """Obtiene los sorteos más recientes de Quiniela"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("""
                SELECT date, number, position, prize_amount
                FROM draw_results
                WHERE draw_type = 'quiniela'
                ORDER BY date DESC, position
                LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def get_numbers_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Tuple]:
        """Obtiene números en un rango de fechas específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("""
                SELECT date, number FROM draw_results
                WHERE date BETWEEN ? AND ?
                ORDER BY date, position
                """, (start_date.date(), end_date.date()))
                return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def get_draws_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Tuple[str, int, str]]:
        """
        Obtiene sorteos en un rango de fechas específico para análisis de co-ocurrencia
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            List[Tuple[str, int, str]]: [(date_str, number, date_str), ...] 
            donde date_str sirve como draw_id (agrupando por fecha de sorteo)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("""
                SELECT date, number FROM draw_results
                WHERE date BETWEEN ? AND ?
                ORDER BY date, position
                """, (start_date.date(), end_date.date()))
                rows = cursor.fetchall()
                # Convertir (date, number) a (date_str, number, date_str) para compatibilidad
                return [(str(date), number, str(date)) for date, number in rows]
        except sqlite3.Error:
            return []
    
    def get_unique_numbers(self) -> List[int]:
        """Obtiene todos los números únicos que han salido"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT number FROM draw_results WHERE draw_type = 'quiniela' ORDER BY number")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Limpia datos antiguos para mantener la base de datos optimizada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                cursor.execute("""
                DELETE FROM draw_results WHERE date < ?
                """, (cutoff_date.date(),))
                
                deleted = cursor.rowcount
                conn.commit()
                
                # Optimizar base de datos
                cursor.execute("VACUUM")
                
                return deleted
                
        except sqlite3.Error as e:
            print(f"Error limpiando datos: {e}")
            return 0
    
    # === MÉTODOS PARA GESTIÓN DE PREDICCIONES DE USUARIOS ===
    
    def save_user_prediction(self, user_id: str, predicted_numbers: List[int], 
                           prediction_method: Optional[str] = None, confidence_threshold: Optional[float] = None,
                           analysis_days: Optional[int] = None, notes: Optional[str] = None) -> int:
        """
        Guarda una predicción de usuario en la base de datos
        
        Args:
            user_id: Identificador del usuario
            predicted_numbers: Lista de números predichos
            prediction_method: Método usado para la predicción
            confidence_threshold: Umbral de confianza usado
            analysis_days: Días de análisis usados
            notes: Notas adicionales del usuario
            
        Returns:
            int: ID de la predicción guardada, 0 si hay error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Convertir lista de números a string separado por comas
                numbers_str = ','.join(map(str, predicted_numbers))
                
                cursor.execute("""
                INSERT INTO user_predictions 
                (user_id, predicted_numbers, prediction_method, confidence_threshold, 
                 analysis_days, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, numbers_str, prediction_method, confidence_threshold, 
                      analysis_days, notes))
                
                conn.commit()
                return cursor.lastrowid or 0
                
        except sqlite3.Error as e:
            print(f"Error guardando predicción: {e}")
            return 0
    
    def get_user_predictions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene las predicciones de un usuario
        
        Args:
            user_id: Identificador del usuario
            active_only: Si solo obtener predicciones activas
            
        Returns:
            List[Dict]: Lista de predicciones del usuario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                query = """
                SELECT id, predicted_numbers, prediction_method, confidence_threshold,
                       analysis_days, prediction_date, is_active, notes
                FROM user_predictions
                WHERE user_id = ?
                """
                
                params = [user_id]
                
                if active_only:
                    query += " AND is_active = 1"
                
                query += " ORDER BY prediction_date DESC"
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    # Convertir string de números de vuelta a lista
                    numbers_list = [int(x.strip()) for x in row[1].split(',') if x.strip()]
                    
                    results.append({
                        'id': row[0],
                        'predicted_numbers': numbers_list,
                        'prediction_method': row[2],
                        'confidence_threshold': row[3],
                        'analysis_days': row[4],
                        'prediction_date': row[5],
                        'is_active': bool(row[6]),
                        'notes': row[7]
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo predicciones: {e}")
            return []
    
    def deactivate_user_prediction(self, prediction_id: int) -> bool:
        """
        Desactiva una predicción de usuario
        
        Args:
            prediction_id: ID de la predicción a desactivar
            
        Returns:
            bool: True si se desactivó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                UPDATE user_predictions 
                SET is_active = 0 
                WHERE id = ?
                """, (prediction_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error desactivando predicción: {e}")
            return False
    
    def get_all_active_predictions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las predicciones activas de todos los usuarios
        
        Returns:
            List[Dict]: Lista de todas las predicciones activas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT id, user_id, predicted_numbers, prediction_method, 
                       confidence_threshold, analysis_days, prediction_date, notes
                FROM user_predictions
                WHERE is_active = 1
                ORDER BY prediction_date DESC
                """)
                
                results = []
                for row in cursor.fetchall():
                    # Convertir string de números de vuelta a lista
                    numbers_list = [int(x.strip()) for x in row[2].split(',') if x.strip()]
                    
                    results.append({
                        'id': row[0],
                        'user_id': row[1],
                        'predicted_numbers': numbers_list,
                        'prediction_method': row[3],
                        'confidence_threshold': row[4],
                        'analysis_days': row[5],
                        'prediction_date': row[6],
                        'notes': row[7]
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo predicciones activas: {e}")
            return []
    
    # === MÉTODOS PARA GESTIÓN DE NOTIFICACIONES ===
    
    def create_notification(self, user_id: str, prediction_id: int, winning_number: int,
                          winning_date: str, winning_position: Optional[int] = None) -> int:
        """
        Crea una notificación cuando una predicción coincide con un número ganador
        
        Args:
            user_id: Identificador del usuario
            prediction_id: ID de la predicción que coincidió
            winning_number: Número ganador que coincidió
            winning_date: Fecha del sorteo ganador
            winning_position: Posición del número ganador (1ra, 2da, 3ra)
            
        Returns:
            int: ID de la notificación creada, 0 si hay error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Crear mensaje personalizado
                position_text = ""
                if winning_position:
                    positions = {1: "1ra", 2: "2da", 3: "3ra"}
                    position_text = f" en {positions.get(winning_position, str(winning_position))} posición"
                
                message = f"¡Felicitaciones! Tu predicción del número {winning_number} coincidió con el sorteo del {winning_date}{position_text}."
                
                cursor.execute("""
                INSERT OR IGNORE INTO notifications 
                (user_id, prediction_id, winning_number, winning_date, 
                 winning_position, notification_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, prediction_id, winning_number, winning_date, 
                      winning_position, message))
                
                conn.commit()
                # Si rowcount es 0, significa que no se insertó (ya existía)
                if cursor.rowcount > 0:
                    return cursor.lastrowid or 0
                else:
                    return 0  # Ya existía la notificación
                
        except sqlite3.Error as e:
            print(f"Error creando notificación: {e}")
            return 0
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False, 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene las notificaciones de un usuario
        
        Args:
            user_id: Identificador del usuario
            unread_only: Si solo obtener notificaciones no leídas
            limit: Número máximo de notificaciones a obtener
            
        Returns:
            List[Dict]: Lista de notificaciones del usuario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                query = """
                SELECT id, prediction_id, winning_number, winning_date, 
                       winning_position, matched_at, is_read, notification_message
                FROM notifications
                WHERE user_id = ?
                """
                
                params: List[Any] = [user_id]
                
                if unread_only:
                    query += " AND is_read = 0"
                
                query += " ORDER BY matched_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'prediction_id': row[1],
                        'winning_number': row[2],
                        'winning_date': row[3],
                        'winning_position': row[4],
                        'matched_at': row[5],
                        'is_read': bool(row[6]),
                        'notification_message': row[7]
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo notificaciones: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id: int) -> bool:
        """
        Marca una notificación como leída
        
        Args:
            notification_id: ID de la notificación
            
        Returns:
            bool: True si se marcó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                UPDATE notifications 
                SET is_read = 1 
                WHERE id = ?
                """, (notification_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error marcando notificación: {e}")
            return False
    
    def mark_all_user_notifications_as_read(self, user_id: str) -> int:
        """
        Marca todas las notificaciones de un usuario como leídas
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            int: Número de notificaciones marcadas como leídas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                UPDATE notifications 
                SET is_read = 1 
                WHERE user_id = ? AND is_read = 0
                """, (user_id,))
                
                conn.commit()
                return cursor.rowcount
                
        except sqlite3.Error as e:
            print(f"Error marcando notificaciones: {e}")
            return 0
    
    def get_unread_notifications_count(self, user_id: str) -> int:
        """
        Obtiene el número de notificaciones no leídas de un usuario
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            int: Número de notificaciones no leídas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Habilitar foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE user_id = ? AND is_read = 0
                """, (user_id,))
                
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            print(f"Error contando notificaciones: {e}")
            return 0
    
    # === MÉTODO PARA DETECCIÓN DE COINCIDENCIAS ===
    
    def check_predictions_against_winning_numbers(self, winning_date: str, 
                                                winning_numbers: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Compara números ganadores contra todas las predicciones activas y crea notificaciones
        
        Args:
            winning_date: Fecha del sorteo
            winning_numbers: Lista de tuplas (número, posición)
            
        Returns:
            List[Dict]: Lista de coincidencias encontradas
        """
        try:
            matches = []
            active_predictions = self.get_all_active_predictions()
            
            for prediction in active_predictions:
                prediction_numbers = prediction['predicted_numbers']
                
                for winning_number, position in winning_numbers:
                    if winning_number in prediction_numbers:
                        # Crear notificación
                        notification_id = self.create_notification(
                            user_id=prediction['user_id'],
                            prediction_id=prediction['id'],
                            winning_number=winning_number,
                            winning_date=winning_date,
                            winning_position=position
                        )
                        
                        if notification_id > 0:
                            matches.append({
                                'user_id': prediction['user_id'],
                                'prediction_id': prediction['id'],
                                'winning_number': winning_number,
                                'winning_position': position,
                                'notification_id': notification_id,
                                'prediction_method': prediction['prediction_method']
                            })
            
            return matches
            
        except Exception as e:
            print(f"Error verificando predicciones: {e}")
            return []
    
    def _check_new_draw_for_matches(self, draw_result: Dict[str, Any]) -> None:
        """
        Método privado para verificar coincidencias cuando se inserta un nuevo sorteo
        
        Args:
            draw_result: Diccionario con información del nuevo sorteo
        """
        try:
            winning_number = draw_result['number']
            winning_date = str(draw_result['date'])
            winning_position = draw_result.get('position', 1)
            
            # Obtener todas las predicciones activas
            active_predictions = self.get_all_active_predictions()
            
            matches_found = 0
            for prediction in active_predictions:
                prediction_numbers = prediction['predicted_numbers']
                
                # Verificar si el número ganador está en la predicción
                if winning_number in prediction_numbers:
                    # Crear notificación
                    notification_id = self.create_notification(
                        user_id=prediction['user_id'],
                        prediction_id=prediction['id'],
                        winning_number=winning_number,
                        winning_date=winning_date,
                        winning_position=winning_position
                    )
                    
                    if notification_id > 0:
                        matches_found += 1
                        print(f"📧 Notificación creada: Usuario {prediction['user_id']} - Número {winning_number}")
            
            if matches_found > 0:
                print(f"🎉 Se crearon {matches_found} notificaciones por coincidencias del número {winning_number}")
                
        except Exception as e:
            print(f"Error verificando coincidencias para nuevo sorteo: {e}")
    
    def get_successful_predictions_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de las predicciones exitosas del usuario
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Dict: Resumen de predicciones exitosas con estadísticas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Obtener predicciones con notificaciones (exitosas)
                cursor.execute("""
                SELECT DISTINCT p.id, p.predicted_numbers, p.prediction_method, 
                       p.confidence_threshold, p.prediction_date, p.notes,
                       COUNT(n.id) as match_count,
                       GROUP_CONCAT(n.winning_number || '(' || n.winning_position || ')') as winning_details
                FROM user_predictions p
                INNER JOIN notifications n ON p.id = n.prediction_id AND n.user_id = p.user_id
                WHERE p.user_id = ?
                GROUP BY p.id
                ORDER BY p.prediction_date DESC
                """, (user_id,))
                
                successful_predictions = []
                total_matches = 0
                
                for row in cursor.fetchall():
                    numbers_list = [int(x.strip()) for x in row[1].split(',') if x.strip()]
                    match_count = row[6]
                    total_matches += match_count
                    
                    successful_predictions.append({
                        'id': row[0],
                        'predicted_numbers': numbers_list,
                        'prediction_method': row[2],
                        'confidence_threshold': row[3],
                        'prediction_date': row[4],
                        'notes': row[5],
                        'match_count': match_count,
                        'winning_details': row[7]
                    })
                
                # Obtener estadísticas generales
                cursor.execute("""
                SELECT COUNT(*) FROM user_predictions WHERE user_id = ?
                """, (user_id,))
                total_predictions = cursor.fetchone()[0]
                
                cursor.execute("""
                SELECT COUNT(*) FROM notifications WHERE user_id = ?
                """, (user_id,))
                total_notifications = cursor.fetchone()[0]
                
                return {
                    'successful_predictions': successful_predictions,
                    'total_predictions': total_predictions,
                    'successful_count': len(successful_predictions),
                    'total_matches': total_matches,
                    'total_notifications': total_notifications,
                    'success_rate': (len(successful_predictions) / total_predictions * 100) if total_predictions > 0 else 0
                }
                
        except sqlite3.Error as e:
            print(f"Error obteniendo resumen de predicciones exitosas: {e}")
            return {
                'successful_predictions': [],
                'total_predictions': 0,
                'successful_count': 0,
                'total_matches': 0,
                'total_notifications': 0,
                'success_rate': 0
            }
    
    def process_recent_draws_for_notifications(self, days: int = 7) -> int:
        """
        Procesa sorteos recientes para crear notificaciones que puedan haberse perdido
        
        Args:
            days: Número de días hacia atrás para procesar
            
        Returns:
            int: Número de notificaciones creadas
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Obtener sorteos recientes
            recent_draws = self.get_draws_in_period(cutoff_date, datetime.now())
            
            notifications_created = 0
            for draw in recent_draws:
                date, number, position, prize_amount = draw
                
                # Verificar coincidencias para este sorteo
                matches = self.check_predictions_against_winning_numbers(
                    winning_date=str(date),
                    winning_numbers=[(number, position)]
                )
                
                notifications_created += len(matches)
            
            print(f"🔄 Procesamiento completo: {notifications_created} notificaciones creadas para últimos {days} días")
            return notifications_created
            
        except Exception as e:
            print(f"Error procesando sorteos recientes: {e}")
            return 0
    
    # === MÉTODOS PARA PREDICCIONES DEL SISTEMA ===
    
    def save_system_prediction(self, predicted_numbers: List[int], 
                              prediction_method: Optional[str] = None, 
                              confidence_threshold: Optional[float] = None,
                              analysis_days: Optional[int] = None, 
                              notes: Optional[str] = None) -> int:
        """
        Guarda una predicción del sistema en la base de datos
        
        Args:
            predicted_numbers: Lista de números predichos
            prediction_method: Método usado para la predicción
            confidence_threshold: Umbral de confianza usado
            analysis_days: Días de análisis usados
            notes: Notas adicionales
            
        Returns:
            int: ID de la predicción guardada, 0 si hay error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Convertir lista de números a string separado por comas
                numbers_str = ','.join(map(str, predicted_numbers))
                
                cursor.execute("""
                INSERT INTO system_predictions 
                (predicted_numbers, prediction_method, confidence_threshold, 
                 analysis_days, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (numbers_str, prediction_method, confidence_threshold, 
                      analysis_days, notes))
                
                conn.commit()
                prediction_id = cursor.lastrowid or 0
                
                if prediction_id > 0:
                    print(f"✅ Predicción del sistema guardada (ID: {prediction_id})")
                
                return prediction_id
                
        except sqlite3.Error as e:
            print(f"Error guardando predicción del sistema: {e}")
            return 0
    
    def get_system_predictions(self, active_only: bool = True, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las predicciones del sistema
        
        Args:
            active_only: Si solo obtener predicciones activas
            limit: Número máximo de predicciones a obtener
            
        Returns:
            List[Dict]: Lista de predicciones del sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                query = """
                SELECT id, predicted_numbers, prediction_method, confidence_threshold,
                       analysis_days, prediction_date, is_active, notes
                FROM system_predictions
                """
                
                params: List[Any] = []
                
                if active_only:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY prediction_date DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    # Convertir string de números de vuelta a lista
                    numbers_list = [int(x.strip()) for x in row[1].split(',') if x.strip()]
                    
                    results.append({
                        'id': row[0],
                        'predicted_numbers': numbers_list,
                        'prediction_method': row[2],
                        'confidence_threshold': row[3],
                        'analysis_days': row[4],
                        'prediction_date': row[5],
                        'is_active': bool(row[6]),
                        'notes': row[7]
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo predicciones del sistema: {e}")
            return []
    
    def create_system_notification(self, prediction_id: int, winning_number: int,
                                  winning_date: str, winning_position: Optional[int] = None,
                                  success_rate: Optional[float] = None) -> int:
        """
        Crea una notificación del sistema cuando una predicción coincide con un número ganador
        
        Args:
            prediction_id: ID de la predicción que coincidió
            winning_number: Número ganador que coincidió
            winning_date: Fecha del sorteo ganador
            winning_position: Posición del número ganador (1ra, 2da, 3ra)
            success_rate: Tasa de éxito de la predicción
            
        Returns:
            int: ID de la notificación creada, 0 si hay error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Crear mensaje personalizado
                position_text = ""
                if winning_position:
                    positions = {1: "1ra", 2: "2da", 3: "3ra"}
                    position_text = f" en {positions.get(winning_position, str(winning_position))} posición"
                
                success_text = ""
                if success_rate:
                    success_text = f" (Tasa de éxito: {success_rate:.1%})"
                
                message = f"🎯 ¡El sistema predijo correctamente el número {winning_number}! Sorteo del {winning_date}{position_text}{success_text}"
                
                cursor.execute("""
                INSERT OR IGNORE INTO system_notifications 
                (prediction_id, winning_number, winning_date, 
                 winning_position, notification_message, success_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (prediction_id, winning_number, winning_date, 
                      winning_position, message, success_rate))
                
                conn.commit()
                # Si rowcount es 0, significa que no se insertó (ya existía)
                if cursor.rowcount > 0:
                    notification_id = cursor.lastrowid or 0
                    print(f"📧 Notificación del sistema creada: {message}")
                    return notification_id
                else:
                    return 0  # Ya existía la notificación
                
        except sqlite3.Error as e:
            print(f"Error creando notificación del sistema: {e}")
            return 0
    
    def get_system_notifications(self, unread_only: bool = False, limit: int = 20, today_only: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene las notificaciones del sistema
        
        Args:
            unread_only: Si solo obtener notificaciones no leídas
            limit: Número máximo de notificaciones a obtener
            today_only: Si solo obtener notificaciones del día actual
            
        Returns:
            List[Dict]: Lista de notificaciones del sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                query = """
                SELECT id, prediction_id, winning_number, winning_date, 
                       winning_position, matched_at, is_read, notification_message, success_rate
                FROM system_notifications
                """
                
                params: List[Any] = []
                conditions = []
                
                if unread_only:
                    conditions.append("is_read = 0")
                
                if today_only:
                    today_date = datetime.now().date()
                    conditions.append("DATE(winning_date) = ?")
                    params.append(today_date)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY matched_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'prediction_id': row[1],
                        'winning_number': row[2],
                        'winning_date': row[3],
                        'winning_position': row[4],
                        'matched_at': row[5],
                        'is_read': bool(row[6]),
                        'notification_message': row[7],
                        'success_rate': row[8]
                    })
                
                return results
                
        except sqlite3.Error as e:
            print(f"Error obteniendo notificaciones del sistema: {e}")
            return []
    
    def mark_system_notifications_as_read(self, notification_ids: Optional[List[int]] = None) -> int:
        """
        Marca notificaciones del sistema como leídas
        
        Args:
            notification_ids: Lista de IDs específicos a marcar, None para marcar todas
            
        Returns:
            int: Número de notificaciones marcadas como leídas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                if notification_ids:
                    # Marcar notificaciones específicas
                    placeholders = ','.join(['?'] * len(notification_ids))
                    cursor.execute(f"""
                    UPDATE system_notifications 
                    SET is_read = 1 
                    WHERE id IN ({placeholders}) AND is_read = 0
                    """, notification_ids)
                else:
                    # Marcar todas las notificaciones
                    cursor.execute("""
                    UPDATE system_notifications 
                    SET is_read = 1 
                    WHERE is_read = 0
                    """)
                
                conn.commit()
                return cursor.rowcount
                
        except sqlite3.Error as e:
            print(f"Error marcando notificaciones del sistema: {e}")
            return 0
    
    def check_system_predictions_against_winning_numbers(self, winning_date: str, 
                                                        winning_numbers: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Compara números ganadores contra todas las predicciones activas del sistema y crea notificaciones
        
        Args:
            winning_date: Fecha del sorteo
            winning_numbers: Lista de tuplas (número, posición)
            
        Returns:
            List[Dict]: Lista de coincidencias encontradas
        """
        try:
            matches = []
            system_predictions = self.get_system_predictions(active_only=True)
            
            for prediction in system_predictions:
                prediction_numbers = prediction['predicted_numbers']
                
                # Calcular tasa de éxito basada en confianza
                success_rate = prediction.get('confidence_threshold', 0.0)
                
                for winning_number, position in winning_numbers:
                    if winning_number in prediction_numbers:
                        # Crear notificación del sistema
                        notification_id = self.create_system_notification(
                            prediction_id=prediction['id'],
                            winning_number=winning_number,
                            winning_date=winning_date,
                            winning_position=position,
                            success_rate=success_rate
                        )
                        
                        if notification_id > 0:
                            matches.append({
                                'prediction_id': prediction['id'],
                                'winning_number': winning_number,
                                'winning_position': position,
                                'notification_id': notification_id,
                                'prediction_method': prediction['prediction_method'],
                                'success_rate': success_rate
                            })
            
            return matches
            
        except Exception as e:
            print(f"Error verificando predicciones del sistema: {e}")
            return []
    
    def _check_new_draw_for_system_matches(self, draw_result: Dict[str, Any]) -> None:
        """
        Método privado para verificar coincidencias del sistema cuando se inserta un nuevo sorteo
        
        Args:
            draw_result: Diccionario con información del nuevo sorteo
        """
        try:
            winning_number = draw_result['number']
            winning_date = str(draw_result['date'])
            winning_position = draw_result.get('position', 1)
            
            # Obtener todas las predicciones activas del sistema
            system_predictions = self.get_system_predictions(active_only=True)
            
            matches_found = 0
            for prediction in system_predictions:
                prediction_numbers = prediction['predicted_numbers']
                
                # Verificar si el número ganador está en la predicción del sistema
                if winning_number in prediction_numbers:
                    # Calcular tasa de éxito
                    success_rate = prediction.get('confidence_threshold', 0.0)
                    
                    # Crear notificación del sistema
                    notification_id = self.create_system_notification(
                        prediction_id=prediction['id'],
                        winning_number=winning_number,
                        winning_date=winning_date,
                        winning_position=winning_position,
                        success_rate=success_rate
                    )
                    
                    if notification_id > 0:
                        matches_found += 1
                        print(f"🎯 Notificación del sistema creada: Predicción {prediction['id']} - Número {winning_number}")
            
            if matches_found > 0:
                print(f"🎉 El sistema tuvo {matches_found} predicción(es) exitosa(s) para el número {winning_number}")
                
        except Exception as e:
            print(f"Error verificando coincidencias del sistema para nuevo sorteo: {e}")
    
    def generate_and_save_system_predictions(self, predictor, analyzer, num_predictions: int = 15) -> int:
        """
        Genera y guarda predicciones automáticamente para el sistema
        
        Args:
            predictor: Instancia del LotteryPredictor
            analyzer: Instancia del StatisticalAnalyzer
            num_predictions: Número de predicciones a generar
            
        Returns:
            int: ID de la predicción guardada, 0 si hay error
        """
        try:
            # Verificar si ya hay predicciones del sistema activas para hoy
            today = datetime.now().date()
            existing_predictions = self.get_system_predictions(active_only=True, limit=5)
            
            # Si ya hay predicciones de hoy, no generar nuevas
            for pred in existing_predictions:
                pred_date = datetime.strptime(pred['prediction_date'][:10], '%Y-%m-%d').date()
                if pred_date == today:
                    print(f"Ya existen predicciones del sistema para hoy ({today})")
                    return pred['id']
            
            # Generar nuevas predicciones usando el método combinado
            predictions = predictor.generate_predictions(
                method="combinado",
                days=180,
                num_predictions=num_predictions,
                confidence_threshold=0.75
            )
            
            if predictions:
                # Extraer solo los números de las predicciones
                predicted_numbers = [pred[0] for pred in predictions]
                avg_confidence = sum(pred[2] for pred in predictions) / len(predictions)
                
                # Guardar predicción del sistema
                prediction_id = self.save_system_prediction(
                    predicted_numbers=predicted_numbers,
                    prediction_method="Predicción Automática del Sistema (Combinado)",
                    confidence_threshold=avg_confidence,
                    analysis_days=180,
                    notes=f"Predicción automática generada el {today} con {num_predictions} números"
                )
                
                if prediction_id > 0:
                    print(f"✅ Predicción automática del sistema generada con {len(predicted_numbers)} números")
                    return prediction_id
                else:
                    print("❌ Error al guardar la predicción automática del sistema")
                    return 0
            else:
                print("❌ No se pudieron generar predicciones automáticas del sistema")
                return 0
                
        except Exception as e:
            print(f"Error generando predicciones automáticas del sistema: {e}")
            return 0
