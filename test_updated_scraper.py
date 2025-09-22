#!/usr/bin/env python3
"""
Prueba del scraper actualizado
"""
from scraper import QuinielaScraperManager
from datetime import datetime, timedelta

def test_updated_scraper():
    """Prueba el scraper actualizado para verificar si obtiene datos reales"""
    
    print("=== Prueba del Scraper Actualizado ===")
    
    scraper = QuinielaScraperManager()
    
    # Probar con un rango de fechas reciente
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)  # Últimos 5 días
    
    print(f"Buscando datos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
    
    results = scraper.scrape_historical_data(start_date, end_date)
    
    print(f"\n=== Resultados ===")
    print(f"Total de resultados obtenidos: {len(results)}")
    
    if results:
        # Mostrar algunos resultados de ejemplo
        print(f"\nPrimeros 10 resultados:")
        for i, result in enumerate(results[:10]):
            print(f"{i+1}. Fecha: {result['date']}, Número: {result['number']}, Posición: {result['position']}")
        
        # Verificar si son datos reales (no de muestra)
        dates = [result['date'] for result in results]
        unique_dates = list(set(dates))
        unique_dates.sort()
        
        print(f"\nFechas únicas encontradas: {unique_dates}")
        
        # Verificar distribución de números
        numbers = [result['number'] for result in results]
        print(f"Números encontrados (primeros 20): {numbers[:20]}")
        
        # Determinar si son datos reales o de muestra
        sample_dates = [item['date'] for item in scraper.sample_data]
        real_data = not any(result['date'] in sample_dates for result in results)
        
        if real_data:
            print(f"\n✅ ¡ÉXITO! El scraper está obteniendo datos REALES")
        else:
            print(f"\n⚠️ El scraper sigue usando datos de muestra")
    else:
        print("\n❌ No se obtuvieron resultados")

if __name__ == "__main__":
    test_updated_scraper()