#!/usr/bin/env python3
"""
Recopilador de Datos Específico - Quiniela Loteka
Sistema especializado para recopilar datos históricos desde 01-08-2025 hasta la actualidad
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class SpecificDataCollector:
    """Clase para recopilar datos históricos desde una fecha específica"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        
    def collect_data_from_august_2025(self) -> bool:
        """
        Recopilar datos específicamente desde 01-08-2025 hasta la fecha actual
        
        Returns:
            bool: True si la recopilación fue exitosa
        """
        print("🎯 INICIANDO RECOPILACIÓN DE DATOS DESDE 01-08-2025")
        print("=" * 60)
        
        # Definir fechas específicas
        start_date = datetime(2025, 8, 1)  # 01-08-2025
        end_date = datetime.now()          # Fecha actual
        
        days_to_collect = (end_date - start_date).days + 1
        
        print(f"📅 Fecha de inicio: {start_date.strftime('%d-%m-%Y')}")
        print(f"📅 Fecha de fin: {end_date.strftime('%d-%m-%Y')}")
        print(f"📊 Total de días a recopilar: {days_to_collect} días")
        
        # Verificar estado actual de la base de datos
        initial_stats = self.db.get_database_stats()
        print(f"\n📊 Estado inicial de la base de datos:")
        print(f"   • Total registros: {initial_stats['total_records']}")
        print(f"   • Fechas únicas: {initial_stats['unique_dates']}")
        print(f"   • Rango de días: {initial_stats['date_range_days']}")
        
        start_time = datetime.now()
        
        try:
            # Recopilar datos históricos desde la fecha específica
            print(f"\n🚀 Iniciando recopilación de datos desde {start_date.strftime('%d-%m-%Y')}...")
            
            # Usar el método de recopilación masiva con fechas específicas
            historical_results = self.scraper.scrape_historical_data_massive(start_date, end_date)
            
            if not historical_results:
                print("❌ No se pudieron obtener datos históricos")
                print("🔍 Intentando con método alternativo...")
                
                # Intentar con método alternativo
                historical_results = self.scraper.scrape_historical_data(start_date, end_date)
                
                if not historical_results:
                    print("❌ No se pudieron obtener datos con ningún método")
                    return False
            
            print(f"✅ Se obtuvieron {len(historical_results)} registros de datos (antes del filtrado)")
            
            # FILTRADO CRÍTICO: Asegurar que SOLO se guarden datos del rango solicitado
            filtered_results = self._filter_results_by_date_range(historical_results, start_date, end_date)
            print(f"📊 Después del filtrado: {len(filtered_results)} registros válidos para el rango {start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}")
            
            if not filtered_results:
                print("❌ No hay registros válidos después del filtrado por fechas")
                return False
            
            # Guardar datos filtrados en la base de datos
            print(f"\n💾 Guardando {len(filtered_results)} registros filtrados en la base de datos...")
            saved_count = self.db.save_multiple_draw_results(filtered_results)
            
            # Verificar resultado final
            final_stats = self.db.get_database_stats()
            
            print("\n🎉 RECOPILACIÓN COMPLETADA")
            print("=" * 50)
            print(f"📊 Estado final de la base de datos:")
            print(f"   • Total registros: {final_stats['total_records']} (+{final_stats['total_records'] - initial_stats['total_records']})")
            print(f"   • Fechas únicas: {final_stats['unique_dates']} (+{final_stats['unique_dates'] - initial_stats['unique_dates']})")
            print(f"   • Rango de días: {final_stats['date_range_days']} (+{final_stats['date_range_days'] - initial_stats['date_range_days']})")
            print(f"   • Registros guardados exitosamente: {saved_count}")
            
            # Estadísticas de tiempo
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"   • Tiempo transcurrido: {duration:.1f} segundos")
            
            # Verificar cobertura de fechas objetivo
            coverage_success = self._verify_date_coverage(start_date, end_date)
            
            success = saved_count > 0 and coverage_success
            
            if success:
                print(f"\n🎉 ¡ÉXITO! Se recopilaron datos desde {start_date.strftime('%d-%m-%Y')}")
                print(f"📈 Base de datos actualizada con {saved_count} nuevos registros")
                
                # Mostrar resumen de datos por mes
                self._show_monthly_summary(start_date, end_date)
                
            else:
                print("\n⚠️ Recopilación parcial - revisar logs para más detalles")
                
            return success
            
        except Exception as e:
            print(f"❌ Error durante la recopilación: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _filter_results_by_date_range(self, results: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Filtra los resultados para asegurar que SOLO están en el rango de fechas solicitado
        
        Args:
            results: Lista de resultados obtenidos del scraper
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            Lista filtrada de resultados dentro del rango de fechas
        """
        filtered = []
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"🔍 Filtrando resultados para el rango: {start_str} - {end_str}")
        
        dates_found = set()
        for result in results:
            result_date_str = result.get('date', '')
            
            # Verificar que la fecha esté en el formato correcto y en el rango
            try:
                # Convertir la fecha del resultado a datetime para comparación
                result_date = datetime.strptime(result_date_str, '%Y-%m-%d')
                
                # Verificar que esté dentro del rango solicitado
                if start_date <= result_date <= end_date:
                    filtered.append(result)
                    dates_found.add(result_date_str)
                else:
                    # Log de fechas fuera del rango (para debugging)
                    if len(dates_found) < 5:  # Mostrar solo las primeras 5 para evitar spam
                        print(f"⚠️ Fecha fuera del rango descartada: {result_date_str}")
                        
            except (ValueError, TypeError):
                print(f"❌ Fecha inválida encontrada y descartada: {result_date_str}")
                continue
        
        print(f"✅ Filtrado completado: {len(filtered)} registros válidos de {len(results)} originales")
        
        if dates_found:
            sorted_dates = sorted(list(dates_found))
            print(f"📅 Fechas válidas encontradas: desde {sorted_dates[0]} hasta {sorted_dates[-1]}")
            print(f"📊 Total de fechas únicas: {len(dates_found)}")
        
        return filtered
    
    def _verify_date_coverage(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Verifica que se hayan obtenido datos para el rango de fechas solicitado
        """
        print("\n🔍 VERIFICANDO COBERTURA DE FECHAS...")
        
        # Obtener datos del rango específico
        draws = self.db.get_draws_in_period(start_date, end_date)
        
        if not draws:
            print("❌ No se encontraron datos en el rango especificado")
            return False
        
        # Extraer fechas únicas de los resultados
        dates_with_data = set()
        for draw in draws:
            date_str = draw[0]  # Primera columna es la fecha
            dates_with_data.add(date_str)
        
        total_days_expected = (end_date - start_date).days + 1
        days_with_data = len(dates_with_data)
        coverage_percentage = (days_with_data / total_days_expected) * 100
        
        print(f"   ✅ Días esperados: {total_days_expected}")
        print(f"   ✅ Días con datos: {days_with_data}")
        print(f"   ✅ Cobertura: {coverage_percentage:.1f}%")
        
        # Mostrar fechas con datos más recientes
        if dates_with_data:
            sorted_dates = sorted(dates_with_data, reverse=True)[:5]
            print(f"   ✅ Fechas más recientes con datos: {', '.join(sorted_dates)}")
        
        # Considerar éxito si tenemos al menos 50% de cobertura
        success = coverage_percentage >= 50
        
        if success:
            print("   🎉 ¡Cobertura de fechas satisfactoria!")
        else:
            print("   ⚠️ Cobertura de fechas limitada")
        
        return success
    
    def _show_monthly_summary(self, start_date: datetime, end_date: datetime):
        """
        Muestra un resumen mensual de los datos recopilados
        """
        print("\n📊 RESUMEN MENSUAL DE DATOS RECOPILADOS:")
        print("-" * 45)
        
        current_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current_month <= end_month:
            month_start = current_month
            if current_month.month == 12:
                month_end = current_month.replace(year=current_month.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = current_month.replace(month=current_month.month + 1) - timedelta(days=1)
            
            # Ajustar fechas límite
            month_start = max(month_start, start_date)
            month_end = min(month_end, end_date)
            
            # Obtener datos del mes
            month_draws = self.db.get_draws_in_period(month_start, month_end)
            unique_dates = set(draw[0] for draw in month_draws)
            
            days_in_range = (month_end - month_start).days + 1
            days_with_data = len(unique_dates)
            
            month_name = month_start.strftime("%B %Y")
            print(f"   {month_name}: {days_with_data}/{days_in_range} días ({len(month_draws)} registros)")
            
            # Avanzar al siguiente mes
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

def main():
    """Función principal para ejecutar la recopilación de datos específica"""
    collector = SpecificDataCollector()
    
    print("🎯 RECOPILADOR DE DATOS ESPECÍFICO - QUINIELA LOTEKA")
    print("Objetivo: Recopilar datos desde 01-08-2025 hasta la actualidad")
    print("=" * 60)
    
    # Recopilar datos desde fecha específica
    success = collector.collect_data_from_august_2025()
    
    # Resultado final
    if success:
        print("\n🎉 MISIÓN CUMPLIDA: Datos recopilados exitosamente desde 01-08-2025")
        return 0
    else:
        print("\n⚠️ RECOPILACIÓN INCOMPLETA: Revisar logs y reintentar si es necesario")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)