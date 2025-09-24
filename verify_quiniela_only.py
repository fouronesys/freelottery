#!/usr/bin/env python3
"""
Script para verificar que todos los sorteos sean exclusivamente de Quiniela Loteka
"""

import sqlite3
import pandas as pd
from datetime import datetime
from database import DatabaseManager

def analyze_lottery_types():
    """Analiza todos los tipos de sorteos en la base de datos"""
    print("🔍 VERIFICANDO TIPOS DE SORTEOS EN LA BASE DE DATOS")
    print("=" * 55)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Verificar tipos de sorteos (draw_type)
            cursor.execute("""
            SELECT draw_type, COUNT(*) as count 
            FROM draw_results 
            GROUP BY draw_type 
            ORDER BY count DESC
            """)
            
            draw_types = cursor.fetchall()
            
            print(f"📊 TIPOS DE SORTEOS ENCONTRADOS:")
            print("   Tipo                | Cantidad")
            print("   " + "-" * 35)
            
            total_records = 0
            non_quiniela_count = 0
            
            for draw_type, count in draw_types:
                status = "✅" if draw_type == 'quiniela' else "⚠️"
                print(f"   {status} {draw_type:<15} | {count:,}")
                total_records += count
                
                if draw_type != 'quiniela':
                    non_quiniela_count += count
            
            print(f"\n📈 RESUMEN:")
            print(f"   • Total registros: {total_records:,}")
            print(f"   • Registros Quiniela: {total_records - non_quiniela_count:,}")
            print(f"   • Registros NO Quiniela: {non_quiniela_count:,}")
            
            return draw_types, non_quiniela_count
            
    except sqlite3.Error as e:
        print(f"❌ Error analizando tipos: {e}")
        return [], 0

def analyze_number_ranges():
    """Analiza los rangos de números para verificar que sean de Quiniela (0-99)"""
    print(f"\n🔍 VERIFICANDO RANGOS DE NÚMEROS")
    print("=" * 35)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Verificar rango de números
            cursor.execute("""
            SELECT 
                MIN(number) as min_number,
                MAX(number) as max_number,
                COUNT(CASE WHEN number < 0 OR number > 99 THEN 1 END) as out_of_range
            FROM draw_results
            """)
            
            min_num, max_num, out_of_range = cursor.fetchone()
            
            print(f"   • Número mínimo: {min_num}")
            print(f"   • Número máximo: {max_num}")
            print(f"   • Fuera de rango (0-99): {out_of_range}")
            
            if min_num >= 0 and max_num <= 99 and out_of_range == 0:
                print("   ✅ Todos los números están en rango válido de Quiniela (0-99)")
            else:
                print("   ⚠️ Hay números fuera del rango de Quiniela")
                
                # Mostrar números fuera de rango
                cursor.execute("""
                SELECT number, COUNT(*) as count 
                FROM draw_results 
                WHERE number < 0 OR number > 99 
                GROUP BY number 
                ORDER BY number
                """)
                
                invalid_numbers = cursor.fetchall()
                if invalid_numbers:
                    print("   📊 Números inválidos encontrados:")
                    for number, count in invalid_numbers:
                        print(f"      • {number}: {count} veces")
            
            return out_of_range
            
    except sqlite3.Error as e:
        print(f"❌ Error analizando números: {e}")
        return 0

def check_position_patterns():
    """Verifica los patrones de posiciones (1er, 2do, 3er premio)"""
    print(f"\n🔍 VERIFICANDO PATRONES DE POSICIONES")
    print("=" * 40)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Verificar posiciones
            cursor.execute("""
            SELECT position, COUNT(*) as count 
            FROM draw_results 
            WHERE draw_type = 'quiniela'
            GROUP BY position 
            ORDER BY position
            """)
            
            positions = cursor.fetchall()
            
            print(f"   📊 DISTRIBUCIÓN DE POSICIONES:")
            print("   Posición | Cantidad")
            print("   " + "-" * 20)
            
            expected_positions = {1, 2, 3}
            found_positions = set()
            
            for position, count in positions:
                status = "✅" if position in expected_positions else "⚠️"
                print(f"   {status} {position:>6} | {count:,}")
                found_positions.add(position)
            
            # Verificar si hay posiciones inesperadas
            unexpected = found_positions - expected_positions
            missing = expected_positions - found_positions
            
            if unexpected:
                print(f"   ⚠️ Posiciones inesperadas: {unexpected}")
            if missing:
                print(f"   ⚠️ Posiciones faltantes: {missing}")
            if not unexpected and not missing:
                print(f"   ✅ Todas las posiciones son correctas (1, 2, 3)")
            
            return len(unexpected) > 0
            
    except sqlite3.Error as e:
        print(f"❌ Error analizando posiciones: {e}")
        return False

