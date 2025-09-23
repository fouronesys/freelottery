#!/usr/bin/env python3
"""
Recopilador Exhaustivo - Quiniela Loteka
Sistema que procesa TODAS las fechas día por día desde 2010 hasta completar
"""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class ExhaustiveCollector:
    """Recopilador que procesa día por día sin muestreo"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.checkpoint_file = "exhaustive_checkpoint.json"
        
    def load_checkpoint(self) -> Dict[str, Any]:
        """Carga checkpoint"""
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except:
            return {'last_processed_date': '2010-08-01', 'total_processed': 0, 'total_saved': 0}
    
    def save_checkpoint(self, data: Dict[str, Any]):
        """Guarda checkpoint"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def process_date_batch(self, start_date: datetime, days_count: int = 7) -> Dict[str, Any]:
        """Procesa un lote de fechas consecutivas"""
        end_date = start_date + timedelta(days=days_count - 1)
        
        batch_result = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'days_processed': 0,
            'records_saved': 0,
            'dates_with_data': 0
        }
        
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # Verificar si ya tenemos datos para esta fecha
                existing_draws = self.db.get_draws_in_period(current_date, current_date)
                
                if len(existing_draws) >= 3:  # Ya tenemos datos suficientes
                    print(f"     📅 {current_date.strftime('%d-%m-%Y')}: ✅ Existe")
                else:
                    print(f"     📅 {current_date.strftime('%d-%m-%Y')}: 🔍 Procesando...")
                    
                    # Intentar obtener datos para esta fecha específica
                    scraped_data = self.scraper.scrape_historical_data(current_date, current_date)
                    
                    if scraped_data:
                        target_date_str = current_date.strftime('%Y-%m-%d')
                        date_specific_data = [r for r in scraped_data if r.get('date') == target_date_str]
                        
                        if date_specific_data:
                            saved_count = self.db.save_multiple_draw_results(date_specific_data)
                            batch_result['records_saved'] += saved_count
                            if saved_count > 0:
                                batch_result['dates_with_data'] += 1
                                print(f"       ✅ Guardados: {saved_count} registros")
                            else:
                                print(f"       ⚪ Sin datos nuevos")
                        else:
                            print(f"       ❌ Sin datos específicos")
                    else:
                        print(f"       ❌ Sin respuesta")
                
                batch_result['days_processed'] += 1
                
                # Pausa corta entre fechas
                time.sleep(1)
                
            except Exception as e:
                print(f"       ❌ Error: {str(e)[:30]}...")
            
            current_date += timedelta(days=1)
        
        return batch_result
    
    def run_exhaustive_collection(self, max_days: int = 100) -> Dict[str, Any]:
        """Ejecuta recopilación exhaustiva día por día"""
        print(f"🚀 RECOPILACIÓN EXHAUSTIVA DÍA POR DÍA")
        print("=" * 50)
        
        # Cargar checkpoint
        checkpoint = self.load_checkpoint()
        start_date = datetime.strptime(checkpoint['last_processed_date'], '%Y-%m-%d')
        end_date = datetime(2025, 9, 23)
        
        total_days = (end_date - start_date).days + 1
        print(f"📅 Desde: {start_date.strftime('%d-%m-%Y')}")
        print(f"📅 Hasta: {end_date.strftime('%d-%m-%Y')}")
        print(f"📊 Total días restantes: {total_days}")
        print(f"🎯 Procesando máximo {max_days} días en esta sesión")
        
        # Limitar días para esta sesión
        session_end_date = min(start_date + timedelta(days=max_days - 1), end_date)
        session_days = (session_end_date - start_date).days + 1
        
        print(f"📦 Esta sesión: {session_days} días ({start_date.strftime('%d-%m')} - {session_end_date.strftime('%d-%m')})")
        
        # Resultados de la sesión
        session_results = {
            'session_start': datetime.now().isoformat(),
            'original_start_date': start_date.strftime('%Y-%m-%d'),
            'session_end_date': session_end_date.strftime('%Y-%m-%d'),
            'total_days_processed': 0,
            'total_records_saved': 0,
            'total_dates_with_data': 0,
            'batch_results': []
        }
        
        # Procesar por lotes semanales
        current_batch_start = start_date
        batch_number = 1
        
        while current_batch_start <= session_end_date:
            # Calcular tamaño del lote
            batch_end = min(current_batch_start + timedelta(days=6), session_end_date)
            batch_days = (batch_end - current_batch_start).days + 1
            
            print(f"\n📦 LOTE {batch_number}: {current_batch_start.strftime('%d-%m')} - {batch_end.strftime('%d-%m')} ({batch_days} días)")
            
            try:
                batch_result = self.process_date_batch(current_batch_start, batch_days)
                session_results['batch_results'].append(batch_result)
                session_results['total_days_processed'] += batch_result['days_processed']
                session_results['total_records_saved'] += batch_result['records_saved']
                session_results['total_dates_with_data'] += batch_result['dates_with_data']
                
                print(f"   📊 Lote completado: {batch_result['records_saved']} registros, {batch_result['dates_with_data']} fechas con datos")
                
                # Actualizar checkpoint
                checkpoint_data = {
                    'last_processed_date': batch_end.strftime('%Y-%m-%d'),
                    'total_processed': checkpoint.get('total_processed', 0) + batch_result['days_processed'],
                    'total_saved': checkpoint.get('total_saved', 0) + batch_result['records_saved'],
                    'session_results': session_results
                }
                self.save_checkpoint(checkpoint_data)
                
                # Progreso
                progress = (batch_number * 7) / session_days * 100
                print(f"   📈 Progreso de sesión: {min(progress, 100):.1f}%")
                
                # Pausa entre lotes
                if current_batch_start < session_end_date:
                    time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrumpido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en lote: {e}")
            
            current_batch_start = batch_end + timedelta(days=1)
            batch_number += 1
        
        # Finalizar sesión
        session_results['session_end'] = datetime.now().isoformat()
        final_checkpoint = checkpoint_data.copy()
        final_checkpoint['final_session_results'] = session_results
        self.save_checkpoint(final_checkpoint)
        
        print(f"\n🎉 SESIÓN COMPLETADA")
        print(f"   ✅ Días procesados: {session_results['total_days_processed']}")
        print(f"   📊 Registros guardados: {session_results['total_records_saved']}")
        print(f"   📅 Fechas con datos: {session_results['total_dates_with_data']}")
        
        return session_results
    
    def show_progress_report(self):
        """Muestra reporte de progreso completo"""
        print(f"\n📋 REPORTE DE PROGRESO EXHAUSTIVO")
        print("=" * 45)
        
        # Checkpoint actual
        checkpoint = self.load_checkpoint()
        start_original = datetime(2010, 8, 1)
        last_processed = datetime.strptime(checkpoint['last_processed_date'], '%Y-%m-%d')
        end_target = datetime(2025, 9, 23)
        
        # Cálculos
        days_processed = (last_processed - start_original).days + 1
        days_remaining = (end_target - last_processed).days
        total_days = (end_target - start_original).days + 1
        progress_percent = (days_processed / total_days) * 100
        
        print(f"📊 Progreso general:")
        print(f"   • Período objetivo: {start_original.strftime('%d-%m-%Y')} - {end_target.strftime('%d-%m-%Y')}")
        print(f"   • Último día procesado: {last_processed.strftime('%d-%m-%Y')}")
        print(f"   • Días procesados: {days_processed:,}")
        print(f"   • Días restantes: {days_remaining:,}")
        print(f"   • Progreso: {progress_percent:.1f}%")
        print(f"   • Total registros guardados: {checkpoint.get('total_saved', 0):,}")
        
        # Estadísticas de BD
        stats = self.db.get_database_stats()
        print(f"\n📈 Estado de base de datos:")
        print(f"   • Total registros: {stats['total_records']:,}")
        print(f"   • Fechas únicas: {stats['unique_dates']:,}")
        print(f"   • Rango: {stats['earliest_date']} - {stats['latest_date']}")

def main():
    """Función principal"""
    collector = ExhaustiveCollector()
    
    print("🎯 RECOPILACIÓN EXHAUSTIVA DE DATOS HISTÓRICOS")
    print("📦 Estrategia: Procesar TODAS las fechas día por día")
    
    # Mostrar progreso actual
    collector.show_progress_report()
    
    try:
        # Ejecutar recopilación (100 días por sesión para control)
        results = collector.run_exhaustive_collection(max_days=100)
        
        # Mostrar progreso actualizado
        collector.show_progress_report()
        
        print(f"\n🎉 SESIÓN COMPLETADA")
        print(f"💡 Para continuar, ejecute el script nuevamente")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)