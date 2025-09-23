#!/usr/bin/env python3
"""
Recopilador Masivo de Datos Históricos - Quiniela Loteka
Sistema de procesamiento por lotes para recopilar 15 años de datos históricos (2010-2025)
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import traceback

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class MassiveHistoricalCollector:
    """Recopilador masivo por lotes para datos históricos de 15 años"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.checkpoint_file = "massive_collection_checkpoint.json"
        
        # Configuración de lotes
        self.batch_size_days = 90  # 3 meses por lote
        self.pause_between_batches = 30  # 30 segundos entre lotes
        self.pause_between_requests = 5  # 5 segundos entre solicitudes
        
        print("🚀 RECOPILADOR MASIVO DE DATOS HISTÓRICOS")
        print("=" * 50)
        print(f"📅 Objetivo: Datos desde 01-08-2010 hasta {datetime.now().strftime('%d-%m-%Y')}")
        print(f"📦 Procesamiento por lotes de {self.batch_size_days} días")
        print(f"⏱️ Pausa entre lotes: {self.pause_between_batches}s")
        
    def load_checkpoint(self) -> Dict[str, Any]:
        """Carga el punto de control para reanudar procesamiento"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                print(f"📋 Checkpoint encontrado: Procesado hasta {checkpoint.get('last_processed_date', 'N/A')}")
                return checkpoint
            except Exception as e:
                print(f"⚠️ Error cargando checkpoint: {e}")
        return {}
    
    def save_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """Guarda el punto de control actual"""
        checkpoint_data['last_update'] = datetime.now().isoformat()
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando checkpoint: {e}")
    
    def generate_batch_periods(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """Genera períodos de lotes para procesamiento"""
        batches = []
        current_start = start_date
        
        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=self.batch_size_days - 1), end_date)
            batches.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)
        
        print(f"📦 Generados {len(batches)} lotes para procesamiento")
        return batches
    
    def process_batch(self, batch_start: datetime, batch_end: datetime, batch_number: int, total_batches: int) -> Dict[str, Any]:
        """Procesa un lote específico de datos"""
        print(f"\n📦 PROCESANDO LOTE {batch_number}/{total_batches}")
        print(f"   📅 Período: {batch_start.strftime('%d-%m-%Y')} - {batch_end.strftime('%d-%m-%Y')}")
        print(f"   📊 Días en lote: {(batch_end - batch_start).days + 1}")
        
        batch_results = {
            'batch_number': batch_number,
            'start_date': batch_start.strftime('%Y-%m-%d'),
            'end_date': batch_end.strftime('%Y-%m-%d'),
            'total_days': (batch_end - batch_start).days + 1,
            'records_collected': 0,
            'dates_with_data': 0,
            'errors': [],
            'processing_time': 0,
            'start_time': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Recopilar datos para el lote
            print(f"   🔍 Iniciando scraping para lote...")
            collected_data = self.scraper.scrape_historical_data(batch_start, batch_end)
            
            if collected_data:
                print(f"   📥 Datos obtenidos: {len(collected_data)} registros potenciales")
                
                # Filtrar datos para el rango específico del lote
                batch_specific_data = []
                for record in collected_data:
                    record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                    if batch_start <= record_date <= batch_end:
                        batch_specific_data.append(record)
                
                print(f"   🎯 Datos filtrados para el lote: {len(batch_specific_data)} registros")
                
                if batch_specific_data:
                    # Guardar en la base de datos
                    saved_count = self.db.save_multiple_draw_results(batch_specific_data)
                    batch_results['records_collected'] = saved_count
                    
                    # Contar fechas únicas
                    unique_dates = set(record['date'] for record in batch_specific_data)
                    batch_results['dates_with_data'] = len(unique_dates)
                    
                    print(f"   ✅ Guardados: {saved_count} registros en {len(unique_dates)} fechas")
                else:
                    print(f"   ⚠️ Sin datos específicos para este lote")
            else:
                print(f"   ❌ Sin datos obtenidos del scraper")
                
        except Exception as e:
            error_msg = f"Error procesando lote: {str(e)}"
            print(f"   ❌ {error_msg}")
            batch_results['errors'].append(error_msg)
            traceback.print_exc()
        
        batch_results['processing_time'] = time.time() - start_time
        batch_results['end_time'] = datetime.now().isoformat()
        
        print(f"   ⏱️ Tiempo de procesamiento: {batch_results['processing_time']:.1f}s")
        
        return batch_results
    
    def collect_massive_historical_data(self, start_date: datetime, end_date: datetime, resume_from_checkpoint: bool = True) -> Dict[str, Any]:
        """Ejecuta la recopilación masiva de datos históricos"""
        print(f"\n🎯 INICIANDO RECOPILACIÓN MASIVA")
        print(f"   📅 Desde: {start_date.strftime('%d-%m-%Y')}")
        print(f"   📅 Hasta: {end_date.strftime('%d-%m-%Y')}")
        print(f"   📊 Total días: {(end_date - start_date).days + 1}")
        
        # Cargar checkpoint si existe
        checkpoint = self.load_checkpoint() if resume_from_checkpoint else {}
        
        # Determinar punto de inicio
        actual_start_date = start_date
        if checkpoint and 'last_processed_date' in checkpoint:
            last_processed = datetime.strptime(checkpoint['last_processed_date'], '%Y-%m-%d')
            if last_processed >= start_date:
                actual_start_date = last_processed + timedelta(days=1)
                print(f"   🔄 Reanudando desde: {actual_start_date.strftime('%d-%m-%Y')}")
        
        # Verificar si ya terminó
        if actual_start_date > end_date:
            print(f"   ✅ Recopilación ya completada según checkpoint")
            return checkpoint.get('final_results', {})
        
        # Generar lotes
        batches = self.generate_batch_periods(actual_start_date, end_date)
        
        # Inicializar resultados de la sesión
        session_results = {
            'session_start': datetime.now().isoformat(),
            'original_start_date': start_date.strftime('%Y-%m-%d'),
            'original_end_date': end_date.strftime('%Y-%m-%d'),
            'resumed_from': actual_start_date.strftime('%Y-%m-%d'),
            'total_batches': len(batches),
            'completed_batches': 0,
            'total_records_collected': 0,
            'total_dates_with_data': 0,
            'batch_results': [],
            'errors': []
        }
        
        # Procesar cada lote
        for i, (batch_start, batch_end) in enumerate(batches, 1):
            try:
                print(f"\n{'='*60}")
                batch_result = self.process_batch(batch_start, batch_end, i, len(batches))
                session_results['batch_results'].append(batch_result)
                session_results['completed_batches'] += 1
                session_results['total_records_collected'] += batch_result['records_collected']
                session_results['total_dates_with_data'] += batch_result['dates_with_data']
                
                # Actualizar checkpoint
                checkpoint_data = {
                    'last_processed_date': batch_end.strftime('%Y-%m-%d'),
                    'completed_batches': session_results['completed_batches'],
                    'total_batches': session_results['total_batches'],
                    'progress_percentage': (session_results['completed_batches'] / session_results['total_batches']) * 100,
                    'session_results': session_results
                }
                self.save_checkpoint(checkpoint_data)
                
                # Mostrar progreso
                progress = (i / len(batches)) * 100
                print(f"\n📊 PROGRESO GENERAL: {progress:.1f}% ({i}/{len(batches)} lotes)")
                print(f"   📈 Registros totales recopilados: {session_results['total_records_collected']}")
                print(f"   📅 Fechas con datos: {session_results['total_dates_with_data']}")
                
                # Pausa entre lotes (excepto el último)
                if i < len(batches):
                    print(f"   ⏸️ Pausando {self.pause_between_batches}s antes del siguiente lote...")
                    time.sleep(self.pause_between_batches)
                    
            except KeyboardInterrupt:
                print(f"\n⚠️ Procesamiento interrumpido por el usuario")
                print(f"   📋 Progreso guardado en checkpoint")
                return session_results
            except Exception as e:
                error_msg = f"Error crítico en lote {i}: {str(e)}"
                print(f"   ❌ {error_msg}")
                session_results['errors'].append(error_msg)
                traceback.print_exc()
                
                # Continuar con el siguiente lote
                continue
        
        # Completar sesión
        session_results['session_end'] = datetime.now().isoformat()
        session_results['completed'] = True
        
        # Guardar resultado final
        final_checkpoint = {
            'completed': True,
            'completion_date': datetime.now().isoformat(),
            'final_results': session_results
        }
        self.save_checkpoint(final_checkpoint)
        
        print(f"\n🎉 RECOPILACIÓN MASIVA COMPLETADA")
        print(f"   ✅ Lotes procesados: {session_results['completed_batches']}/{session_results['total_batches']}")
        print(f"   📊 Total registros: {session_results['total_records_collected']}")
        print(f"   📅 Total fechas: {session_results['total_dates_with_data']}")
        
        return session_results
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Genera un reporte final de toda la base de datos"""
        print(f"\n📋 GENERANDO REPORTE FINAL DE BASE DE DATOS")
        print("=" * 50)
        
        stats = self.db.get_database_stats()
        
        # Obtener distribución por años usando un rango amplio
        earliest_year = int(stats['earliest_date'][:4]) if stats['earliest_date'] else 2010
        latest_year = int(stats['latest_date'][:4]) if stats['latest_date'] else datetime.now().year
        
        year_distribution = {}
        for year in range(earliest_year, latest_year + 1):
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            year_draws = self.db.get_draws_in_period(year_start, year_end)
            if year_draws:
                year_distribution[str(year)] = len(year_draws)
        
        report = {
            'report_date': datetime.now().isoformat(),
            'database_stats': stats,
            'year_distribution': year_distribution,
            'total_years_covered': len(year_distribution),
            'date_range': {
                'earliest': stats['earliest_date'],
                'latest': stats['latest_date']
            }
        }
        
        print(f"📊 ESTADÍSTICAS FINALES:")
        print(f"   • Total registros: {stats['total_records']}")
        print(f"   • Fechas únicas: {stats['unique_dates']}")
        print(f"   • Años cubiertos: {len(year_distribution)}")
        print(f"   • Rango temporal: {stats['earliest_date']} - {stats['latest_date']}")
        
        print(f"\n📈 DISTRIBUCIÓN POR AÑOS:")
        for year, count in sorted(year_distribution.items()):
            print(f"   • {year}: {count} registros")
        
        return report

def main():
    """Función principal"""
    collector = MassiveHistoricalCollector()
    
    # Definir rango completo (15 años)
    start_date = datetime(2010, 8, 1)
    end_date = datetime.now()
    
    print(f"🎯 OBJETIVO: Recopilar {(end_date - start_date).days + 1} días de datos históricos")
    
    try:
        # Ejecutar recopilación masiva
        results = collector.collect_massive_historical_data(start_date, end_date)
        
        # Generar reporte final
        final_report = collector.generate_final_report()
        
        print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)