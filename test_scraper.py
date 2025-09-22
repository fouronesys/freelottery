#!/usr/bin/env python3
"""
Script de prueba para diagnosticar problemas de scraping
"""
import requests
import trafilatura
from datetime import datetime, timedelta
import time

# Headers similares a los del scraper original
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def test_website_access():
    """Prueba el acceso a los sitios web de lotería"""
    
    base_urls = [
        "https://loteka.com.do",
        "https://loteriasdominicanas.com"
    ]
    
    print("=== Prueba de Conectividad a Sitios Web ===")
    
    for base_url in base_urls:
        print(f"\n--- Probando {base_url} ---")
        
        # Generar lista de endpoints para probar
        if "loteka.com.do" in base_url:
            endpoints = [
                f"{base_url}",
                f"{base_url}/quiniela",
                f"{base_url}/resultados"
            ]
        elif "loteriasdominicanas.com" in base_url:
            endpoints = [
                f"{base_url}/loteka/quiniela-mega-decenas",
                f"{base_url}/loteka",
                f"{base_url}"
            ]
        else:
            endpoints = [base_url]
        
        for endpoint in endpoints:
            try:
                print(f"Probando: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=15)
                
                print(f"  Status Code: {response.status_code}")
                print(f"  Content Length: {len(response.text)}")
                
                if response.status_code == 200:
                    # Extraer contenido con trafilatura
                    text_content = trafilatura.extract(response.text)
                    
                    if text_content:
                        print(f"  Texto extraído: {len(text_content)} caracteres")
                        print(f"  Muestra del contenido: {text_content[:300]}...")
                        
                        # Buscar palabras clave relacionadas con lotería
                        keywords = ['quiniela', 'loteka', 'resultado', 'ganador', 'sorteo']
                        found_keywords = [kw for kw in keywords if kw.lower() in text_content.lower()]
                        print(f"  Palabras clave encontradas: {found_keywords}")
                    else:
                        print("  ⚠️  No se pudo extraer texto con trafilatura")
                        # Revisar HTML directo
                        html_snippet = response.text[:500]
                        print(f"  HTML directo (primeros 500 chars): {html_snippet}")
                else:
                    print(f"  ❌ Error HTTP: {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"  ❌ Error de conexión: {e}")
            except Exception as e:
                print(f"  ❌ Error general: {e}")
                
            # Pausa entre solicitudes
            time.sleep(2)
    
def test_parsing_patterns():
    """Prueba los patrones de parsing en contenido de ejemplo"""
    
    print("\n\n=== Prueba de Patrones de Parsing ===")
    
    # Contenido de ejemplo que podría encontrarse en los sitios
    sample_content_loteka = """
    Resultados de hoy 22/09/2024
    Quiniela Loteka
    1er. 47
    2do. 85  
    3er. 23
    Premio: RD$ 50,000
    """
    
    sample_content_loteriasdominicanas = """
    Quiniela Loteka - 22-09
    478523
    Resultado del día
    """
    
    import re
    
    # Probar patrón de Loteka
    print("--- Probando patrón de Loteka ---")
    print(f"Contenido: {sample_content_loteka}")
    
    # Buscar números estilo "1er. 47"
    loteka_pattern = r'(?:1er\.|2do\.|3er\.)\s*(\d{2})'
    loteka_matches = re.findall(loteka_pattern, sample_content_loteka)
    print(f"Números encontrados: {loteka_matches}")
    
    # Buscar fechas
    date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
    date_matches = re.findall(date_pattern, sample_content_loteka)
    print(f"Fechas encontradas: {date_matches}")
    
    # Probar patrón de LoteriasDominicanas
    print("\n--- Probando patrón de LoteriasDominicanas ---")
    print(f"Contenido: {sample_content_loteriasdominicanas}")
    
    # Buscar números de 6 dígitos
    six_digit_pattern = r'(\d{6})'
    six_digit_matches = re.findall(six_digit_pattern, sample_content_loteriasdominicanas)
    print(f"Números de 6 dígitos encontrados: {six_digit_matches}")
    
    # Convertir a números individuales
    if six_digit_matches:
        full_number = six_digit_matches[0]
        individual_numbers = [full_number[i:i+2] for i in range(0, 6, 2)]
        print(f"Números individuales: {individual_numbers}")
    
    print("\n=== Fin de Pruebas ===")

if __name__ == "__main__":
    test_website_access()
    test_parsing_patterns()