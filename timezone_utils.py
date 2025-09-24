#!/usr/bin/env python3
"""
Utilidades de zona horaria para República Dominicana (UTC-4)
"""

import pytz
from datetime import datetime, timedelta
from typing import Optional

# Zona horaria de República Dominicana
DOMINICAN_TZ = pytz.timezone('America/Santo_Domingo')

def get_dominican_now() -> datetime:
    """
    Obtiene la fecha y hora actual en la zona horaria de República Dominicana (UTC-4)
    
    Returns:
        datetime: Fecha y hora actual en zona horaria dominicana
    """
    return datetime.now(DOMINICAN_TZ)

def get_dominican_today_str() -> str:
    """
    Obtiene la fecha actual en República Dominicana como string YYYY-MM-DD
    
    Returns:
        str: Fecha actual en formato YYYY-MM-DD
    """
    return get_dominican_now().strftime('%Y-%m-%d')

def get_dominican_datetime_str() -> str:
    """
    Obtiene la fecha y hora actual en República Dominicana como string
    
    Returns:
        str: Fecha y hora actual en formato YYYY-MM-DD HH:MM:SS
    """
    return get_dominican_now().strftime('%Y-%m-%d %H:%M:%S')

def convert_to_dominican_tz(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convierte un datetime a la zona horaria dominicana
    
    Args:
        dt: datetime a convertir (puede ser None)
        
    Returns:
        datetime: datetime convertido a zona horaria dominicana, o None
    """
    if dt is None:
        return None
    
    # Si no tiene timezone, asumir UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(DOMINICAN_TZ)

def is_data_current(latest_date_str: str, max_days_behind: int = 1) -> bool:
    """
    Verifica si los datos están actualizados según la zona horaria dominicana
    
    Args:
        latest_date_str: Fecha más reciente en formato YYYY-MM-DD
        max_days_behind: Máximo número de días de retraso aceptable
        
    Returns:
        bool: True si los datos están actualizados
    """
    if not latest_date_str:
        return False
    
    try:
        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
        today_dominican = get_dominican_now().date()
        days_behind = (today_dominican - latest_date).days
        
        return days_behind <= max_days_behind
    except:
        return False

def get_date_range_dominican(days_back: int = 3) -> tuple[datetime, datetime]:
    """
    Obtiene un rango de fechas basado en la zona horaria dominicana
    
    Args:
        days_back: Número de días hacia atrás para el inicio del rango
        
    Returns:
        tuple: (start_date, end_date) en zona horaria dominicana
    """
    end_date = get_dominican_now()
    
    # Simplificado: usar fechas naive para compatibilidad
    end_date_naive = end_date.replace(tzinfo=None)
    start_date_naive = end_date_naive - timedelta(days=days_back)
    
    return start_date_naive, end_date_naive

def format_dominican_time(dt: datetime, include_timezone: bool = True) -> str:
    """
    Formatea un datetime en zona horaria dominicana
    
    Args:
        dt: datetime a formatear
        include_timezone: Si incluir información de zona horaria
        
    Returns:
        str: datetime formateado
    """
    dominican_dt = convert_to_dominican_tz(dt)
    if dominican_dt is None:
        return "N/A"
    
    if include_timezone:
        return dominican_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    else:
        return dominican_dt.strftime('%Y-%m-%d %H:%M:%S')