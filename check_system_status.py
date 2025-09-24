#!/usr/bin/env python3
"""
Script para verificar el estado actual del sistema y eliminar duplicados
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from database import DatabaseManager

def check_database_status():
    """Verifica el estado actual de la base de datos"""
    print("🔍 VERIFICANDO ESTADO ACTUAL DEL SISTEMA")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Obtener estadísticas generales
    stats = db.get_database_stats()
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Total registros: {stats['total_records']:,}")
    print(f"   • Fechas únicas: {stats['unique_dates']:,}")
    print(f"   • Rango de días: {stats['date_range_days']:,}")
    print(f"   • Fecha más antigua: {stats['earliest_date']}")
    print(f"   • Fecha más reciente: {stats['latest_date']}")
    print(f"   • ¿Tiene 720+ días?: {'✅ Sí' if stats['has_720_days'] else '❌ No'}")
    
    return stats

def check_for_duplicates():
    """Verifica si existen registros duplicados en la base de datos"""
    print(f"\n🔍 VERIFICANDO DUPLICADOS...")
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Buscar duplicados por (date, number, position)
            cursor.execute("""
            SELECT date, number, position, COUNT(*) as count
            FROM draw_results 
            WHERE draw_type = 'quiniela'
            GROUP BY date, number, position 
            HAVING COUNT(*) > 1
            ORDER BY count DESC, date DESC
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"⚠️ ENCONTRADOS {len(duplicates)} GRUPOS DE DUPLICADOS:")
                print("   Fecha      | Número | Pos | Cantidad")
                print("   " + "-" * 40)
                
                total_duplicate_records = 0
                for date, number, position, count in duplicates[:10]:  # Mostrar solo los primeros 10
                    print(f"   {date} |   {number:02d}   |  {position}  |    {count}")
                    total_duplicate_records += count - 1  # -1 porque uno es el original
                
                if len(duplicates) > 10:
                    print(f"   ... y {len(duplicates) - 10} grupos más")
                
                print(f"\n📊 Total registros duplicados a eliminar: {total_duplicate_records}")
                return duplicates
            else:
                print("✅ No se encontraron registros duplicados")
                return []
                
    except sqlite3.Error as e:
        print(f"❌ Error verificando duplicados: {e}")
        return []

def remove_duplicates():
    """Elimina registros duplicados manteniendo solo el más reciente por cada grupo"""
    print(f"\n🧹 ELIMINANDO DUPLICADOS...")
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Crear tabla temporal con registros únicos (manteniendo el ID más alto)
            cursor.execute("""
            CREATE TEMPORARY TABLE temp_unique AS
            SELECT MAX(id) as id, date, number, position, draw_type, prize_amount
            FROM draw_results 
            WHERE draw_type = 'quiniela'
            GROUP BY date, number, position
            """)
            
            # Contar registros antes
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type = 'quiniela'")
            count_before = cursor.fetchone()[0]
            
            # Eliminar todos los registros de quiniela
            cursor.execute("DELETE FROM draw_results WHERE draw_type = 'quiniela'")
            
            # Insertar solo registros únicos
            cursor.execute("""
            INSERT INTO draw_results (date, number, position, draw_type, prize_amount, created_at)
            SELECT date, number, position, draw_type, prize_amount, CURRENT_TIMESTAMP
            FROM temp_unique
            """)
            
            # Contar registros después
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type = 'quiniela'")
            count_after = cursor.fetchone()[0]
            
            removed_count = count_before - count_after
            
            conn.commit()
            
            print(f"✅ LIMPIEZA COMPLETADA:")
            print(f"   • Registros antes: {count_before:,}")
            print(f"   • Registros después: {count_after:,}")
            print(f"   • Duplicados eliminados: {removed_count:,}")
            
            return removed_count
            
    except sqlite3.Error as e:
        print(f"❌ Error eliminando duplicados: {e}")
        return 0

def check_data_coverage():
    """Verifica la cobertura de datos hasta la fecha actual"""
    print(f"\n📅 VERIFICANDO COBERTURA DE DATOS...")
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Obtener la fecha más reciente
            cursor.execute("""
            SELECT MAX(date) FROM draw_results WHERE draw_type = 'quiniela'
            """)
            latest_date_str = cursor.fetchone()[0]
            
            if latest_date_str:
                latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
                today = datetime.now()
                days_behind = (today - latest_date).days
                
                print(f"   • Última fecha en BD: {latest_date.strftime('%d-%m-%Y')}")
                print(f"   • Fecha actual: {today.strftime('%d-%m-%Y')}")
                print(f"   • Días de retraso: {days_behind}")
                
                if days_behind > 1:
                    print(f"⚠️ NECESITA ACTUALIZACIÓN: Faltan {days_behind} días de datos")
                    return days_behind
                else:
                    print("✅ Datos están actualizados")
                    return 0
            else:
                print("❌ No se encontraron datos en la base de datos")
                return float('inf')
                
    except sqlite3.Error as e:
        print(f"❌ Error verificando cobertura: {e}")
        return float('inf')

def main():
    """Función principal"""
    print("🚀 INICIANDO VERIFICACIÓN Y LIMPIEZA DEL SISTEMA")
    print("=" * 60)
    
    # 1. Verificar estado actual
    stats = check_database_status()
    
    # 2. Verificar duplicados
    duplicates = check_for_duplicates()
    
    # 3. Eliminar duplicados si existen
    if duplicates:
        print(f"\n❓ ¿Desea eliminar los {len(duplicates)} grupos de duplicados? (y/n): ", end="")
        # Para automatización, siempre eliminar duplicados
        response = "y"
        print("y (automático)")
        
        if response.lower() == 'y':
            removed = remove_duplicates()
            if removed > 0:
                print(f"✅ Se eliminaron {removed} registros duplicados")
                # Verificar estado después de limpieza
                print(f"\n📊 ESTADO DESPUÉS DE LIMPIEZA:")
                stats_after = check_database_status()
        else:
            print("⏭️ Saltando eliminación de duplicados")
    
    # 4. Verificar cobertura de datos
    days_behind = check_data_coverage()
    
    # 5. Resumen final
    print(f"\n📋 RESUMEN:")
    print(f"   • Registros totales: {stats['total_records']:,}")
    print(f"   • Rango de datos: {stats['date_range_days']} días")
    print(f"   • Duplicados encontrados: {len(duplicates)} grupos")
    print(f"   • Días de retraso: {days_behind}")
    
    if days_behind > 1:
        print(f"\n🎯 PRÓXIMO PASO: Ejecutar importación de datos históricos para obtener {days_behind} días faltantes")
    else:
        print(f"\n✅ SISTEMA EN BUEN ESTADO: Datos actualizados y sin duplicados")

if __name__ == "__main__":
    main()