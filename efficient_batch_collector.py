#!/usr/bin/env python3
"""
Recopilador Eficiente por Lotes - Quiniela Loteka
Versión eficiente que prioriza los últimos años y permite colección incremental
"""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class EfficientBatchCollector:
    """Recopilador eficiente por lotes con priorización"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.checkpoint_file = "efficient_batch_checkpoint.json"
        
    def load_checkpoint(self) -> Dict[str, Any]:
        """Carga checkpoint existente"""
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except:
            return {'processed_years': []}
    
    def save_checkpoint(self, data: Dict[str, Any]):
        """Guarda checkpoint"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def process_year_efficiently(self, year: int) -> Dict[str, Any]:
        """Procesa un año de manera eficiente con menos fechas"""
        print(f"\n📅 PROCESANDO AÑO {year}")
        print("=" * 30)
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        # Verificar datos existentes
        existing_draws = self.db.get_draws_in_period(start_date, end_date)
        print(f"   📊 Datos existentes: {len(existing_draws)} registros")
        
        if len(existing_draws) > 30:
            print(f"   ✅ Año ya tiene suficientes datos")
            return {
                'year': year,
                'status': 'sufficient_data',
                'existing_records': len(existing_draws),
                'new_records': 0
            }
        
        result = {
            'year': year,
            'status': 'processing',
            'existing_records': len(existing_draws),
            'new_records': 0
        }
        
        try:
            # Solo 1 fecha por mes para ser más eficiente
            sample_dates = self._get_monthly_samples(year)
            print(f"   🎯 Procesando {len(sample_dates)} fechas (1 por mes)")
            
            total_new_records = 0
            
            for i, sample_date in enumerate(sample_dates, 1):
                try:
                    print(f"     📅 {sample_date.strftime('%d-%m')} ({i}/{len(sample_dates)})", end=" ")
                    
                    scraped_data = self.scraper.scrape_historical_data(sample_date, sample_date)
                    
                    if scraped_data:
                        target_date_str = sample_date.strftime('%Y-%m-%d')
                        date_specific_data = [r for r in scraped_data if r.get('date') == target_date_str]
                        
                        if date_specific_data:
                            saved_count = self.db.save_multiple_draw_results(date_specific_data)
                            total_new_records += saved_count
                            print(f"✅ {saved_count}")
                        else:
                            print("⚪")
                    else:
                        print("❌")
                    
                    # Pausa corta entre fechas
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌")
                    continue
            
            result['new_records'] = total_new_records
            result['status'] = 'completed'
            
            print(f"   📊 Total nuevos: {total_new_records} registros")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"   ❌ Error: {e}")
        
        return result
    
    def _get_monthly_samples(self, year: int) -> List[datetime]:
        """Obtiene 1 fecha de muestra por mes"""
        dates = []
        
        for month in range(1, 13):
            try:
                # Fecha media del mes (día 15)
                sample_date = datetime(year, month, 15)
                dates.append(sample_date)
            except ValueError:
                continue
        
        return dates
    
    def run_priority_collection(self, priority_years: List[int]) -> Dict[str, Any]:
        """Ejecuta recopilación para años prioritarios"""
        print(f"🚀 RECOPILACIÓN EFICIENTE - AÑOS PRIORITARIOS")
        print("=" * 50)
        print(f"🎯 Años prioritarios: {priority_years}")
        
        # Cargar checkpoint
        checkpoint = self.load_checkpoint()
        processed_years = set(checkpoint.get('processed_years', []))
        
        # Filtrar años ya procesados
        pending_years = [y for y in priority_years if y not in processed_years]
        
        if not pending_years:
            print("✅ Todos los años prioritarios ya fueron procesados")
            return checkpoint
        
        print(f"📊 Años pendientes: {pending_years}")
        
        results = checkpoint.get('year_results', [])
        total_new_records = checkpoint.get('total_new_records', 0)
        
        # Procesar años prioritarios
        for i, year in enumerate(pending_years, 1):
            print(f"\n{'='*50}")
            print(f"🔄 AÑO {i}/{len(pending_years)}: {year}")
            
            try:
                year_result = self.process_year_efficiently(year)
                results.append(year_result)
                total_new_records += year_result['new_records']
                
                # Actualizar checkpoint
                processed_years.add(year)
                checkpoint_data = {
                    'processed_years': list(processed_years),
                    'year_results': results,
                    'total_new_records': total_new_records,
                    'last_update': datetime.now().isoformat()
                }
                self.save_checkpoint(checkpoint_data)
                
                # Mostrar progreso
                progress = (i / len(pending_years)) * 100
                print(f"\n📊 PROGRESO: {progress:.1f}% - Nuevos registros totales: {total_new_records}")
                
                # Pausa corta entre años
                if i < len(pending_years):
                    time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrumpido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en año {year}: {e}")
                continue
        
        # Resultados
        final_results = {
            'priority_collection_completed': True,
            'completion_date': datetime.now().isoformat(),
            'processed_years': list(processed_years),
            'total_years_processed': len(processed_years),
            'total_new_records': total_new_records,
            'year_results': results
        }
        
        self.save_checkpoint(final_results)
        
        print(f"\n🎉 RECOPILACIÓN PRIORITARIA COMPLETADA")
        print(f"   ✅ Años procesados: {len(processed_years)}")
        print(f"   📊 Nuevos registros: {total_new_records}")
        
        return final_results
    
    def get_database_overview(self):
        """Muestra resumen de la base de datos actual"""
        print(f"\n📋 RESUMEN DE BASE DE DATOS")
        print("=" * 40)
        
        stats = self.db.get_database_stats()
        
        print(f"📊 Estado actual:")
        print(f"   • Total registros: {stats['total_records']}")
        print(f"   • Fechas únicas: {stats['unique_dates']}")
        print(f"   • Rango: {stats['earliest_date']} - {stats['latest_date']}")
        
        # Distribución por años recientes
        current_year = datetime.now().year
        print(f"\n📈 Distribución reciente:")
        for year in range(current_year, current_year - 6, -1):
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            year_draws = self.db.get_draws_in_period(year_start, year_end)
            print(f"   • {year}: {len(year_draws)} registros")

def main():
    """Función principal con estrategia eficiente"""
    collector = EfficientBatchCollector()
    
    print("🎯 RECOPILACIÓN HISTÓRICA EFICIENTE")
    print("📦 Estrategia: Priorizar últimos 6 años con 1 fecha/mes")
    
    # Mostrar estado actual
    collector.get_database_overview()
    
    try:
        # Definir años prioritarios (últimos 6 años)
        current_year = datetime.now().year
        priority_years = list(range(current_year, current_year - 6, -1))
        
        # Ejecutar recopilación prioritaria
        results = collector.run_priority_collection(priority_years)
        
        # Mostrar resultado final
        collector.get_database_overview()
        
        print(f"\n🎉 FASE PRIORITARIA COMPLETADA")
        print(f"💡 Para recopilar años más antiguos (2010-{current_year-6}),")
        print(f"   ejecute el script nuevamente con años adicionales")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)