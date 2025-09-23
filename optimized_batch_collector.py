#!/usr/bin/env python3
"""
Recopilador Optimizado por Lotes - Quiniela Loteka
Versión optimizada para procesamiento eficiente de datos históricos masivos
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

class OptimizedBatchCollector:
    """Recopilador optimizado por lotes para datos históricos"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        self.checkpoint_file = "optimized_collection_checkpoint.json"
        
        # Configuración optimizada
        self.batch_size_months = 6  # 6 meses por lote
        self.max_samples_per_month = 5  # Máximo 5 fechas de muestra por mes
        self.pause_between_batches = 15  # 15 segundos entre lotes
        
    def load_checkpoint(self) -> Dict[str, Any]:
        """Carga el checkpoint existente"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error cargando checkpoint: {e}")
        return {}
    
    def save_checkpoint(self, data: Dict[str, Any]):
        """Guarda el checkpoint actual"""
        data['last_update'] = datetime.now().isoformat()
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando checkpoint: {e}")
    
    def generate_optimized_batches(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Genera lotes optimizados por períodos de meses"""
        batches = []
        current_date = start_date
        batch_id = 1
        
        while current_date <= end_date:
            # Calcular fin del lote (6 meses después)
            batch_end = current_date + timedelta(days=180)  # ~6 meses
            if batch_end > end_date:
                batch_end = end_date
            
            # Priorizar períodos más recientes
            priority = self._calculate_batch_priority(current_date, end_date)
            
            batch = {
                'id': batch_id,
                'start_date': current_date,
                'end_date': batch_end,
                'priority': priority,
                'total_days': (batch_end - current_date).days + 1
            }
            
            batches.append(batch)
            current_date = batch_end + timedelta(days=1)
            batch_id += 1
        
        # Ordenar por prioridad (más reciente primero)
        batches.sort(key=lambda x: x['priority'], reverse=True)
        
        print(f"📦 Generados {len(batches)} lotes optimizados")
        return batches
    
    def _calculate_batch_priority(self, batch_date: datetime, end_date: datetime) -> float:
        """Calcula la prioridad del lote (más reciente = mayor prioridad)"""
        days_from_end = (end_date - batch_date).days
        max_days = (end_date - datetime(2010, 8, 1)).days
        return (max_days - days_from_end) / max_days
    
    def process_optimized_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un lote de manera optimizada"""
        start_date = batch['start_date']
        end_date = batch['end_date']
        
        print(f"\n📦 LOTE {batch['id']} - Prioridad: {batch['priority']:.2f}")
        print(f"   📅 {start_date.strftime('%m/%Y')} - {end_date.strftime('%m/%Y')}")
        print(f"   📊 {batch['total_days']} días")
        
        batch_results = {
            'batch_id': batch['id'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'priority': batch['priority'],
            'records_collected': 0,
            'dates_with_data': 0,
            'processing_time': 0,
            'success': False
        }
        
        start_time = time.time()
        
        try:
            # Usar muestreo estratégico en lugar de todas las fechas
            sample_dates = self._generate_strategic_sample_dates(start_date, end_date)
            print(f"   🎯 Muestreando {len(sample_dates)} fechas estratégicas")
            
            total_records = 0
            unique_dates = set()
            
            for sample_date in sample_dates:
                try:
                    # Intentar una sola fecha específica
                    results = self.scraper.scrape_historical_data(sample_date, sample_date)
                    
                    if results:
                        # Filtrar para la fecha específica
                        date_results = [r for r in results if r.get('date') == sample_date.strftime('%Y-%m-%d')]
                        
                        if date_results:
                            saved = self.db.save_multiple_draw_results(date_results)
                            total_records += saved
                            unique_dates.add(sample_date.strftime('%Y-%m-%d'))
                            print(f"     ✅ {sample_date.strftime('%d-%m-%Y')}: {saved} registros")
                        else:
                            print(f"     ⚪ {sample_date.strftime('%d-%m-%Y')}: Sin datos específicos")
                    
                    # Pausa corta entre fechas
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"     ❌ {sample_date.strftime('%d-%m-%Y')}: Error - {e}")
                    continue
            
            batch_results['records_collected'] = total_records
            batch_results['dates_with_data'] = len(unique_dates)
            batch_results['success'] = total_records > 0
            
            print(f"   📊 Resultados: {total_records} registros en {len(unique_dates)} fechas")
            
        except Exception as e:
            print(f"   ❌ Error en lote: {e}")
            batch_results['error'] = str(e)
        
        batch_results['processing_time'] = time.time() - start_time
        return batch_results
    
    def _generate_strategic_sample_dates(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Genera fechas de muestra estratégicas para el período"""
        sample_dates = []
        current_month = start_date.replace(day=1)
        
        while current_month <= end_date:
            # Obtener fechas de muestra para este mes
            month_end = (current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_samples = self._get_month_sample_dates(current_month, min(month_end, end_date))
            sample_dates.extend(month_samples)
            
            # Avanzar al siguiente mes
            current_month = (current_month + timedelta(days=32)).replace(day=1)
        
        return sample_dates
    
    def _get_month_sample_dates(self, month_start: datetime, month_end: datetime) -> List[datetime]:
        """Obtiene fechas de muestra estratégicas para un mes"""
        samples = []
        days_in_month = (month_end - month_start).days + 1
        
        if days_in_month <= 5:
            # Mes pequeño, tomar todas las fechas
            current = month_start
            while current <= month_end:
                samples.append(current)
                current += timedelta(days=1)
        else:
            # Muestreo estratégico: principio, medio, fin del mes
            samples.extend([
                month_start,  # Primer día
                month_start + timedelta(days=days_in_month // 4),  # Primer cuarto
                month_start + timedelta(days=days_in_month // 2),  # Medio
                month_start + timedelta(days=3 * days_in_month // 4),  # Tercer cuarto
                month_end  # Último día
            ])
        
        return samples
    
    def run_optimized_collection(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Ejecuta la recopilación optimizada"""
        print(f"🚀 RECOPILACIÓN OPTIMIZADA POR LOTES")
        print("=" * 50)
        print(f"📅 Período: {start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}")
        print(f"📦 Estrategia: Lotes de 6 meses con muestreo estratégico")
        
        # Cargar checkpoint
        checkpoint = self.load_checkpoint()
        
        # Generar lotes optimizados
        batches = self.generate_optimized_batches(start_date, end_date)
        
        # Filtrar lotes ya procesados
        processed_batches = set(checkpoint.get('completed_batch_ids', []))
        pending_batches = [b for b in batches if b['id'] not in processed_batches]
        
        if not pending_batches:
            print("✅ Todos los lotes ya fueron procesados")
            return checkpoint.get('final_results', {})
        
        print(f"📊 Lotes pendientes: {len(pending_batches)}/{len(batches)}")
        
        # Procesar lotes
        session_results = {
            'session_start': datetime.now().isoformat(),
            'total_batches': len(batches),
            'pending_batches': len(pending_batches),
            'completed_batches': 0,
            'total_records': 0,
            'total_dates': 0,
            'batch_results': checkpoint.get('batch_results', [])
        }
        
        for i, batch in enumerate(pending_batches, 1):
            print(f"\n{'='*60}")
            print(f"🔄 PROCESANDO LOTE {i}/{len(pending_batches)}")
            
            try:
                batch_result = self.process_optimized_batch(batch)
                session_results['batch_results'].append(batch_result)
                session_results['completed_batches'] += 1
                session_results['total_records'] += batch_result['records_collected']
                session_results['total_dates'] += batch_result['dates_with_data']
                
                # Actualizar checkpoint
                completed_ids = checkpoint.get('completed_batch_ids', [])
                completed_ids.append(batch['id'])
                checkpoint_data = {
                    'completed_batch_ids': completed_ids,
                    'session_results': session_results,
                    'last_processed_batch': batch['id']
                }
                self.save_checkpoint(checkpoint_data)
                
                # Mostrar progreso
                progress = (i / len(pending_batches)) * 100
                print(f"\n📊 PROGRESO: {progress:.1f}% ({i}/{len(pending_batches)})")
                print(f"   📈 Registros totales: {session_results['total_records']}")
                print(f"   📅 Fechas con datos: {session_results['total_dates']}")
                
                # Pausa entre lotes
                if i < len(pending_batches):
                    print(f"   ⏸️ Pausa de {self.pause_between_batches}s...")
                    time.sleep(self.pause_between_batches)
                
            except KeyboardInterrupt:
                print("\n⚠️ Proceso interrumpido por el usuario")
                return session_results
            except Exception as e:
                print(f"❌ Error en lote {batch['id']}: {e}")
                continue
        
        # Finalizar
        session_results['session_end'] = datetime.now().isoformat()
        session_results['completed'] = True
        
        final_checkpoint = {
            'completed': True,
            'completion_date': datetime.now().isoformat(),
            'final_results': session_results
        }
        self.save_checkpoint(final_checkpoint)
        
        print(f"\n🎉 RECOPILACIÓN OPTIMIZADA COMPLETADA")
        print(f"   ✅ Lotes procesados: {len(pending_batches)}")
        print(f"   📊 Total registros: {session_results['total_records']}")
        print(f"   📅 Total fechas: {session_results['total_dates']}")
        
        return session_results

def main():
    """Función principal"""
    collector = OptimizedBatchCollector()
    
    # Rango de 15 años
    start_date = datetime(2010, 8, 1)
    end_date = datetime.now()
    
    print(f"🎯 Recopilación de {(end_date - start_date).days + 1} días con muestreo estratégico")
    
    try:
        results = collector.run_optimized_collection(start_date, end_date)
        
        # Mostrar estadísticas finales
        stats = collector.db.get_database_stats()
        print(f"\n📋 ESTADÍSTICAS FINALES DE BD:")
        print(f"   • Total registros: {stats['total_records']}")
        print(f"   • Fechas únicas: {stats['unique_dates']}")
        print(f"   • Rango: {stats['earliest_date']} - {stats['latest_date']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)