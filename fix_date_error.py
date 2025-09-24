#!/usr/bin/env python3
"""
Script para corregir automáticamente el error de fechas:
Los datos del día 22 están incorrectamente en el día 23
"""

import sqlite3
from datetime import datetime

def fix_date_error_automatic():
    """Corrige automáticamente el error: datos del día 22 puestos en día 23"""
    db_path = "quiniela_loteka.db"
    
    with sqlite3.connect(db_path) as conn:
        print("=== CORRECCIÓN AUTOMÁTICA DE ERROR DE FECHAS ===")
        
        cursor = conn.cursor()
        
        # Verificar situación actual
        cursor.execute("SELECT COUNT(*) FROM draw_results WHERE date = '2025-09-22'")
        count_22 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM draw_results WHERE date = '2025-09-23'")
        count_23 = cursor.fetchone()[0]
        
        print(f"   📅 Registros en 2025-09-22: {count_22}")
        print(f"   📅 Registros en 2025-09-23: {count_23}")
        
        # Si hay datos en 23 pero no en 22, mover automáticamente
        if count_23 > 0 and count_22 == 0:
            print("\n   🔧 CORRIGIENDO ERROR DE FECHA:")
            print("   Moviendo datos de 2025-09-23 a 2025-09-22...")
            
            # Obtener los datos que están mal fechados
            cursor.execute("""
                SELECT id, number, position, prize_amount, created_at
                FROM draw_results 
                WHERE date = '2025-09-23'
                ORDER BY position
            """)
            wrong_dated_data = cursor.fetchall()
            
            # Mostrar qué se va a mover
            print("   📋 Datos a mover:")
            for row in wrong_dated_data:
                print(f"      ID: {row[0]} | Núm: {row[1]} | Pos: {row[2]} | Creado: {row[4]}")
            
            # Actualizar la fecha de 2025-09-23 a 2025-09-22
            cursor.execute("""
                UPDATE draw_results 
                SET date = '2025-09-22' 
                WHERE date = '2025-09-23'
            """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Movidos {rows_updated} registros de 2025-09-23 a 2025-09-22")
            
            # Verificar el resultado
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE date = '2025-09-22'")
            new_count_22 = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE date = '2025-09-23'")
            new_count_23 = cursor.fetchone()[0]
            
            print(f"\n   📊 RESULTADO FINAL:")
            print(f"   📅 Registros en 2025-09-22: {new_count_22}")
            print(f"   📅 Registros en 2025-09-23: {new_count_23}")
            
            return True
        
        elif count_22 > 0 and count_23 > 0:
            print("\n   ⚠️ SITUACIÓN AMBIGUA:")
            print("   Hay datos tanto en 2025-09-22 como en 2025-09-23")
            print("   Se requiere revisión manual para determinar cuáles son correctos")
            return False
        
        elif count_22 > 0 and count_23 == 0:
            print("\n   ✅ FECHAS YA ESTÁN CORRECTAS:")
            print("   Los datos del 22 están en su fecha correcta")
            return True
        
        else:
            print("\n   ℹ️ NO HAY DATOS PARA CORREGIR")
            return True

def verify_recent_draws():
    """Verifica los últimos sorteos después de la corrección"""
    db_path = "quiniela_loteka.db"
    
    with sqlite3.connect(db_path) as conn:
        print("\n=== VERIFICACIÓN DE ÚLTIMOS SORTEOS ===")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, number, position, prize_amount
            FROM draw_results
            WHERE draw_type = 'quiniela'
            ORDER BY date DESC, position
            LIMIT 10
        """)
        recent_draws = cursor.fetchall()
        
        print("   📋 Últimos 10 sorteos en la base de datos:")
        for row in recent_draws:
            print(f"      📅 {row[0]} | Núm: {row[1]} | Pos: {row[2]} | Premio: {row[3]}")
        
        return recent_draws

if __name__ == "__main__":
    # Ejecutar corrección
    success = fix_date_error_automatic()
    
    # Verificar resultado
    verify_recent_draws()
    
    if success:
        print("\n🎉 CORRECCIÓN COMPLETADA EXITOSAMENTE")
        print("Los datos del día 22 ahora están en su fecha correcta")
        print("El día 23 queda disponible para los próximos resultados")
    else:
        print("\n⚠️ CORRECCIÓN REQUIERE REVISIÓN MANUAL")