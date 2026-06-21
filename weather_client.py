"""
weather_client.py
-----------------
Cliente para la API de OpenWeatherMap (Tiempo en tiempo real).

Responsabilidades:
  - Construir y realizar peticiones a la API de OpenWeather.
  - Normalizar los datos recibidos (temperatura, lluvia, viento) al formato 
    que espera la aplicación.
  - Gestionar errores de API con un modo de respaldo (valores por defecto).
  - Convertir unidades (viento a km/h).
  - Cachear en memoria con TTL para optimizar peticiones.
"""

from datetime import datetime
import time
import requests
import config

# Sesión HTTP reutilizable
_session = requests.Session()
_cache = {}

def _consultar_openweather(lon, lat):
    """
    Consulta la API de OpenWeatherMap. 
    
    Returns:
        tuple: (temperatura_C, precipitacion_mm, viento_kmh).
        Si la API falla, devuelve valores de respaldo seguros.
    """
    API_KEY = config.WEATHER_TOKEN
    url = config.WEATHER_API_URL
    
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }
    
    try:
        resp = _session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        temp = data['main']['temp']
        lluvia = data.get('rain', {}).get('1h', 0)
        viento = data['wind']['speed'] * 3.6
        
        return round(temp, 1), round(lluvia, 1), round(viento, 1)

    except Exception as e:
        print(f"DEBUG: Error en API ({e}). Usando valores de respaldo.")
        return (20.0, 0.0, 10.0)

def obtener_clima(concello: dict):
    """
    Devuelve (temperatura, precipitacion, viento) para un concello,
    usando cache con TTL.
    """
    nombre = concello["nombre"]
    ahora = time.time()

    if nombre in _cache:
        ts, payload = _cache[nombre]
        if ahora - ts < config.CACHE_TTL_SECONDS:
            return payload

    clima = _consultar_openweather(concello["lon"], concello["lat"])
    _cache[nombre] = (ahora, clima)
    return clima