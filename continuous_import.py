#!/usr/bin/env python3
"""
Script de Importación Continua - Quiniela Loteka
Ejecuta el recopilador exhaustivo hasta completar 15+ años de datos
"""

import subprocess
import time
import json
from datetime import datetime, timedelta

def get_current_progress():
    """Obtiene el progreso actual del checkpoint"""
    try:
        with open('exhaustive_checkpoint.json', 'r') as f:
            checkpoint = json.load(f)
        
        start_date = datetime(2010, 8, 1)
        last_processed = datetime.strptime(checkpoint['last_processed_date'], '%Y-%m-%d')
        end_date = datetime(2025, 9, 23)
        
        total_days = (end_date - start_date).days + 1
        processed_days = (last_processed - start_date).days + 1
        remaining_days = (end_date - last_processed).days
        progress_percent = (processed_days / total_days) * 100
        
        return {
            'last_processed': last_processed,
            'processed_days': processed_days,
            'remaining_days': remaining_days,
            'total_days': total_days,
            'progress_percent': progress_percent,
            'total_saved': checkpoint.get('total_saved', 0)
        }
    except:
        return None

def run_continuous_import():
    """Ejecuta la importación continua hasta completar 15+ años"""
    print("🚀 INICIANDO IMPORTACIÓN CONTINUA DE DATOS HISTÓRICOS")
    print("🎯 Objetivo: Importar +15 años de datos (2010-2025)")
    print("=" * 60)
    
    start_time = datetime.now()
    session_count = 0
    target_years = 15
    
    while True:
        session_count += 1
        
        # Obtener progreso actual
        progress = get_current_progress()
        if progress:
            years_processed = progress['processed_days'] / 365.25
            print(f"\n📊 SESIÓN {session_count}")
            print(f"   • Último día procesado: {progress['last_processed'].strftime('%d-%m-%Y')}")
            print(f"   • Días procesados: {progress['processed_days']:,}")
            print(f"   • Años procesados: {years_processed:.1f}")
            print(f"   • Progreso: {progress['progress_percent']:.1f}%")
            print(f"   • Total registros: {progress['total_saved']:,}")
            
            # Verificar si hemos completado 15+ años
            if years_processed >= target_years:
                print(f"\n🎉 ¡OBJETIVO COMPLETADO!")
                print(f"   ✅ Se han importado {years_processed:.1f} años de datos")
                print(f"   📊 Total registros guardados: {progress['total_saved']:,}")
                elapsed = datetime.now() - start_time
                print(f"   ⏱️ Tiempo total: {elapsed}")
                break
        
        print(f"\n🔄 Ejecutando recopilador exhaustivo (sesión {session_count})...")
        
        try:
            # Ejecutar el recopilador exhaustivo
            result = subprocess.run(['python3', 'exhaustive_collector.py'], 
                                  capture_output=True, text=True, timeout=300)
            
            print(f"✅ Sesión {session_count} completada")
            
            # Pausa corta entre sesiones
            print("⏸️ Pausa de 10 segundos antes de la siguiente sesión...")
            time.sleep(10)
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Sesión {session_count} completada (timeout normal)")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n⚠️ Interrumpido por usuario")
            break
        except Exception as e:
            print(f"❌ Error en sesión {session_count}: {e}")
            time.sleep(30)  # Pausa más larga si hay error
            
        # Verificación de seguridad - máximo 1000 sesiones
        if session_count >= 1000:
            print("⚠️ Límite de sesiones alcanzado por seguridad")
            break
    
    # Reporte final
    final_progress = get_current_progress()
    if final_progress:
        final_years = final_progress['processed_days'] / 365.25
        print(f"\n📋 REPORTE FINAL")
        print(f"   • Sesiones ejecutadas: {session_count}")
        print(f"   • Años de datos importados: {final_years:.1f}")
        print(f"   • Total registros: {final_progress['total_saved']:,}")
        print(f"   • Progreso final: {final_progress['progress_percent']:.1f}%")
        
        elapsed = datetime.now() - start_time
        print(f"   • Tiempo total de ejecución: {elapsed}")

if __name__ == "__main__":
    run_continuous_import()