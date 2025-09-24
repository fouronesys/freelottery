#!/usr/bin/env python3
"""
Script para actualizar los datos hasta la fecha actual
"""

from datetime import datetime
from automated_collector import AutomatedLotteryCollector
from database import DatabaseManager

def update_to_current_date():
    """Actualiza los datos hasta la fecha actual"""
    print("🚀 ACTUALIZANDO DATOS HASTA LA FECHA ACTUAL")
    print("=" * 50)
    
    # Verificar estado inicial
    db = DatabaseManager()
    initial_stats = db.get_database_stats()
    print(f"📊 Estado inicial:")
    print(f"   • Total registros: {initial_stats['total_records']:,}")
    print(f"   • Última fecha: {initial_stats['latest_date']}")
    
    # Usar el recopilador automatizado
    collector = AutomatedLotteryCollector()
    
    print(f"\n🔍 Verificando y llenando fechas faltantes...")
    result = collector.fill_missing_dates()
    
    if result['success']:
        if result['action'] == 'no_gaps_found':
            print("✅ Los datos ya están actualizados")
        elif result['action'] == 'gap_filled':
            print(f"✅ Vacío llenado exitosamente:")
            print(f"   • Registros guardados: {result['records_saved']}")
            print(f"   • Rango actualizado: {result['date_range']}")
        else:
            print(f"✅ Acción completada: {result['action']}")
    else:
        print(f"❌ Error en la actualización: {result.get('error', 'Error desconocido')}")
        return False
    
    # Verificar estado final
    final_stats = db.get_database_stats()
    print(f"\n📊 Estado final:")
    print(f"   • Total registros: {final_stats['total_records']:,} (+{final_stats['total_records'] - initial_stats['total_records']})")
    print(f"   • Última fecha: {final_stats['latest_date']}")
    
    # Verificar si estamos al día
    if final_stats['latest_date']:
        latest_date = datetime.strptime(final_stats['latest_date'], '%Y-%m-%d')
        today = datetime.now()
        days_behind = (today - latest_date).days
        
        if days_behind <= 1:
            print("🎉 ¡DATOS COMPLETAMENTE ACTUALIZADOS!")
        else:
            print(f"⚠️ Aún faltan {days_behind} días")
    
    return True

if __name__ == "__main__":
    update_to_current_date()