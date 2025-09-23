#!/usr/bin/env python3
"""
Recopilador de Datos Históricos de Quiniela Loteka
Sistema mejorado para obtener al menos 720 días de datos históricos
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time

# Importar nuestros módulos
from database import DatabaseManager
from scraper import QuinielaScraperManager

class HistoricalDataCollector:
    """Clase principal para coordinar la recopilación masiva de datos históricos"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = QuinielaScraperManager()
        
    def collect_720_days_data(self) -> bool:
        """
        Función principal para recopilar 720+ días de datos históricos
        
        Returns:
            bool: True si la recopilación fue exitosa
        """
        print("🎯 INICIANDO RECOPILACIÓN MASIVA DE DATOS HISTÓRICOS DE QUINIELA LOTEKA")
        print("=" * 70)
        
        # Verificar estado actual
        initial_stats = self.db.get_database_stats()
        print(f"📊 Estado inicial de la base de datos:")
        print(f"   • Total registros: {initial_stats['total_records']}")
        print(f"   • Fechas únicas: {initial_stats['unique_dates']}")
        print(f"   • Rango de días: {initial_stats['date_range_days']}")
        print(f"   • ¿Tiene 720+ días?: {'✅ Sí' if initial_stats['has_720_days'] else '❌ No'}")
        
        if initial_stats['has_720_days']:
            print("🎉 ¡Ya tenemos 720+ días de datos!")
            return True
        
        # Calcular días faltantes
        target_days = 720
        days_needed = max(0, target_days - initial_stats['date_range_days'])
        
        print(f"\n🎯 OBJETIVO: Recopilar {target_days} días de datos históricos")
        print(f"📈 Días adicionales necesarios: {days_needed}")
        
        start_time = datetime.now()
        
        try:
            # Recopilar datos históricos masivos
            print("\n🚀 Iniciando recopilación de datos...")
            historical_results = self.scraper.scrape_massive_historical_data(target_days)
            
            if not historical_results:
                print("❌ No se pudieron obtener datos históricos")
                return False
            
            # Guardar datos en la base de datos
            print(f"\n💾 Guardando {len(historical_results)} registros en la base de datos...")
            saved_count = self.db.save_multiple_draw_results(historical_results)
            
            # Verificar resultado final
            final_stats = self.db.get_database_stats()
            
            print("\n🎉 RECOPILACIÓN COMPLETADA")
            print("=" * 50)
            print(f"📊 Estado final de la base de datos:")
            print(f"   • Total registros: {final_stats['total_records']} (+{final_stats['total_records'] - initial_stats['total_records']})")
            print(f"   • Fechas únicas: {final_stats['unique_dates']} (+{final_stats['unique_dates'] - initial_stats['unique_dates']})")
            print(f"   • Rango de días: {final_stats['date_range_days']} (+{final_stats['date_range_days'] - initial_stats['date_range_days']})")
            print(f"   • ¿Tiene 720+ días?: {'✅ Sí' if final_stats['has_720_days'] else '❌ No'}")
            print(f"   • Registros guardados: {saved_count}")
            
            # Estadísticas de tiempo
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"   • Tiempo transcurrido: {duration:.1f} segundos")
            
            # Determinar éxito
            success = final_stats['has_720_days'] and saved_count > 0
            
            if success:
                print("\n🎉 ¡ÉXITO! Sistema ahora tiene 720+ días de datos históricos")
                print("📈 Las predicciones tendrán mayor precisión con este volumen de datos")
            else:
                print("\n⚠️ Recopilación parcial - se necesitan más datos")
                
            return success
            
        except Exception as e:
            print(f"❌ Error durante la recopilación: {e}")
            return False
    
    def verify_data_quality(self) -> Dict[str, Any]:
        """
        Verifica la calidad de los datos recopilados
        """
        print("\n🔍 VERIFICANDO CALIDAD DE DATOS...")
        
        stats = self.db.get_database_stats()
        quality_report = {
            'total_records': stats['total_records'],
            'unique_dates': stats['unique_dates'],
            'date_range_days': stats['date_range_days'],
            'has_minimum_data': stats['has_720_days'],
            'data_density': 0,
            'issues': []
        }
        
        if stats['total_records'] > 0 and stats['unique_dates'] > 0:
            # Calcular densidad de datos (registros por día)
            quality_report['data_density'] = stats['total_records'] / stats['unique_dates']
            
            # Verificar densidad esperada (3 números por día = 3 registros por día)
            expected_density = 3.0
            if quality_report['data_density'] < expected_density * 0.8:  # 80% del esperado
                quality_report['issues'].append("Baja densidad de datos - posibles días faltantes")
            
            # Verificar rango de fechas
            if stats['date_range_days'] < 720:
                days_missing = 720 - stats['date_range_days']
                quality_report['issues'].append(f"Faltan {days_missing} días para alcanzar el objetivo de 720 días")
        
        print(f"   ✅ Registros totales: {quality_report['total_records']}")
        print(f"   ✅ Fechas únicas: {quality_report['unique_dates']}")
        print(f"   ✅ Rango de días: {quality_report['date_range_days']}")
        print(f"   ✅ Densidad de datos: {quality_report['data_density']:.2f} registros/día")
        print(f"   ✅ Objetivo 720+ días: {'✅ Cumplido' if quality_report['has_minimum_data'] else '❌ Pendiente'}")
        
        if quality_report['issues']:
            print("   ⚠️ Problemas detectados:")
            for issue in quality_report['issues']:
                print(f"      • {issue}")
        else:
            print("   🎉 ¡Calidad de datos excelente!")
            
        return quality_report

def main():
    """Función principal para ejecutar la recopilación de datos"""
    collector = HistoricalDataCollector()
    
    print("🎯 RECOPILADOR DE DATOS HISTÓRICOS - QUINIELA LOTEKA")
    print("Objetivo: Obtener al menos 720 días de datos para mejorar predicciones")
    print("=" * 70)
    
    # Recopilar datos
    success = collector.collect_720_days_data()
    
    # Verificar calidad
    quality_report = collector.verify_data_quality()
    
    # Resultado final
    if success and quality_report['has_minimum_data']:
        print("\n🎉 MISIÓN CUMPLIDA: Sistema listo con 720+ días de datos históricos")
        return 0
    else:
        print("\n⚠️ RECOPILACIÓN PARCIAL: Se necesita más trabajo para obtener todos los datos")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)