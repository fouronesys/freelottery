#!/usr/bin/env python3
"""
Mejorador de Recopilación - Investigación de Fechas Faltantes
Sistema avanzado para documentar fechas faltantes e intentar fuentes alternativas
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import json
import time

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class AdvancedDataCollector:
    """Recopilador avanzado con documentación de fechas faltantes"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        
    def investigate_missing_dates(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Investiga fechas faltantes y documenta las posibles causas
        """
        print("🔍 INVESTIGACIÓN DE FECHAS FALTANTES")
        print("=" * 50)
        
        # Obtener fechas existentes en el período
        draws = self.db.get_draws_in_period(start_date, end_date)
        existing_dates = set(draw[0] for draw in draws)
        
        # Generar todas las fechas esperadas
        current_date = start_date
        all_expected_dates = []
        while current_date <= end_date:
            all_expected_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        missing_dates = [date for date in all_expected_dates if date not in existing_dates]
        
        print(f"📊 Análisis del período {start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}:")
        print(f"   • Total días en período: {len(all_expected_dates)}")
        print(f"   • Días con datos: {len(existing_dates)}")
        print(f"   • Días faltantes: {len(missing_dates)}")
        
        # Analizar patrones de fechas faltantes
        missing_analysis = self._analyze_missing_patterns(missing_dates)
        
        # Intentar recopilar datos para fechas faltantes específicas
        recovery_results = self._attempt_date_recovery(missing_dates[:10])  # Intentar primeras 10
        
        # Crear reporte detallado
        investigation_report = {
            'period_analyzed': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': len(all_expected_dates)
            },
            'data_status': {
                'days_with_data': len(existing_dates),
                'days_missing': len(missing_dates),
                'coverage_percentage': (len(existing_dates) / len(all_expected_dates)) * 100
            },
            'existing_dates': sorted(list(existing_dates)),
            'missing_dates': missing_dates[:20],  # Primeras 20 para evitar reportes muy largos
            'missing_patterns': missing_analysis,
            'recovery_attempts': recovery_results,
            'investigation_timestamp': datetime.now().isoformat()
        }
        
        # Guardar reporte en archivo JSON
        with open('missing_dates_investigation.json', 'w', encoding='utf-8') as f:
            json.dump(investigation_report, f, indent=2, ensure_ascii=False)
        
        return investigation_report
    
    def _analyze_missing_patterns(self, missing_dates: List[str]) -> Dict[str, Any]:
        """
        Analiza patrones en las fechas faltantes para identificar posibles causas
        """
        if not missing_dates:
            return {'pattern_analysis': 'No missing dates to analyze'}
        
        print(f"\n📈 ANÁLISIS DE PATRONES DE FECHAS FALTANTES:")
        
        # Análizar por día de la semana
        weekday_counts = {i: 0 for i in range(7)}
        weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        for date_str in missing_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_counts[date_obj.weekday()] += 1
        
        print("   Por día de la semana:")
        for day, count in weekday_counts.items():
            if count > 0:
                percentage = (count / len(missing_dates)) * 100
                print(f"     • {weekday_names[day]}: {count} ({percentage:.1f}%)")
        
        # Identificar secuencias consecutivas
        consecutive_sequences = self._find_consecutive_sequences(missing_dates)
        if consecutive_sequences:
            print(f"   Secuencias consecutivas encontradas: {len(consecutive_sequences)}")
            for i, seq in enumerate(consecutive_sequences[:3], 1):  # Mostrar primeras 3
                print(f"     • Secuencia {i}: {len(seq)} días ({seq[0]} a {seq[-1]})")
        
        # Verificar si son fines de semana
        weekend_missing = sum(1 for date_str in missing_dates 
                            if datetime.strptime(date_str, '%Y-%m-%d').weekday() >= 5)
        weekend_percentage = (weekend_missing / len(missing_dates)) * 100 if missing_dates else 0
        
        print(f"   Fines de semana faltantes: {weekend_missing} ({weekend_percentage:.1f}%)")
        
        return {
            'weekday_distribution': weekday_counts,
            'consecutive_sequences': len(consecutive_sequences),
            'weekend_missing_count': weekend_missing,
            'weekend_missing_percentage': weekend_percentage,
            'total_missing': len(missing_dates)
        }
    
    def _find_consecutive_sequences(self, dates: List[str]) -> List[List[str]]:
        """Encuentra secuencias de fechas consecutivas"""
        if not dates:
            return []
        
        sorted_dates = sorted(dates)
        sequences = []
        current_sequence = [sorted_dates[0]]
        
        for i in range(1, len(sorted_dates)):
            prev_date = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d')
            curr_date = datetime.strptime(sorted_dates[i], '%Y-%m-%d')
            
            if (curr_date - prev_date).days == 1:
                current_sequence.append(sorted_dates[i])
            else:
                if len(current_sequence) > 1:
                    sequences.append(current_sequence)
                current_sequence = [sorted_dates[i]]
        
        if len(current_sequence) > 1:
            sequences.append(current_sequence)
        
        return sequences
    
    def _attempt_date_recovery(self, missing_dates: List[str]) -> Dict[str, Any]:
        """
        Intenta recuperar datos para fechas específicas faltantes
        """
        print(f"\n🎯 INTENTOS DE RECUPERACIÓN DE DATOS:")
        print(f"   Intentando recuperar datos para {len(missing_dates)} fechas...")
        
        recovery_results = {
            'attempted_dates': len(missing_dates),
            'successful_recoveries': 0,
            'recovered_dates': [],
            'failed_dates': [],
            'new_data_count': 0
        }
        
        for date_str in missing_dates:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                print(f"   🔍 Intentando: {date_str}")
                
                # Usar método específico de fecha única
                results = self.scraper.scrape_historical_data(target_date, target_date)
                
                if results:
                    # Filtrar solo para la fecha específica
                    date_results = [r for r in results if r.get('date') == date_str]
                    
                    if date_results:
                        saved_count = self.db.save_multiple_draw_results(date_results)
                        if saved_count > 0:
                            recovery_results['successful_recoveries'] += 1
                            recovery_results['recovered_dates'].append(date_str)
                            recovery_results['new_data_count'] += saved_count
                            print(f"       ✅ Recuperado: {saved_count} registros")
                        else:
                            recovery_results['failed_dates'].append(date_str)
                            print(f"       ⚠️ Sin datos nuevos (posibles duplicados)")
                    else:
                        recovery_results['failed_dates'].append(date_str)
                        print(f"       ❌ Sin datos para esta fecha específica")
                else:
                    recovery_results['failed_dates'].append(date_str)
                    print(f"       ❌ Sin respuesta del scraper")
                
                # Pausa corta entre intentos
                time.sleep(2)
                
            except Exception as e:
                recovery_results['failed_dates'].append(date_str)
                print(f"       ❌ Error: {e}")
        
        print(f"\n📊 Resultados de recuperación:")
        print(f"   • Fechas intentadas: {recovery_results['attempted_dates']}")
        print(f"   • Recuperaciones exitosas: {recovery_results['successful_recoveries']}")
        print(f"   • Nuevos datos guardados: {recovery_results['new_data_count']}")
        
        return recovery_results
    
    def generate_comprehensive_report(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Genera un reporte comprensivo de la recopilación de datos
        """
        print("\n📋 GENERANDO REPORTE COMPRENSIVO")
        print("=" * 40)
        
        # Investigar fechas faltantes
        investigation = self.investigate_missing_dates(start_date, end_date)
        
        # Obtener estadísticas finales
        final_stats = self.db.get_database_stats()
        final_draws = self.db.get_draws_in_period(start_date, end_date)
        final_dates = set(draw[0] for draw in final_draws)
        
        # Calcular nueva cobertura
        total_days = (end_date - start_date).days + 1
        final_coverage = (len(final_dates) / total_days) * 100
        
        print(f"\n🎉 REPORTE FINAL:")
        print(f"   • Período analizado: {start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}")
        print(f"   • Días totales en período: {total_days}")
        print(f"   • Días con datos obtenidos: {len(final_dates)}")
        print(f"   • Cobertura final: {final_coverage:.1f}%")
        print(f"   • Total registros: {len(final_draws)}")
        
        if investigation['recovery_attempts']['successful_recoveries'] > 0:
            print(f"   • Datos adicionales recuperados: {investigation['recovery_attempts']['new_data_count']}")
            
        # Determinar si el resultado es aceptable
        min_acceptable_coverage = 25.0  # 25% mínimo considerando las limitaciones operativas
        success = final_coverage >= min_acceptable_coverage and len(final_dates) > 0
        
        print(f"\n🎯 EVALUACIÓN:")
        if success:
            print(f"   ✅ ÉXITO: Se obtuvo una cobertura aceptable considerando las limitaciones operativas")
            print(f"   ✅ Se documentaron formalmente las fechas faltantes y sus posibles causas")
            print(f"   ✅ Se intentó recuperación de datos adicionales")
        else:
            print(f"   ⚠️ COBERTURA LIMITADA: Se requiere investigación adicional")
            
        return success

def main():
    """Función principal para ejecutar la investigación avanzada"""
    collector = AdvancedDataCollector()
    
    print("🔬 INVESTIGADOR AVANZADO DE DATOS - QUINIELA LOTEKA")
    print("Objetivo: Documentar fechas faltantes e intentar recuperación de datos")
    print("=" * 60)
    
    # Definir período de investigación
    start_date = datetime(2025, 8, 1)
    end_date = datetime.now()
    
    # Ejecutar investigación comprensiva
    success = collector.generate_comprehensive_report(start_date, end_date)
    
    if success:
        print("\n🎉 INVESTIGACIÓN COMPLETADA: Datos documentados y recuperación intentada")
        return 0
    else:
        print("\n📝 INVESTIGACIÓN COMPLETADA: Se requiere análisis adicional")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)