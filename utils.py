from datetime import datetime, timedelta
from typing import Union, Optional, List, Dict, Any
import re

def format_currency(amount: Union[int, float], currency: str = "DOP") -> str:
    """
    Formatea una cantidad como moneda dominicana
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda (default: DOP)
    
    Returns:
        str: Cantidad formateada como moneda
    """
    if amount == 0:
        return f"0 {currency}"
    
    try:
        # Formatear con separadores de miles
        if amount >= 1000000:
            formatted = f"{amount:,.0f}"
        else:
            formatted = f"{amount:,.0f}"
        
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"0 {currency}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje
    
    Args:
        value: Valor decimal a formatear (ej: 0.25 para 25%)
        decimals: Número de decimales a mostrar
    
    Returns:
        str: Valor formateado como porcentaje
    """
    try:
        return f"{value * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Valida que un rango de fechas sea lógico
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
    
    Returns:
        bool: True si el rango es válido
    """
    if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
        return False
    
    # La fecha de inicio debe ser anterior a la fecha de fin
    if start_date >= end_date:
        return False
    
    # No debe ser un rango demasiado grande (más de 5 años)
    max_range = timedelta(days=365 * 5)
    if (end_date - start_date) > max_range:
        return False
    
    # La fecha de fin no debe ser en el futuro
    if end_date > datetime.now():
        return False
    
    return True

def parse_lottery_number(number_str: str) -> Optional[int]:
    """
    Parsea un string que representa un número de lotería
    
    Args:
        number_str: String que contiene el número
    
    Returns:
        Optional[int]: Número parseado o None si es inválido
    """
    if not isinstance(number_str, str):
        return None
    
    # Limpiar el string
    cleaned = re.sub(r'[^\d]', '', number_str.strip())
    
    if not cleaned:
        return None
    
    try:
        number = int(cleaned)
        
        # Validar rango típico de Quiniela (00-99)
        if 0 <= number <= 99:
            return number
        
        return None
    except ValueError:
        return None

def format_date_spanish(date: datetime) -> str:
    """
    Formatea una fecha en español
    
    Args:
        date: Fecha a formatear
    
    Returns:
        str: Fecha formateada en español
    """
    months_spanish = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    
    days_spanish = {
        0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
        4: "viernes", 5: "sábado", 6: "domingo"
    }
    
    try:
        day_name = days_spanish[date.weekday()]
        month_name = months_spanish[date.month]
        
        return f"{day_name}, {date.day} de {month_name} de {date.year}"
    except (KeyError, AttributeError):
        return date.strftime("%Y-%m-%d")

def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Calcula la diferencia en días entre dos fechas
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
    
    Returns:
        int: Número de días de diferencia
    """
    try:
        return (end_date - start_date).days
    except (TypeError, AttributeError):
        return 0

def clean_text_content(text: str) -> str:
    """
    Limpia contenido de texto para análisis
    
    Args:
        text: Texto a limpiar
    
    Returns:
        str: Texto limpio
    """
    if not isinstance(text, str):
        return ""
    
    # Remover caracteres especiales y normalizar espacios
    cleaned = re.sub(r'[^\w\s\d.-]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip().lower()

def extract_numbers_from_text(text: str) -> List[int]:
    """
    Extrae números de lotería de un texto
    
    Args:
        text: Texto que contiene números
    
    Returns:
        List[int]: Lista de números válidos encontrados
    """
    if not isinstance(text, str):
        return []
    
    # Patrones para encontrar números de 1-2 dígitos
    patterns = [
        r'\b(\d{1,2})\b',  # Números de 1-2 dígitos como palabras completas
        r'(\d{2})',        # Números de 2 dígitos exactos
    ]
    
    numbers = []
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            number = parse_lottery_number(match)
            if number is not None and number not in numbers:
                numbers.append(number)
    
    return sorted(numbers)

def validate_lottery_result(result: Dict[str, Any]) -> bool:
    """
    Valida que un resultado de lotería tenga el formato correcto
    
    Args:
        result: Diccionario con datos del resultado
    
    Returns:
        bool: True si el resultado es válido
    """
    required_fields = ['date', 'number']
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in result:
            return False
    
    # Validar fecha
    try:
        if isinstance(result['date'], str):
            datetime.strptime(result['date'], '%Y-%m-%d')
        elif not isinstance(result['date'], datetime):
            return False
    except ValueError:
        return False
    
    # Validar número
    number = result['number']
    if not isinstance(number, int) or not (0 <= number <= 99):
        return False
    
    # Validar campos opcionales
    if 'position' in result:
        position = result['position']
        if not isinstance(position, int) or position < 1:
            return False
    
    if 'prize_amount' in result:
        prize = result['prize_amount']
        if not isinstance(prize, (int, float)) or prize < 0:
            return False
    
    return True

def generate_date_range(start_date: datetime, end_date: datetime, step_days: int = 1) -> List[datetime]:
    """
    Genera una lista de fechas en un rango dado
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        step_days: Incremento en días
    
    Returns:
        List[datetime]: Lista de fechas
    """
    if not validate_date_range(start_date, end_date):
        return []
    
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=step_days)
    
    return dates

def get_confidence_level_text(confidence: float) -> str:
    """
    Convierte un valor de confianza numérico a texto descriptivo
    
    Args:
        confidence: Valor de confianza (0-1)
    
    Returns:
        str: Descripción textual del nivel de confianza
    """
    if confidence >= 0.8:
        return "Muy Alta"
    elif confidence >= 0.6:
        return "Alta"
    elif confidence >= 0.4:
        return "Media"
    elif confidence >= 0.2:
        return "Baja"
    else:
        return "Muy Baja"

def format_number_with_leading_zero(number: int) -> str:
    """
    Formatea un número con cero inicial si es necesario (para quiniela)
    
    Args:
        number: Número a formatear
    
    Returns:
        str: Número formateado con dos dígitos
    """
    try:
        return f"{number:02d}"
    except (ValueError, TypeError):
        return "00"

def calculate_statistics_summary(values: List[Union[int, float]]) -> Dict[str, float]:
    """
    Calcula un resumen estadístico de una lista de valores
    
    Args:
        values: Lista de valores numéricos
    
    Returns:
        Dict[str, float]: Resumen estadístico
    """
    if not values:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std_dev': 0.0
        }
    
    try:
        import statistics
        
        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
        }
    except Exception:
        return {
            'count': len(values),
            'mean': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2],
            'min': min(values),
            'max': max(values),
            'std_dev': 0.0
        }
