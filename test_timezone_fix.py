#!/usr/bin/env python3
"""
Test rápido para verificar que las correcciones de zona horaria funcionan
"""

from timezone_utils import get_dominican_now, get_dominican_today_str, is_data_current
from automated_collector import AutomatedLotteryCollector
from database import DatabaseManager

def test_timezone_functions():
    """Verifica que las funciones de zona horaria funcionan correctamente"""
    print("🧪 PROBANDO FUNCIONES DE ZONA HORARIA")
    print("=" * 45)
    
    # Probar funciones básicas
    dominican_now = get_dominican_now()
    dominican_today = get_dominican_today_str()
    
    print(f"   • Hora dominicana: {dominican_now}")
    print(f"   • Fecha dominicana: {dominican_today}")
    print(f"   • Zona horaria: {dominican_now.tzinfo}")

def test_data_current_check():
    """Verifica la función de verificación de datos actuales"""
    print(f"\n🧪 PROBANDO VERIFICACIÓN DE DATOS ACTUALES")
    print("=" * 50)
    
    db = DatabaseManager()
    stats = db.get_database_stats()
    
    if stats['latest_date']:
        is_current = is_data_current(stats['latest_date'])
        print(f"   • Última fecha en BD: {stats['latest_date']}")
        print(f"   • Fecha actual (RD): {get_dominican_today_str()}")
        print(f"   • ¿Datos actuales?: {is_current}")
    else:
        print("   • No hay datos en la base de datos")

def test_automated_collector():
    """Verifica que el recopilador automatizado use zona horaria correcta"""
    print(f"\n🧪 PROBANDO RECOPILADOR AUTOMATIZADO")
    print("=" * 45)
    
    collector = AutomatedLotteryCollector()
    
    # Test de fill_missing_dates con zona horaria
    result = collector.fill_missing_dates()
    
    print(f"   • Resultado: {result['action']}")
    print(f"   • Éxito: {result['success']}")

if __name__ == "__main__":
    print("🚀 VERIFICANDO CORRECCIONES DE ZONA HORARIA")
    print("=" * 55)
    
    try:
        test_timezone_functions()
        test_data_current_check()
        test_automated_collector()
        
        print(f"\n✅ TODAS LAS PRUEBAS COMPLETADAS")
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()