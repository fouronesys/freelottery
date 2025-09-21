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
