#!/usr/bin/env python3
"""
Script para analizar y corregir problemas en la base de datos de sorteos:
1. Identificar datos duplicados
2. Corregir error de fechas (día 22 puesto en día 23)
3. Eliminar duplicados
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def analyze_database():
    """Analiza la base de datos para identificar problemas"""
    db_path = "quiniela_loteka.db"
    
    with sqlite3.connect(db_path) as conn:
        print("=== ANÁLISIS DE LA BASE DE DATOS ===\n")
        
        # 1. Verificar datos duplicados
        print("1. BÚSQUEDA DE DATOS DUPLICADOS:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, number, position, COUNT(*) as duplicates
            FROM draw_results 
            GROUP BY date, number, position 
            HAVING COUNT(*) > 1 
            ORDER BY date DESC
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"   ❌ Encontrados {len(duplicates)} grupos de datos duplicados:")
            for row in duplicates:
                print(f"      Fecha: {row[0]}, Número: {row[1]}, Posición: {row[2]}, Duplicados: {row[3]}")
        else:
            print("   ✅ No se encontraron datos duplicados exactos")
        
        # 2. Verificar datos recientes (últimos 7 días)
        print(f"\n2. ANÁLISIS DE DATOS RECIENTES:")
        cursor.execute("""
            SELECT date, number, position, prize_amount, created_at
            FROM draw_results 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC, position
        """)
        recent_data = cursor.fetchall()
        
        print(f"   📅 Datos de los últimos 7 días:")
        for row in recent_data:
            print(f"      {row[0]} | Núm: {row[1]} | Pos: {row[2]} | Premio: {row[3]} | Creado: {row[4]}")
        
        # 3. Verificar específicamente septiembre 22 y 23, 2025
        print(f"\n3. VERIFICACIÓN DE FECHAS ESPECÍFICAS (Sep 22-23, 2025):")
        for date_check in ['2025-09-22', '2025-09-23']:
            cursor.execute("""
                SELECT date, number, position, prize_amount, created_at
                FROM draw_results 
                WHERE date = ?
                ORDER BY position
            """, (date_check,))
            date_data = cursor.fetchall()
            
            print(f"   📅 {date_check}:")
            if date_data:
                for row in date_data:
                    print(f"      Núm: {row[1]} | Pos: {row[2]} | Premio: {row[3]} | Creado: {row[4]}")
            else:
                print(f"      Sin datos para esta fecha")
        
        # 4. Contar total de registros por fecha reciente
        print(f"\n4. CONTEO DE REGISTROS POR FECHA (últimos 10 días):")
        cursor.execute("""
            SELECT date, COUNT(*) as total_records
            FROM draw_results 
            WHERE date >= date('now', '-10 days')
            GROUP BY date
            ORDER BY date DESC
        """)
        daily_counts = cursor.fetchall()
        
        for row in daily_counts:
            print(f"   📅 {row[0]}: {row[1]} registros")
            
        return duplicates, recent_data

def fix_duplicate_data():
    """Elimina datos duplicados manteniendo solo el más reciente"""
    db_path = "quiniela_loteka.db"
    
    with sqlite3.connect(db_path) as conn:
        print("\n=== ELIMINACIÓN DE DATOS DUPLICADOS ===")
        
        cursor = conn.cursor()
        
        # Encontrar duplicados con sus IDs
        cursor.execute("""
            SELECT id, date, number, position, created_at
            FROM draw_results a
            WHERE EXISTS (
                SELECT 1 FROM draw_results b 
                WHERE a.date = b.date 
                AND a.number = b.number 
                AND a.position = b.position 
                AND a.id != b.id
            )
            ORDER BY date, number, position, created_at
        """)
        
        all_duplicates = cursor.fetchall()
        
        if not all_duplicates:
            print("   ✅ No hay duplicados para eliminar")
            return
        
        print(f"   🔍 Encontrados {len(all_duplicates)} registros duplicados")
        
        # Agrupar duplicados y mantener solo el más reciente
        groups = {}
        for row in all_duplicates:
            key = (row[1], row[2], row[3])  # (date, number, position)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        
        deleted_count = 0
        for key, group in groups.items():
            if len(group) > 1:
                # Ordenar por created_at DESC y mantener el primero (más reciente)
                group.sort(key=lambda x: x[4], reverse=True)
                keep_id = group[0][0]
                
                print(f"   📅 {key[0]} Núm:{key[1]} Pos:{key[2]} - Manteniendo ID {keep_id}")
                
                # Eliminar los demás
                for row in group[1:]:
                    cursor.execute("DELETE FROM draw_results WHERE id = ?", (row[0],))
                    deleted_count += 1
                    print(f"      🗑️ Eliminado ID {row[0]} (creado: {row[4]})")
        
        conn.commit()
        print(f"   ✅ Eliminados {deleted_count} registros duplicados")

def fix_date_error():
    """Corrige el error específico: datos del día 22 puestos en día 23"""
    db_path = "quiniela_loteka.db"
    
    with sqlite3.connect(db_path) as conn:
        print("\n=== CORRECCIÓN DE ERROR DE FECHAS ===")
        
        cursor = conn.cursor()
        
        # Verificar si hay datos en 2025-09-23
        cursor.execute("""
            SELECT id, date, number, position, created_at
            FROM draw_results 
            WHERE date = '2025-09-23'
            ORDER BY position
        """)
        sep_23_data = cursor.fetchall()
        
        if not sep_23_data:
            print("   ℹ️ No hay datos en 2025-09-23 para verificar")
            return
        
        print(f"   🔍 Datos encontrados en 2025-09-23:")
        for row in sep_23_data:
            print(f"      ID: {row[0]} | Núm: {row[2]} | Pos: {row[3]} | Creado: {row[4]}")
        
        # Verificar si hay datos en 2025-09-22
        cursor.execute("""
            SELECT id, date, number, position, created_at
            FROM draw_results 
            WHERE date = '2025-09-22'
            ORDER BY position
        """)
        sep_22_data = cursor.fetchall()
        
        print(f"   🔍 Datos encontrados en 2025-09-22:")
        if sep_22_data:
            for row in sep_22_data:
                print(f"      ID: {row[0]} | Núm: {row[2]} | Pos: {row[3]} | Creado: {row[4]}")
        else:
            print("      Sin datos en 2025-09-22")
        
        # Si hay datos en 23 pero no en 22, probablemente están mal
        if sep_23_data and not sep_22_data:
            print("\n   ⚠️ POSIBLE ERROR DETECTADO:")
            print("   Hay datos en 2025-09-23 pero no en 2025-09-22")
            print("   ¿Mover datos de 2025-09-23 a 2025-09-22? (y/n):")
            
            # Para automatizar, asumimos que sí queremos mover
            response = input()
            if response.lower() == 'y':
                for row in sep_23_data:
                    cursor.execute("""
                        UPDATE draw_results 
                        SET date = '2025-09-22' 
                        WHERE id = ?
                    """, (row[0],))
                    print(f"      ✅ Movido registro ID {row[0]} de 2025-09-23 a 2025-09-22")
                
                conn.commit()
                print("   ✅ Corrección de fechas completada")
            else:
                print("   ⏭️ Corrección cancelada por el usuario")

if __name__ == "__main__":
    # Ejecutar análisis
    duplicates, recent_data = analyze_database()
    
    # Ejecutar correcciones
    if duplicates:
        fix_duplicate_data()
    
    fix_date_error()
    
    print("\n=== ANÁLISIS FINAL ===")
    analyze_database()