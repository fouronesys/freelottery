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
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                    FOREIGN KEY (prediction_id) REFERENCES user_predictions (id)
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
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error inicializando base de datos: {e}")
            raise
    
    def save_draw_result(self, result: Dict[str, Any]) -> bool:
        """
        Guarda un resultado de sorteo en la base de datos
        
        Args:
            result: Diccionario con 'date', 'number', 'position', 'prize_amount'
        
        Returns:
            bool: True si se guardó exitosamente, False si ya existía
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT OR IGNORE INTO draw_results 
                (date, number, position, prize_amount)
                VALUES (?, ?, ?, ?)
                """, (
                    result['date'],
                    result['number'],
                    result.get('position', 1),
                    result.get('prize_amount', 0)
                ))
                
                # Actualizar metadatos de última actualización
                cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value, updated_at)
                VALUES ('last_update', ?, CURRENT_TIMESTAMP)
                """, (datetime.now().isoformat(),))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error guardando resultado: {e}")
            return False
    
    def get_draws_in_period(self, start_date: datetime, end_date: datetime) -> List[Tuple]:
        """Obtiene todos los sorteos en un período específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT date, number, position, prize_amount
                FROM draw_results
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, position
                """, (start_date.date(), end_date.date()))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            print(f"Error obteniendo sorteos: {e}")
            return []
    
    def get_number_frequency(self, number: int, days: int = 180) -> Tuple[int, float]:
        """
        Obtiene la frecuencia de un número específico
        
        Returns:
            Tuple[int, float]: (frecuencia_absoluta, frecuencia_relativa)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Frecuencia absoluta
                cursor.execute("""
                SELECT COUNT(*) FROM draw_results
                WHERE number = ? AND date >= ?
                """, (number, cutoff_date.date()))
                
                absolute_freq = cursor.fetchone()[0]
                
                # Total de sorteos
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ?
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
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Total de sorteos únicos en el período
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ?
                """, (cutoff_date.date(),))
                
                total_draws = cursor.fetchone()[0]
                
                if total_draws == 0:
                    return []
                
                # Frecuencia por número
                cursor.execute("""
                SELECT number, COUNT(*) as frequency
                FROM draw_results
                WHERE date >= ?
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
        """Obtiene el número total de sorteos registrados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT date) FROM draw_results")
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def get_draws_count_last_days(self, days: int) -> int:
        """Obtiene el número de sorteos en los últimos N días"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM draw_results
                WHERE date >= ?
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
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute("""
                SELECT date, number, position
                FROM draw_results
                WHERE date >= ? AND position IS NOT NULL
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
        """Obtiene los sorteos más recientes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT date, number, position, prize_amount
                FROM draw_results
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
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT number FROM draw_results ORDER BY number")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Limpia datos antiguos para mantener la base de datos optimizada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                           prediction_method: str = None, confidence_threshold: float = None,
                           analysis_days: int = None, notes: str = None) -> int:
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
                return cursor.lastrowid
                
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
                          winning_date: str, winning_position: int = None) -> int:
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
                cursor = conn.cursor()
                
                # Crear mensaje personalizado
                position_text = ""
                if winning_position:
                    positions = {1: "1ra", 2: "2da", 3: "3ra"}
                    position_text = f" en {positions.get(winning_position, str(winning_position))} posición"
                
                message = f"¡Felicitaciones! Tu predicción del número {winning_number} coincidió con el sorteo del {winning_date}{position_text}."
                
                cursor.execute("""
                INSERT INTO notifications 
                (user_id, prediction_id, winning_number, winning_date, 
                 winning_position, notification_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, prediction_id, winning_number, winning_date, 
                      winning_position, message))
                
                conn.commit()
                return cursor.lastrowid
                
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
                cursor = conn.cursor()
                
                query = """
                SELECT id, prediction_id, winning_number, winning_date, 
                       winning_position, matched_at, is_read, notification_message
                FROM notifications
                WHERE user_id = ?
                """
                
                params = [user_id]
                
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
