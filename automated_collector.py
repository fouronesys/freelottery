#!/usr/bin/env python3
"""
Sistema de Recopilación Automatizada de Datos de Quiniela Loteka
Recopila datos diariamente y mantiene la base de datos actualizada
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lottery_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedLotteryCollector:
    """Sistema automatizado para recopilación continua de datos de lotería"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.is_running = False
        self.last_collection_time = None
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_records_collected': 0
        }
        
    def collect_latest_results(self) -> Dict[str, Any]:
        """
        Recopila los resultados más recientes disponibles
        """
        try:
            logger.info("🎯 Iniciando recopilación automática de datos...")
            
            # Obtener últimos 3 días para asegurar cobertura completa
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)
            
            logger.info(f"📅 Buscando datos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
            
            # Recopilar datos
            results = self.scraper.scrape_historical_data(start_date, end_date)
            
            if results:
                # Guardar en base de datos
                saved_count = self.db.save_multiple_draw_results(results)
                
                # Actualizar estadísticas
                self.stats['total_records_collected'] += saved_count
                self.stats['successful_runs'] += 1
                
                logger.info(f"✅ Recopilación exitosa: {saved_count} registros guardados")
                
                return {
                    'success': True,
                    'records_found': len(results),
                    'records_saved': saved_count,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning("⚠️ No se encontraron nuevos datos")
                self.stats['failed_runs'] += 1
                
                return {
                    'success': False,
                    'reason': 'No data found',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error en recopilación automática: {e}")
            self.stats['failed_runs'] += 1
            
            return {
                'success': False,
                'reason': f'Exception: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self.stats['total_runs'] += 1
            self.last_collection_time = datetime.now()
    
    def fill_missing_dates(self) -> Dict[str, Any]:
        """
        Llena fechas faltantes en la base de datos
        """
        try:
            logger.info("🔍 Verificando fechas faltantes...")
            
            # Obtener estadísticas de la base de datos
            stats = self.db.get_database_stats()
            
            if stats['total_records'] == 0:
                logger.info("📊 Base de datos vacía, iniciando recopilación inicial...")
                # Recopilar últimas 2 semanas
                end_date = datetime.now()
                start_date = end_date - timedelta(days=14)
                
            else:
                # Identificar vacíos en los datos
                latest_date = datetime.strptime(stats['latest_date'], '%Y-%m-%d')
                today = datetime.now()
                
                # Si hay un vacío de más de 1 día, llenarlo
                days_gap = (today - latest_date).days
                
                if days_gap <= 1:
                    logger.info("📅 Datos están actualizados")
                    return {'success': True, 'action': 'no_gaps_found'}
                
                logger.info(f"📊 Detectado vacío de {days_gap} días, llenando...")
                start_date = latest_date + timedelta(days=1)
                end_date = today
            
            # Recopilar datos para llenar el vacío
            results = self.scraper.scrape_historical_data(start_date, end_date)
            
            if results:
                saved_count = self.db.save_multiple_draw_results(results)
                logger.info(f"✅ Llenado de vacíos: {saved_count} registros guardados")
                
                return {
                    'success': True,
                    'action': 'gap_filled',
                    'records_saved': saved_count,
                    'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                }
            else:
                logger.warning("⚠️ No se pudieron llenar los vacíos de datos")
                return {'success': False, 'action': 'gap_fill_failed'}
                
        except Exception as e:
            logger.error(f"❌ Error llenando vacíos: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_collection_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del sistema de recopilación
        """
        db_stats = self.db.get_database_stats()
        
        return {
            'automation_stats': self.stats,
            'database_stats': db_stats,
            'last_collection': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'is_running': self.is_running,
            'progress_to_720_days': {
                'current_days': db_stats['date_range_days'],
                'target_days': 720,
                'percentage': min(100, (db_stats['date_range_days'] / 720) * 100),
                'days_remaining': max(0, 720 - db_stats['date_range_days'])
            }
        }
    
    def scheduled_collection_job(self):
        """
        Trabajo programado para recopilación automática
        """
        logger.info("⏰ Ejecutando trabajo programado de recopilación...")
        
        # Recopilar datos recientes
        result = self.collect_latest_results()
        
        # Si fue exitoso, intentar llenar vacíos ocasionalmente
        if result['success'] and self.stats['total_runs'] % 7 == 0:  # Cada 7 ejecuciones
            logger.info("🔄 Verificando y llenando vacíos periódicamente...")
            self.fill_missing_dates()
        
        # Mostrar estadísticas
        status = self.get_collection_status()
        progress = status['progress_to_720_days']['percentage']
        logger.info(f"📊 Progreso hacia 720 días: {progress:.1f}% ({status['database_stats']['date_range_days']} días actuales)")
    
    def start_automation(self, schedule_interval: str = "daily"):
        """
        Inicia el sistema de automatización
        
        Args:
            schedule_interval: Intervalo de programación ('daily', 'hourly', etc.)
        """
        logger.info("🚀 Iniciando sistema de automatización...")
        
        self.is_running = True
        
        # Configurar horarios
        if schedule_interval == "daily":
            # Recopilar datos diariamente a las 8:30 PM (después del sorteo de las 7:55 PM)
            schedule.every().day.at("20:30").do(self.scheduled_collection_job)
            logger.info("⏰ Programado para ejecutarse diariamente a las 8:30 PM")
            
        elif schedule_interval == "hourly":
            # Para testing o situaciones donde necesitamos más frecuencia
            schedule.every().hour.do(self.scheduled_collection_job)
            logger.info("⏰ Programado para ejecutarse cada hora")
        
        # Ejecución inicial para llenar vacíos
        logger.info("🎯 Ejecutando recopilación inicial...")
        self.fill_missing_dates()
        
        # Ejecutar el scheduler en un hilo separado
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("✅ Sistema de automatización iniciado correctamente")
        
        return scheduler_thread
    
    def stop_automation(self):
        """
        Detiene el sistema de automatización
        """
        logger.info("🛑 Deteniendo sistema de automatización...")
        self.is_running = False
        schedule.clear()
        logger.info("✅ Sistema de automatización detenido")

def main():
    """Función principal para ejecutar el sistema automatizado"""
    
    print("🎯 SISTEMA DE RECOPILACIÓN AUTOMATIZADA - QUINIELA LOTEKA")
    print("=" * 60)
    
    collector = AutomatedLotteryCollector()
    
    try:
        # Iniciar automatización
        scheduler_thread = collector.start_automation("daily")
        
        # Mostrar estado inicial
        status = collector.get_collection_status()
        print(f"📊 Estado inicial:")
        print(f"   • Registros en BD: {status['database_stats']['total_records']}")
        print(f"   • Días de datos: {status['database_stats']['date_range_days']}")
        print(f"   • Progreso hacia 720 días: {status['progress_to_720_days']['percentage']:.1f}%")
        
        print("\n✅ Sistema funcionando en segundo plano...")
        print("💡 El sistema recopilará datos diariamente a las 8:30 PM")
        print("💡 Presiona Ctrl+C para detener")
        
        # Mantener el programa ejecutándose
        try:
            while collector.is_running:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Señal de interrupción recibida...")
            
    except Exception as e:
        logger.error(f"❌ Error en el sistema: {e}")
        
    finally:
        collector.stop_automation()
        print("👋 Sistema de automatización finalizado")

if __name__ == "__main__":
    main()