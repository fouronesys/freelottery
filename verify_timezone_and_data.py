#!/usr/bin/env python3
"""
Script para verificar zona horaria y analizar discrepancia de datos
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz
from database import DatabaseManager

def check_current_timezone():
    """Verifica la zona horaria actual del sistema"""
    print("🌍 VERIFICANDO ZONA HORARIA")
    print("=" * 40)
    
    # Zona horaria UTC (actual)
    utc_now = datetime.utcnow()
    print(f"   • UTC actual: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Zona horaria República Dominicana (UTC-4)
    dominican_tz = pytz.timezone('America/Santo_Domingo')
    dominican_now = datetime.now(dominican_tz)
    print(f"   • Rep. Dominicana (UTC-4): {dominican_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Diferencia
    print(f"   • Fecha dominicana: {dominican_now.strftime('%Y-%m-%d')}")
    print(f"   • Fecha UTC: {utc_now.strftime('%Y-%m-%d')}")
    
    return dominican_now

def analyze_daily_draws():
    """Analiza la relación entre sorteos y días"""
    print(f"\n📊 ANALIZANDO RELACIÓN SORTEOS/DÍAS")
    print("=" * 45)
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            # Estadísticas básicas
            cursor = conn.cursor()
            
            # Total registros
            cursor.execute("SELECT COUNT(*) FROM draw_results WHERE draw_type = 'quiniela'")
            total_records = cursor.fetchone()[0]
            
            # Fechas únicas
            cursor.execute("SELECT COUNT(DISTINCT date) FROM draw_results WHERE draw_type = 'quiniela'")
            unique_dates = cursor.fetchone()[0]
            
            # Rango de fechas
            cursor.execute("SELECT MIN(date), MAX(date) FROM draw_results WHERE draw_type = 'quiniela'")
            earliest, latest = cursor.fetchone()
            
            print(f"   • Total registros: {total_records:,}")
            print(f"   • Fechas únicas: {unique_dates:,}")
            print(f"   • Promedio registros por fecha: {total_records/unique_dates:.2f}")
            
            # Calcular días del rango completo
            if earliest and latest:
                start_date = datetime.strptime(earliest, '%Y-%m-%d')
                end_date = datetime.strptime(latest, '%Y-%m-%d')
                total_days_in_range = (end_date - start_date).days + 1
                
                print(f"   • Rango: {earliest} a {latest}")
                print(f"   • Días en el rango: {total_days_in_range:,}")
                print(f"   • Cobertura: {(unique_dates/total_days_in_range)*100:.1f}%")
                
                # Si hay 1 sorteo por día, deberíamos tener aprox. 3 registros por fecha (1er, 2do, 3er premio)
                expected_records = unique_dates * 3
                print(f"   • Registros esperados (3 por fecha): {expected_records:,}")
                print(f"   • Diferencia: {total_records - expected_records:,}")
                
                has_valid_range = True
            else:
                print("   ❌ No hay datos válidos para analizar rango")
                start_date = None
                end_date = None
                total_days_in_range = 0
                has_valid_range = False
            
            # Analizar distribución por fecha
            cursor.execute("""
            SELECT date, COUNT(*) as count 
            FROM draw_results 
            WHERE draw_type = 'quiniela'
            GROUP BY date 
            ORDER BY count DESC, date DESC
            LIMIT 10
            """)
            
            print(f"\n   📅 DISTRIBUCIÓN POR FECHA (Top 10):")
            print("      Fecha      | Cantidad")
            print("      " + "-" * 25)
            
            distribution = cursor.fetchall()
            for date, count in distribution:
                print(f"      {date} |    {count}")
            
            # Verificar fechas con registros atípicos
            cursor.execute("""
            SELECT 
                COUNT(CASE WHEN cnt = 1 THEN 1 END) as fechas_1_registro,
                COUNT(CASE WHEN cnt = 2 THEN 1 END) as fechas_2_registros,
                COUNT(CASE WHEN cnt = 3 THEN 1 END) as fechas_3_registros,
                COUNT(CASE WHEN cnt > 3 THEN 1 END) as fechas_mas_3_registros
            FROM (
                SELECT date, COUNT(*) as cnt 
                FROM draw_results 
                WHERE draw_type = 'quiniela'
                GROUP BY date
            ) date_counts
            """)
            
            counts = cursor.fetchone()
            print(f"\n   📊 DISTRIBUCIÓN DE REGISTROS POR FECHA:")
            print(f"      • 1 registro: {counts[0]:,} fechas")
            print(f"      • 2 registros: {counts[1]:,} fechas")
            print(f"      • 3 registros: {counts[2]:,} fechas")
            print(f"      • Más de 3: {counts[3]:,} fechas")
            
            # Identificar fechas faltantes en el rango
            print(f"\n🔍 IDENTIFICANDO FECHAS FALTANTES...")
            
            if has_valid_range and start_date and end_date:
                # Crear lista de todas las fechas en el rango
                all_dates = []
                current = start_date
                while current <= end_date:
                    all_dates.append(current.strftime('%Y-%m-%d'))
                    current += timedelta(days=1)
                
                # Obtener fechas con datos
                cursor.execute("""
                SELECT DISTINCT date 
                FROM draw_results 
                WHERE draw_type = 'quiniela'
                ORDER BY date
                """)
                dates_with_data = [row[0] for row in cursor.fetchall()]
                
                # Encontrar fechas faltantes
                missing_dates = set(all_dates) - set(dates_with_data)
                
                if missing_dates:
                    missing_count = len(missing_dates)
                    print(f"   ⚠️ Fechas faltantes: {missing_count:,}")
                    print(f"   📊 Porcentaje faltante: {(missing_count/len(all_dates))*100:.2f}%")
                    
                    # Mostrar algunas fechas faltantes recientes
                    recent_missing = sorted([d for d in missing_dates if d >= '2024-01-01'])[-10:]
                    if recent_missing:
                        print(f"   📅 Fechas faltantes recientes:")
                        for date in recent_missing:
                            print(f"      • {date}")
                else:
                    print("   ✅ No hay fechas faltantes en el rango")
                    missing_dates = set()
            else:
                print("   ❌ No se puede analizar fechas faltantes sin rango válido")
                missing_dates = set()
            
            return {
                'total_records': total_records,
                'unique_dates': unique_dates,
                'total_days_in_range': total_days_in_range if has_valid_range else 0,
                'missing_dates': len(missing_dates) if missing_dates else 0,
                'coverage_percent': (unique_dates/total_days_in_range)*100 if has_valid_range and total_days_in_range > 0 else 0
            }
            
    except sqlite3.Error as e:
        print(f"❌ Error analizando datos: {e}")
        return None

def check_recent_data_with_timezone():
    """Verifica datos recientes con zona horaria correcta"""
    print(f"\n🕐 VERIFICANDO DATOS RECIENTES (ZONA HORARIA CORRECTA)")
    print("=" * 55)
    
    # Obtener fecha actual en República Dominicana
    dominican_tz = pytz.timezone('America/Santo_Domingo')
    dominican_now = datetime.now(dominican_tz)
    dominican_today = dominican_now.date()
    
    print(f"   • Fecha actual RD: {dominican_today}")
    print(f"   • Hora actual RD: {dominican_now.strftime('%H:%M:%S')}")
    
    try:
        with sqlite3.connect("quiniela_loteka.db") as conn:
            cursor = conn.cursor()
            
            # Verificar últimos 7 días
            for i in range(7):
                check_date = dominican_today - timedelta(days=i)
                check_date_str = check_date.strftime('%Y-%m-%d')
                
                cursor.execute("""
                SELECT COUNT(*) 
                FROM draw_results 
                WHERE date = ? AND draw_type = 'quiniela'
                """, (check_date_str,))
                
                count = cursor.fetchone()[0]
                status = "✅" if count >= 3 else "⚠️" if count > 0 else "❌"
                print(f"   {status} {check_date_str}: {count} registros")
    
    except sqlite3.Error as e:
        print(f"❌ Error verificando datos recientes: {e}")

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN DE ZONA HORARIA Y ANÁLISIS DE DATOS")
    print("=" * 65)
    
    # 1. Verificar zona horaria
    dominican_time = check_current_timezone()
    
    # 2. Analizar relación sorteos/días
    analysis = analyze_daily_draws()
    
    # 3. Verificar datos recientes con zona horaria correcta
    check_recent_data_with_timezone()
    
    # 4. Resumen y recomendaciones
    print(f"\n📋 RESUMEN Y RECOMENDACIONES")
    print("=" * 35)
    
    dominican_date = dominican_time.strftime('%Y-%m-%d')
    print(f"   • Fecha actual RD: {dominican_date}")
    
    if analysis:
        print(f"   • Cobertura de datos: {analysis['coverage_percent']:.1f}%")
        print(f"   • Fechas faltantes: {analysis['missing_dates']:,}")
        
        # Calcular promedio por fecha
        avg_per_date = analysis['total_records'] / analysis['unique_dates']
        print(f"   • Promedio registros/fecha: {avg_per_date:.2f}")
        
        if avg_per_date < 2.5:
            print("   ⚠️ PROBLEMA: Muy pocos registros por fecha")
            print("   📝 Esperado: ~3 registros por fecha (1er, 2do, 3er premio)")
        elif avg_per_date > 3.5:
            print("   ⚠️ PROBLEMA: Demasiados registros por fecha")
            print("   📝 Posibles duplicados o datos adicionales")
        else:
            print("   ✅ Registros por fecha dentro del rango esperado")

if __name__ == "__main__":
    main()