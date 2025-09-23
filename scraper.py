import requests
from bs4 import BeautifulSoup
import trafilatura
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import random
from typing import List, Dict, Any, Optional
import json

class QuinielaScraperManager:
    """Gestiona el web scraping para obtener datos históricos de Quiniela Loteka"""
    
    def __init__(self):
        # Múltiples fuentes confiables para datos históricos
        self.base_urls = [
            "https://loteka.com.do",  # Sitio oficial
            "https://www.bolomagico.com",  # Agregador confiable
            "https://loteriasdominicanas.com",  # Fuente secundaria
            "https://paginasamarillas.com.do"  # Fuente adicional
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Patrones mejorados para múltiples fuentes
        self.number_patterns = {
            'loteka': [
                r'(?:1er\.|2do\.|3er\.)\s*(\d{2})',
                r'quiniela.*?(\d{2})\s*(\d{2})\s*(\d{2})'
            ],
            'bolomagico': [
                r'<span[^>]*class="[^"]*number[^"]*"[^>]*>(\d{2})</span>',
                r'Quiniela[^\d]*(\d{2})[^\d]*(\d{2})[^\d]*(\d{2})'
            ],
            'loteriasdominicanas': [
                r'quiniela\s+loteka[^\d]*(\d{2})(\d{2})(\d{2})',
                r'(\d{6})',  # 6 dígitos consecutivos
            ],
            'generic': [
                r'quiniela.*?(\d{2})',
                r'resultado.*?(\d{2})',
                r'ganador.*?(\d{2})'
            ]
        }
        
        # Configuración para recopilación masiva de datos históricos
        self.max_retries = 3
        self.retry_delay = 5  # segundos
        self.batch_size = 30  # días por lote
        self.request_delay = (2, 5)  # rango aleatorio de espera entre requests
    
    def _generate_realistic_sample_data(self) -> List[Dict[str, Any]]:
        """
        MÉTODO DESHABILITADO - NO generar datos de prueba
        El sistema SOLO debe usar datos reales de loteka.com.do
        """
        print("❌ Generación de datos de prueba DESHABILITADA")
        print("✅ Sistema configurado para usar SOLO datos reales")
        return []  # Retornar lista vacía - NO datos de prueba
    
    def scrape_historical_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Intenta obtener datos históricos de múltiples fuentes
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de resultados de sorteos
        """
        results = []
        
        # Agregar datos de TODAS las fuentes disponibles para completitud
        for base_url in self.base_urls:
            try:
                data = self._scrape_from_source(base_url, start_date, end_date)
                if data:
                    validated_data = self.validate_scraped_data(data)
                    if validated_data:
                        results.extend(validated_data)
                        print(f"Datos validados de {base_url}: {len(validated_data)} registros")
                    
            except Exception as e:
                print(f"Error obteniendo datos de {base_url}: {e}")
                continue
        
        # Deduplicar resultados finales
        results = self._deduplicate_by_date_position(results)
        
        # Si no se obtuvieron datos reales, reportar error en lugar de usar datos de prueba
        if not results:
            print("❌ NO se pudieron obtener datos reales de loteka.com.do")
            print("❌ Sistema NO utilizará datos de prueba - solo datos reales")
            # NO usar datos de muestra - mantener results vacío
            results = []
        
        return results
    
    def _scrape_from_source(self, base_url: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Intenta obtener datos de una fuente específica
        """
        results = []
        
        try:
            # Permitir múltiples fuentes confiables para datos históricos
            if "loteka.com.do" in base_url:
                possible_endpoints = [
                    f"{base_url}/quiniela",
                    f"{base_url}/resultados", 
                    f"{base_url}",
                ]
            elif "bolomagico.com" in base_url:
                possible_endpoints = [
                    f"{base_url}/en/loteria/loteka/",
                    f"{base_url}/loteria/loteka/"
                ]
            elif "loteriasdominicanas.com" in base_url:
                possible_endpoints = [
                    f"{base_url}",
                    f"{base_url}/resultados"
                ]
            else:
                possible_endpoints = [base_url]
            
            for endpoint in possible_endpoints:
                for attempt in range(self.max_retries):
                    try:
                        print(f"🔍 Intento {attempt + 1}/{self.max_retries}: {endpoint}")
                        response = requests.get(endpoint, headers=self.headers, timeout=20)
                        
                        if response.status_code == 200:
                            # Usar trafilatura para extraer contenido limpio
                            text_content = trafilatura.extract(response.text)
                            
                            if text_content:
                                parsed_results = self._parse_lottery_content(text_content, start_date, end_date, endpoint)
                                
                                if parsed_results:
                                    results.extend(parsed_results)
                                    print(f"✅ Datos obtenidos de {endpoint}: {len(parsed_results)} registros")
                                    return results  # Retornar en cuanto encontremos datos válidos
                        else:
                            print(f"⚠️ Status {response.status_code} para {endpoint}")
                            
                    except requests.RequestException as e:
                        print(f"❌ Error en intento {attempt + 1}: {e}")
                        if attempt < self.max_retries - 1:
                            delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⏳ Reintentando en {delay} segundos...")
                            time.sleep(delay)
                        else:
                            print(f"❌ Falló después de {self.max_retries} intentos")
                
                # Pausa entre endpoints
                delay = random.uniform(*self.request_delay)
                print(f"⏸️ Pausa de {delay:.1f}s entre endpoints")
                time.sleep(delay)
        
        except Exception as e:
            print(f"❌ Error general scrapeando {base_url}: {e}")
        
        return results
    
    def _parse_lottery_content(self, content: str, start_date: datetime, end_date: datetime, source_url: str = "") -> List[Dict[str, Any]]:
        """
        Parsea el contenido extraído buscando resultados de lotería de las páginas específicas
        """
        results = []
        
        if not content:
            return results
        
        try:
            # Usar parser específico según la fuente
            if 'loteka.com.do' in source_url.lower():
                results.extend(self._parse_loteka_content(content, start_date, end_date))
                if not results:
                    results.extend(self._parse_generic_content(content, start_date, end_date))
            elif 'bolomagico.com' in source_url.lower():
                results.extend(self._parse_bolomagico_content(content, start_date, end_date))
            elif 'loteriasdominicanas.com' in source_url.lower():
                results.extend(self._parse_loteriasdominicanas_content(content, start_date, end_date))
            else:
                results.extend(self._parse_generic_content(content, start_date, end_date))
        
        except Exception as e:
            print(f"Error parseando contenido: {e}")
        
        return results
    
    def _parse_loteka_content(self, content: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Parsea contenido específico de loteka.com.do
        """
        results = []
        
        try:
            print(f"Parseando contenido de Loteka. Contenido: {len(content)} caracteres")
            
            # Dividir contenido en líneas para procesamiento secuencial
            lines = content.split('\n')
            current_date = None
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Buscar fechas (formato DD/MM/YYYY)
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', line)
                if date_match:
                    try:
                        day, month, year = date_match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                        
                        if start_date <= parsed_date <= end_date:
                            current_date = parsed_date
                            print(f"Fecha válida encontrada: {current_date.strftime('%Y-%m-%d')}")
                    except (ValueError, IndexError):
                        print(f"Error parseando fecha: {line}")
                
                # Si encontramos indicadores de posición, buscar números en las siguientes líneas
                # SOLO posiciones 1, 2, 3 para Quiniela Loteka
                if current_date and line in ['1er.', '2do.', '3er.']:
                    position = {'1er.': 1, '2do.': 2, '3er.': 3}.get(line, 0)
                    
                    # Buscar el número en las siguientes líneas
                    j = i + 1
                    while j < len(lines) and j < i + 3:  # Buscar hasta 3 líneas adelante
                        next_line = lines[j].strip()
                        
                        # Verificar si la línea contiene solo números de 1-2 dígitos
                        if re.match(r'^\d{1,2}$', next_line):
                            try:
                                number = int(next_line)
                                if 0 <= number <= 99:
                                    result = {
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'number': number,
                                        'position': position,
                                        'prize_amount': 0,
                                        'draw_type': 'quiniela'
                                    }
                                    results.append(result)
                                    print(f"Número encontrado: {line} {number} para fecha {current_date.strftime('%Y-%m-%d')}")
                                    break
                            except ValueError:
                                pass
                        j += 1
                
                # Buscar patrones en línea con posiciones específicas
                position_patterns = {
                    r'1er\.\s*(\d{2})': 1,
                    r'2do\.\s*(\d{2})': 2, 
                    r'3er\.\s*(\d{2})': 3,
                }
                
                for pattern, pos in position_patterns.items():
                    matches = re.findall(pattern, line)
                    for number_str in matches:
                        try:
                            number = int(number_str)
                            if 0 <= number <= 99 and current_date:
                                # Verificar que no hayamos agregado ya esta fecha-posición
                                duplicate_check = f"{current_date.strftime('%Y-%m-%d')}_{pos}"
                                if not any(f"{r['date']}_{r['position']}" == duplicate_check for r in results):
                                    result = {
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'number': number,
                                        'position': pos,  # Posición correcta basada en patrón
                                        'prize_amount': 0,
                                        'draw_type': 'quiniela'
                                    }
                                    results.append(result)
                                    print(f"Número en línea encontrado: {number} (pos {pos}) para fecha {current_date.strftime('%Y-%m-%d')}")
                        except ValueError:
                            continue
                
                i += 1
        
        except Exception as e:
            print(f"❌ Error parseando contenido de Loteka: {e}")
        
        print(f"Total resultados parseados de Loteka: {len(results)}")
        return results
    
    def _parse_loteriasdominicanas_content(self, content: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Parsea contenido específico de loteriasdominicanas.com
        """
        results = []
        
        try:
            # Buscar patrones como "348996" (6 dígitos para quiniela)
            lines = content.split('\n')
            
            current_date = datetime.now()
            
            for line in lines:
                line = line.strip()
                
                # Buscar fechas (formato DD-MM)
                date_match = re.search(r'(\d{1,2})-(\d{1,2})', line)
                if date_match:
                    try:
                        day, month = date_match.groups()
                        # Asumir año actual
                        parsed_date = datetime(datetime.now().year, int(month), int(day))
                        if start_date <= parsed_date <= end_date:
                            current_date = parsed_date
                    except (ValueError, IndexError):
                        pass
                
                # Buscar números de quiniela loteka con validación estricta
                if 'quiniela' in line.lower() or 'loteka' in line.lower():
                    # Usar patrones definidos para loteriasdominicanas
                    patterns = self.number_patterns.get('loteriasdominicanas', [])
                    
                    for pattern in patterns:
                        if pattern == r'(\d{6})':
                            # Número de 6 dígitos dividido en 3 pares
                            matches = re.findall(pattern, line)
                            for number_str in matches:
                                if len(number_str) == 6:
                                    for i in range(0, 6, 2):
                                        try:
                                            number = int(number_str[i:i+2])
                                            if 0 <= number <= 99:
                                                results.append({
                                                    'date': current_date.strftime('%Y-%m-%d'),
                                                    'number': number,
                                                    'position': (i // 2) + 1,
                                                    'prize_amount': 0,
                                                    'draw_type': 'quiniela'
                                                })
                                        except ValueError:
                                            continue
                        else:
                            # Otros patrones
                            matches = re.findall(pattern, line)
                            for match in matches:
                                if isinstance(match, tuple):
                                    # Patrón con grupos múltiples
                                    for i, num_str in enumerate(match[:3]):
                                        try:
                                            number = int(num_str)
                                            if 0 <= number <= 99:
                                                results.append({
                                                    'date': current_date.strftime('%Y-%m-%d'),
                                                    'number': number,
                                                    'position': i + 1,
                                                    'prize_amount': 0,
                                                    'draw_type': 'quiniela'
                                                })
                                        except ValueError:
                                            continue
        
        except Exception as e:
            print(f"Error parseando contenido de LoteriasDominicanas: {e}")
        
        return results
    
    def _parse_generic_content(self, content: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Parsing específico SOLO para Quiniela Loteka (validaciones estrictas)
        """
        results = []
        
        try:
            lines = content.split('\n')
            current_date = None
            
            for line in lines:
                line_original = line.strip()
                line = line_original.lower()
                
                # Buscar fechas en diferentes formatos
                date_patterns = [
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, line)
                    if date_match:
                        try:
                            if '/' in line:
                                day, month, year = date_match.groups()
                            elif '-' in line and date_match.group(1).isdigit() and len(date_match.group(1)) == 4:
                                year, month, day = date_match.groups()
                            else:
                                day, month, year = date_match.groups()
                                
                            parsed_date = datetime(int(year), int(month), int(day))
                            
                            if start_date <= parsed_date <= end_date:
                                current_date = parsed_date
                            break
                        except (ValueError, IndexError):
                            continue
                
                # VALIDACIÓN ESTRICTA: Solo procesar líneas que contengan ESPECÍFICAMENTE "quiniela loteka"
                if current_date and ('quiniela loteka' in line or 'loteka quiniela' in line):
                    simple_patterns = [r'(\d{2})']
                    for pattern in simple_patterns:
                        numbers = re.findall(pattern, line_original)  # Usar línea original para números
                        for i, number_str in enumerate(numbers[:3]):  # Limitar a 3 números por línea
                            try:
                                number = int(number_str)
                                if 0 <= number <= 99:
                                    results.append({
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'number': number,
                                        'position': i + 1,
                                        'prize_amount': 0,
                                        'draw_type': 'quiniela'  # Asegurar que es quiniela
                                    })
                                    print(f"📍 Quiniela Loteka genérica encontrada: {number} para fecha {current_date.strftime('%Y-%m-%d')}")
                            except ValueError:
                                continue
        
        except Exception as e:
            print(f"Error en parsing de Quiniela Loteka: {e}")
        
        print(f"Total resultados de Quiniela Loteka (genérico): {len(results)}")
        return results
    
    def get_latest_results(self) -> List[Dict[str, Any]]:
        """
        Obtiene los resultados más recientes disponibles
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Última semana
        
        return self.scrape_historical_data(start_date, end_date)
    
    def validate_scraped_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida y limpia los datos obtenidos con validación estricta
        """
        if not data:
            return []
            
        validated_data = []
        date_position_tracker = {}  # Para rastrear posiciones por fecha
        
        for item in data:
            try:
                # Validar campos requeridos
                if not all(key in item for key in ['date', 'number']):
                    continue
                
                # Validar fecha
                try:
                    parsed_date = datetime.strptime(item['date'], '%Y-%m-%d')
                    date_str = item['date']
                except ValueError:
                    print(f"❌ Fecha inválida: {item.get('date', 'N/A')}")
                    continue
                
                # Validar número (rango Quiniela: 0-99)
                try:
                    number = int(item['number'])
                    if not (0 <= number <= 99):
                        print(f"❌ Número fuera de rango: {number}")
                        continue
                except (ValueError, TypeError):
                    print(f"❌ Número inválido: {item.get('number', 'N/A')}")
                    continue
                
                # Validar posición (1, 2, 3 solamente)
                position = item.get('position', 1)
                if not isinstance(position, int) or position < 1 or position > 3:
                    print(f"❌ Posición inválida {position} para fecha {date_str}")
                    continue
                
                # Verificar duplicados por fecha-posición
                date_pos_key = f"{date_str}_{position}"
                if date_pos_key in date_position_tracker:
                    existing_number = date_position_tracker[date_pos_key]
                    print(f"⚠️ Duplicado detectado para {date_str} posición {position}: {existing_number} vs {number}")
                    continue  # Saltar duplicados
                
                # Registrar en tracker
                date_position_tracker[date_pos_key] = number
                
                # Normalizar datos
                validated_item = {
                    'date': date_str,
                    'number': number,
                    'position': position,
                    'prize_amount': item.get('prize_amount', 0),
                    'draw_type': 'quiniela'
                }
                
                validated_data.append(validated_item)
                
            except Exception as e:
                print(f"❌ Error validando item {item}: {e}")
                continue
        
        # Verificar completitud por fecha
        self._verify_date_completeness(validated_data)
        
        print(f"📊 Total datos validados: {len(validated_data)}")
        return validated_data
    
    def _verify_date_completeness(self, data: List[Dict[str, Any]]) -> None:
        """
        Verifica que cada fecha tenga los 3 números esperados (posiciones 1, 2, 3)
        """
        date_counts = {}
        
        for item in data:
            date_str = item['date']
            if date_str not in date_counts:
                date_counts[date_str] = set()
            date_counts[date_str].add(item['position'])
        
        complete_dates = 0
        incomplete_dates = 0
        
        for date_str, positions in date_counts.items():
            expected_positions = {1, 2, 3}
            if positions == expected_positions:
                complete_dates += 1
            else:
                incomplete_dates += 1
                missing = expected_positions - positions
                print(f"⚠️ Fecha incompleta {date_str}: faltan posiciones {missing}")
        
        print(f"📋 Fechas completas: {complete_dates}, incompletas: {incomplete_dates}")
        
        if incomplete_dates > complete_dates * 0.5:  # Más del 50% incompletas
            print(f"⚠️ ADVERTENCIA: Muchas fechas incompletas ({incomplete_dates}/{len(date_counts)}). Los datos podrían tener problemas de calidad.")
    
    def get_scraping_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del sistema de scraping
        """
        status = {
            'sources_available': len(self.base_urls),
            'last_attempt': datetime.now().isoformat(),
            'sample_data_available': 0,  # Ya no hay datos de prueba
            'real_data_only': True,  # Solo datos reales
            'status': 'ready'
        }
        
        return status
        
    def scrape_massive_historical_data(self, target_days: int = 720) -> List[Dict[str, Any]]:
        """
        Recopila datos históricos masivos para el número de días especificado
        
        Args:
            target_days: Número de días de datos históricos a recopilar (por defecto 720)
            
        Returns:
            Lista de resultados de sorteos
        """
        print(f"🎯 INICIANDO recopilación masiva de {target_days} días de datos históricos")
        
        all_results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=target_days)
        
        # Dividir en lotes para procesamiento eficiente
        current_date = start_date
        batch_count = 0
        
        while current_date <= end_date:
            batch_end = min(current_date + timedelta(days=self.batch_size), end_date)
            batch_count += 1
            
            print(f"📦 Procesando lote {batch_count}: {current_date.strftime('%Y-%m-%d')} a {batch_end.strftime('%Y-%m-%d')}")
            
            # Intentar recopilar datos del lote actual
            batch_results = self._scrape_date_range_batch(current_date, batch_end)
            
            if batch_results:
                validated_results = self.validate_scraped_data(batch_results)
                all_results.extend(validated_results)
                print(f"✅ Lote {batch_count}: {len(validated_results)} registros válidos obtenidos")
            else:
                print(f"⚠️ Lote {batch_count}: Sin datos obtenidos")
            
            # Pausa entre lotes para ser respetuoso
            delay = random.uniform(*self.request_delay)
            print(f"⏸️ Pausa de {delay:.1f} segundos entre lotes...")
            time.sleep(delay)
            
            current_date = batch_end + timedelta(days=1)
        
        print(f"🎉 RECOPILACIÓN COMPLETADA: {len(all_results)} registros históricos obtenidos de {target_days} días")
        return all_results
    
    def _scrape_date_range_batch(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Recopila datos de un rango específico de fechas usando múltiples fuentes con agregación
        """
        all_results = []
        successful_sources = 0
        
        # Intentar TODAS las fuentes para llenar vacíos (no hacer break)
        for base_url in self.base_urls:
            try:
                print(f"🔄 Probando fuente: {base_url}")
                source_results = self._scrape_from_enhanced_source(base_url, start_date, end_date)
                
                if source_results:
                    # Validar datos de esta fuente antes de agregarlos
                    validated_source_results = self.validate_scraped_data(source_results)
                    if validated_source_results:
                        all_results.extend(validated_source_results)
                        successful_sources += 1
                        print(f"✅ Datos obtenidos de {base_url}: {len(validated_source_results)} registros validados")
                    else:
                        print(f"⚠️ {base_url}: datos obtenidos pero no pasaron validación")
                else:
                    print(f"❌ Sin datos de {base_url}")
                    
            except Exception as e:
                print(f"❌ Error en {base_url}: {e}")
                continue
        
        # Deduplicar por (fecha, posición) manteniendo el primer encontrado
        deduplicated_results = self._deduplicate_by_date_position(all_results)
        
        print(f"📊 Lote completado: {successful_sources}/{len(self.base_urls)} fuentes exitosas")
        print(f"📊 Total registros después de deduplicación: {len(deduplicated_results)}")
        
        return deduplicated_results
    
    def _deduplicate_by_date_position(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Elimina duplicados basándose en (fecha, posición), manteniendo el primero
        """
        seen = set()
        deduplicated = []
        
        for item in data:
            key = (item['date'], item['position'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(item)
            else:
                print(f"🔄 Eliminando duplicado: {item['date']} pos {item['position']}")
        
        return deduplicated
    
    def _scrape_from_enhanced_source(self, base_url: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Versión mejorada de scraping con soporte para múltiples fuentes y datos históricos
        """
        results = []
        
        try:
            # Determinar endpoints específicos según la fuente
            endpoints = self._get_source_endpoints(base_url, start_date, end_date)
            
            for endpoint in endpoints:
                for attempt in range(self.max_retries):
                    try:
                        print(f"🔍 Intento {attempt + 1}: {endpoint}")
                        response = requests.get(endpoint, headers=self.headers, timeout=20)
                        
                        if response.status_code == 200:
                            # Usar parsing específico según la fuente
                            parsed_results = self._parse_by_source(response.text, base_url, start_date, end_date)
                            
                            if parsed_results:
                                results.extend(parsed_results)
                                print(f"✅ {len(parsed_results)} registros obtenidos de {endpoint}")
                                return results
                        else:
                            print(f"⚠️ Status {response.status_code} para {endpoint}")
                            
                    except requests.RequestException as e:
                        print(f"❌ Error en intento {attempt + 1} para {endpoint}: {e}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                
                # Pausa entre endpoints
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            print(f"❌ Error general en scraping de {base_url}: {e}")
            
        return results
    
    def _get_source_endpoints(self, base_url: str, start_date: datetime, end_date: datetime) -> List[str]:
        """
        Genera endpoints con iteración real día por día para datos históricos
        """
        endpoints = []
        
        if "loteka.com.do" in base_url:
            # Endpoints estáticos para Loteka oficial
            endpoints.extend([
                f"{base_url}/quiniela",
                f"{base_url}/resultados",
                f"{base_url}",
            ])
            
            # Intentar endpoints por fecha si existen
            current_date = start_date
            while current_date <= end_date:
                date_formats = [
                    current_date.strftime("%Y-%m-%d"),
                    current_date.strftime("%d-%m-%Y"),
                    current_date.strftime("%Y/%m/%d"),
                ]
                
                for date_str in date_formats:
                    endpoints.extend([
                        f"{base_url}/resultados/{date_str}",
                        f"{base_url}/quiniela/{date_str}",
                        f"{base_url}/historico/{date_str}",
                    ])
                
                current_date += timedelta(days=1)  # Iteración día por día
                
        elif "bolomagico.com" in base_url:
            # Bolomagico: iterar día por día
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                date_str_alt = current_date.strftime("%Y/%m/%d")
                date_str_short = current_date.strftime("%m-%d-%Y")
                
                endpoints.extend([
                    f"{base_url}/en/loteria/loteka/{date_str}",
                    f"{base_url}/loteria/loteka/{date_str}",
                    f"{base_url}/en/lottery-results/{date_str_alt}",
                    f"{base_url}/results/{date_str_short}",
                ])
                
                current_date += timedelta(days=1)  # Día por día para completitud
                
        elif "loteriasdominicanas.com" in base_url:
            # Loterías Dominicanas: iterar día por día
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%d-%m-%Y")  # DD-MM-YYYY
                date_str_alt = current_date.strftime("%Y-%m-%d")  # YYYY-MM-DD
                
                endpoints.extend([
                    f"{base_url}/resultados/{date_str}",
                    f"{base_url}/loteka/{date_str}",
                    f"{base_url}/results/{date_str_alt}",
                    f"{base_url}/historical/{date_str}",
                ])
                
                current_date += timedelta(days=1)  # Día por día
        else:
            # Para otras fuentes, endpoints básicos
            endpoints.extend([f"{base_url}", f"{base_url}/lottery", f"{base_url}/results"])
            
        # Agregar endpoints base al final
        endpoints.extend([
            f"{base_url}/en/loteria/loteka/" if "bolomagico.com" in base_url else f"{base_url}",
        ])
            
        return endpoints
    
    def _parse_by_source(self, content: str, base_url: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Parser específico según la fuente
        """
        results = []
        
        try:
            # Extraer contenido con trafilatura
            clean_content = trafilatura.extract(content)
            if not clean_content:
                clean_content = content
            
            # Parser específico por fuente
            if "loteka.com.do" in base_url:
                results = self._parse_loteka_content(clean_content, start_date, end_date)
            elif "bolomagico.com" in base_url:
                results = self._parse_bolomagico_content(clean_content, start_date, end_date)
            elif "loteriasdominicanas.com" in base_url:
                results = self._parse_loteriasdominicanas_content(clean_content, start_date, end_date)
            else:
                results = self._parse_generic_content(clean_content, start_date, end_date)
                
        except Exception as e:
            print(f"❌ Error parseando contenido de {base_url}: {e}")
            
        return results
    
    def _parse_bolomagico_content(self, content: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Parser específico para bolomagico.com
        """
        results = []
        
        try:
            lines = content.split('\\n')
            current_date = None
            
            for line in lines:
                line = line.strip()
                
                # Buscar fechas en formato bolomagico
                date_patterns = [
                    r'(\\d{4})-(\\d{1,2})-(\\d{1,2})',
                    r'(\\d{1,2})/(\\d{1,2})/(\\d{4})',
                    r'(\\d{1,2})-(\\d{1,2})-(\\d{4})'
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, line)
                    if date_match:
                        try:
                            groups = date_match.groups()
                            if len(groups[0]) == 4:  # Formato YYYY-MM-DD
                                year, month, day = groups
                            else:  # Formato DD/MM/YYYY o DD-MM-YYYY
                                day, month, year = groups
                                
                            parsed_date = datetime(int(year), int(month), int(day))
                            if start_date <= parsed_date <= end_date:
                                current_date = parsed_date
                        except (ValueError, IndexError):
                            continue
                
                # Buscar números de Quiniela Loteka
                if current_date and ('quiniela' in line.lower() or 'loteka' in line.lower()):
                    # Usar patrones específicos de bolomagico
                    patterns = self.number_patterns.get('bolomagico', [])
                    for pattern in patterns:
                        matches = re.findall(pattern, line)
                        for i, match in enumerate(matches[:3]):
                            try:
                                # Manejar diferentes tipos de matches
                                if isinstance(match, tuple):
                                    number_str = match[0] if match[0] else match[1] if len(match) > 1 else ''
                                else:
                                    number_str = match
                                    
                                number = int(number_str)
                                if 0 <= number <= 99:
                                    results.append({
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'number': number,
                                        'position': i + 1,
                                        'prize_amount': 0,
                                        'draw_type': 'quiniela'
                                    })
                            except (ValueError, IndexError):
                                continue
                    
                    # Patrón genérico para números consecutivos de 2 dígitos
                    generic_pattern = r'(\d{2})\s+(\d{2})\s+(\d{2})'
                    matches = re.findall(generic_pattern, line)
                    if matches and not results:  # Solo si no encontramos con patrones específicos
                        for match_group in matches:
                            for i, number_str in enumerate(match_group):
                                try:
                                    number = int(number_str)
                                    if 0 <= number <= 99:
                                        results.append({
                                            'date': current_date.strftime('%Y-%m-%d'),
                                            'number': number,
                                            'position': i + 1,
                                            'prize_amount': 0,
                                            'draw_type': 'quiniela'
                                        })
                                except ValueError:
                                    continue
                                
        except Exception as e:
            print(f"❌ Error parseando contenido de bolomagico: {e}")
            
        return results