def check_recent_data_sample():
    """Revisa una muestra de datos recientes para verificar calidad"""
    print(f"\n🔍 MUESTRA DE DATOS RECIENTES")
    print("=" * 32)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Obtener muestra de últimos 3 días
            cursor.execute("""
            SELECT date, number, position, draw_type 
            FROM draw_results 
            WHERE draw_type = 'quiniela'
            ORDER BY date DESC, position 
            LIMIT 15
            """)
            
            recent_data = cursor.fetchall()
            
            print(f"   📊 ÚLTIMOS 15 REGISTROS:")
            print("   Fecha      | Núm | Pos | Tipo")
            print("   " + "-" * 35)
            
            for date, number, position, draw_type in recent_data:
                print(f"   {date} | {number:2d}  |  {position}  | {draw_type}")
            
            return True
            
    except sqlite3.Error as e:
        print(f"❌ Error revisando muestra: {e}")
        return False

def clean_non_quiniela_data():
    """Elimina datos que no sean de Quiniela Loteka"""
    print(f"\n🧹 LIMPIANDO DATOS NO-QUINIELA")
    print("=" * 35)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Contar registros antes de limpieza
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type != 'quiniela'")
            non_quiniela_count = cursor.fetchone()[0]
            
            if non_quiniela_count > 0:
                print(f"   ⚠️ Encontrados {non_quiniela_count} registros NO-Quiniela")
                print(f"   🗑️ Eliminando registros...")
                
                # Eliminar registros que no sean de quiniela
                cursor.execute("DELETE FROM draw_results WHERE draw_type != 'quiniela'")
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"   ✅ Eliminados {deleted_count} registros NO-Quiniela")
                return deleted_count
            else:
                print(f"   ✅ No hay registros NO-Quiniela para eliminar")
                return 0
                
    except sqlite3.Error as e:
        print(f"❌ Error limpiando datos: {e}")
        return 0

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN DE DATOS DE QUINIELA LOTEKA")
    print("=" * 50)
    
    # 1. Analizar tipos de sorteos
    draw_types, non_quiniela_count = analyze_lottery_types()
    
    # 2. Verificar rangos de números
    out_of_range_count = analyze_number_ranges()
    
    # 3. Verificar patrones de posiciones
    has_invalid_positions = check_position_patterns()
    
    # 4. Revisar muestra de datos recientes
    check_recent_data_sample()
    
    # 5. Limpiar datos si es necesario
    deleted_count = 0
    if non_quiniela_count > 0:
        print(f"\n❓ ¿Desea eliminar los {non_quiniela_count} registros NO-Quiniela? (y/n): ", end="")
        # Para automatización, eliminar automáticamente
        response = "y"
        print("y (automático)")
        
        if response.lower() == 'y':
            deleted_count = clean_non_quiniela_data()
    
    # 6. Resumen final
    print(f"\n📋 RESUMEN FINAL")
    print("=" * 20)
    
    if non_quiniela_count == 0 and out_of_range_count == 0 and not has_invalid_positions:
        print("✅ PERFECTO: Todos los datos son de Quiniela Loteka válidos")
    else:
        print("⚠️ PROBLEMAS ENCONTRADOS:")
        if non_quiniela_count > 0:
            print(f"   • {non_quiniela_count} registros de otras loterías")
            if deleted_count > 0:
                print(f"     → {deleted_count} eliminados")
        if out_of_range_count > 0:
            print(f"   • {out_of_range_count} números fuera de rango")
        if has_invalid_positions:
            print(f"   • Posiciones inválidas encontradas")
    
    # Verificar estado final después de limpieza
    if deleted_count > 0:
        print(f"\n🔄 VERIFICANDO ESTADO DESPUÉS DE LIMPIEZA...")
        final_types, final_non_quiniela = analyze_lottery_types()
        
        if final_non_quiniela == 0:
            print("✅ LIMPIEZA EXITOSA: Solo quedan datos de Quiniela Loteka")
        else:
            print(f"⚠️ AÚN QUEDAN {final_non_quiniela} registros NO-Quiniela")

if __name__ == "__main__":
    main()