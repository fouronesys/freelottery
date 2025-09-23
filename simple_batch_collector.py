#!/usr/bin/env python3
"""
Recopilador Simple por Lotes - Quiniela Loteka
Versión robusta y simple para procesamiento por años
"""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class SimpleBatchCollector:
    """Recopilador simple por lotes anuales"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.checkpoint_file = "simple_batch_checkpoint.json"
        
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
        except Exception as e:
            print(f"⚠️ Error guardando checkpoint: {e}")
    
    def process_year_batch(self, year: int) -> Dict[str, Any]:
        """Procesa un año completo"""
        print(f"\n📅 PROCESANDO AÑO {year}")
        print("=" * 30)
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        # Verificar si ya tenemos datos de este año
        existing_draws = self.db.get_draws_in_period(start_date, end_date)
        
        print(f"   📊 Datos existentes: {len(existing_draws)} registros")
        
        if len(existing_draws) > 50:  # Si ya tenemos muchos datos del año, saltar
            print(f"   ✅ Año ya procesado (suficientes datos)")
            return {
                'year': year,
                'status': 'skipped',
                'existing_records': len(existing_draws),
                'new_records': 0
            }
        
        result = {
            'year': year,
            'status': 'processing',
            'existing_records': len(existing_draws),
            'new_records': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            print(f"   🔍 Iniciando scraping para {year}...")
            
            # Usar fechas estratégicas del año
            sample_dates = self._get_strategic_year_dates(year)
            print(f"   🎯 Procesando {len(sample_dates)} fechas estratégicas")
            
            total_new_records = 0
            
            for i, sample_date in enumerate(sample_dates, 1):
                try:
                    print(f"     📅 {sample_date.strftime('%d-%m-%Y')} ({i}/{len(sample_dates)})")
                    
                    # Scraping para fecha específica
                    scraped_data = self.scraper.scrape_historical_data(sample_date, sample_date)
                    
                    if scraped_data:
                        # Filtrar solo datos de la fecha objetivo
                        target_date_str = sample_date.strftime('%Y-%m-%d')
                        date_specific_data = [r for r in scraped_data if r.get('date') == target_date_str]
                        
                        if date_specific_data:
                            saved_count = self.db.save_multiple_draw_results(date_specific_data)
                            total_new_records += saved_count
                            print(f"       ✅ Guardados: {saved_count} registros")
                        else:
                            print(f"       ⚪ Sin datos específicos para esta fecha")
                    else:
                        print(f"       ❌ Sin respuesta del scraper")
                    
                    # Pausa entre fechas
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"       ❌ Error: {str(e)[:50]}...")
                    continue
            
            result['new_records'] = total_new_records
            result['status'] = 'completed'
            
            print(f"   📊 Total nuevos registros: {total_new_records}")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"   ❌ Error procesando año: {e}")
        
        result['processing_time'] = time.time() - start_time
        print(f"   ⏱️ Tiempo: {result['processing_time']:.1f}s")
        
        return result
    
    def _get_strategic_year_dates(self, year: int) -> list:
        """Obtiene fechas estratégicas para un año"""
        dates = []
        
        # 2 fechas por mes (medio y fin)
        for month in range(1, 13):
            try:
                # Fecha media del mes
                mid_date = datetime(year, month, 15)
                dates.append(mid_date)
                
                # Última fecha del mes
                if month == 12:
                    end_date = datetime(year, month, 31)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                dates.append(end_date)
                
            except ValueError:
                continue
        
        return dates
    
    def run_batch_collection(self, start_year: int = 2010, end_year: int = 2025) -> Dict[str, Any]:
        """Ejecuta la recopilación por lotes anuales"""
        print(f"🚀 RECOPILACIÓN SIMPLE POR LOTES ANUALES")
        print("=" * 50)
        print(f"📅 Años: {start_year} - {end_year}")
        
        # Cargar checkpoint
        checkpoint = self.load_checkpoint()
        processed_years = set(checkpoint.get('processed_years', []))
        
        # Determinar años pendientes (procesar desde más reciente)
        all_years = list(range(end_year, start_year - 1, -1))  # De más reciente a más antiguo
        pending_years = [y for y in all_years if y not in processed_years]
        
        if not pending_years:
            print("✅ Todos los años ya fueron procesados")
            return checkpoint
        
        print(f"📊 Años pendientes: {len(pending_years)}/{len(all_years)}")
        print(f"🎯 Lista: {pending_years}")
        
        results = checkpoint.get('year_results', [])
        total_new_records = checkpoint.get('total_new_records', 0)
        
        # Procesar cada año
        for i, year in enumerate(pending_years, 1):
            print(f"\n{'='*60}")
            print(f"🔄 PROCESANDO AÑO {i}/{len(pending_years)}: {year}")
            
            try:
                year_result = self.process_year_batch(year)
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
                print(f"\n📊 PROGRESO GENERAL: {progress:.1f}% ({i}/{len(pending_years)})")
                print(f"   📈 Nuevos registros totales: {total_new_records}")
                
                # Pausa entre años
                if i < len(pending_years):
                    print(f"   ⏸️ Pausa de 20s antes del siguiente año...")
                    time.sleep(20)
                
            except KeyboardInterrupt:
                print("\n⚠️ Proceso interrumpido por el usuario")
                break
            except Exception as e:
                print(f"❌ Error crítico en año {year}: {e}")
                continue
        
        # Resultados finales
        final_results = {
            'completed': True,
            'completion_date': datetime.now().isoformat(),
            'processed_years': list(processed_years),
            'total_years_processed': len(processed_years),
            'total_new_records': total_new_records,
            'year_results': results
        }
        
        self.save_checkpoint(final_results)
        
        print(f"\n🎉 RECOPILACIÓN POR LOTES COMPLETADA")
        print(f"   ✅ Años procesados: {len(processed_years)}")
        print(f"   📊 Nuevos registros: {total_new_records}")
        
        return final_results
    
    def show_final_stats(self):
        """Muestra estadísticas finales de la base de datos"""
        print(f"\n📋 ESTADÍSTICAS FINALES DE BASE DE DATOS")
        print("=" * 45)
        
        stats = self.db.get_database_stats()
        
        print(f"📊 Resumen:")
        print(f"   • Total registros: {stats['total_records']}")
        print(f"   • Fechas únicas: {stats['unique_dates']}")
        print(f"   • Rango temporal: {stats['earliest_date']} - {stats['latest_date']}")
        
        # Mostrar distribución por años recientes
        current_year = datetime.now().year
        for year in range(current_year, max(2020, current_year - 5), -1):
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            year_draws = self.db.get_draws_in_period(year_start, year_end)
            print(f"   • Año {year}: {len(year_draws)} registros")

def main():
    """Función principal"""
    collector = SimpleBatchCollector()
    
    print("🎯 Objetivo: Recopilar datos históricos por lotes anuales")
    print("📦 Estrategia: 2 fechas por mes, años más recientes primero")
    
    try:
        # Ejecutar recopilación
        results = collector.run_batch_collection(2010, 2025)
        
        # Mostrar estadísticas finales
        collector.show_final_stats()
        
        print(f"\n🎉 PROCESO COMPLETADO")
        return 0
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)