"""
config.py
---------
Configuración central del proyecto Santi & Go.

Aquí vive:
  - La carga segura del token de la API de Tiempo (vía .env).
  - Los umbrales que definen si es apto o no para deporte.
  - El catálogo de concellos de Galicia con sus coordenadas (lat, lon).
"""

import os
from dotenv import load_dotenv

# Carga el .env situado en la raíz del proyecto (no se versiona en git).
load_dotenv()

# ---------------------------------------------------------------------------
# API de OpenWeatherMap para obtener el tiempo actual de cada concello.
# ---------------------------------------------------------------------------
# El token se solicita por correo a OpenWeatherMap / por el canal del reto.
# NUNCA se escribe en el código: se inyecta por variable de entorno.
WEATHER_TOKEN = os.getenv("OPENWEATHER_API_KEY", "")

# Endpoint de predicción numérica de OpenWeatherMap.
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Timeout (segundos) por petición HTTP a OpenWeatherMap.
HTTP_TIMEOUT = 8

# Cache en memoria: segundos que consideramos "fresco" un dato.
CACHE_TTL_SECONDS = 600

# Nº de peticiones concurrentes al refrescar todos los concellos a la vez.
MAX_WORKERS = 6

# ---------------------------------------------------------------------------
# Umbrales para evaluar si es apto para deporte al aire libre
# ---------------------------------------------------------------------------
UMBRAL_LLUVIA_MM = 2.0     # mm de precipitación a partir de la cual NO se recomienda
UMBRAL_TEMP_MIN = 5.0      # ºC: por debajo, frío extremo
UMBRAL_TEMP_MAX = 30.0     # ºC: por encima, calor extremo
UMBRAL_VIENTO_KMH = 25.0   # km/h: por encima, demasiado viento

# ---------------------------------------------------------------------------
# Catálogo de concellos de Galicia (cobertura de las 4 provincias)
# ---------------------------------------------------------------------------
# Coordenadas en grados decimales (WGS84).
# Para añadir un municipio basta con sumar una entrada aquí:
# la lista alimenta tanto el Geomap como la variable $municipio del dashboard.
CONCELLOS = [
    # --- A Coruña ---
    {"nombre": "A Coruña",                  "lat": 43.3623, "lon": -8.4115, "provincia": "A Coruña"},
    {"nombre": "Santiago de Compostela",    "lat": 42.8805, "lon": -8.5457, "provincia": "A Coruña"},
    {"nombre": "Ferrol",                    "lat": 43.4839, "lon": -8.2330, "provincia": "A Coruña"},
    {"nombre": "Narón",                     "lat": 43.5036, "lon": -8.1860, "provincia": "A Coruña"},
    {"nombre": "Carballo",                  "lat": 43.2130, "lon": -8.6910, "provincia": "A Coruña"},
    {"nombre": "Ribeira",                   "lat": 42.5560, "lon": -8.9913, "provincia": "A Coruña"},
    {"nombre": "A Estrada",                 "lat": 42.6890, "lon": -8.4890, "provincia": "A Coruña"},
    # --- Lugo ---
    {"nombre": "Lugo",                      "lat": 43.0096, "lon": -7.5560, "provincia": "Lugo"},
    {"nombre": "Monforte de Lemos",         "lat": 42.5218, "lon": -7.5140, "provincia": "Lugo"},
    {"nombre": "Viveiro",                   "lat": 43.6618, "lon": -7.5944, "provincia": "Lugo"},
    {"nombre": "Sarria",                    "lat": 42.7810, "lon": -7.4140, "provincia": "Lugo"},
    {"nombre": "Burela",                    "lat": 43.6630, "lon": -7.3560, "provincia": "Lugo"},
    # --- Ourense ---
    {"nombre": "Ourense",                   "lat": 42.3358, "lon": -7.8639, "provincia": "Ourense"},
    {"nombre": "Verín",                     "lat": 41.9410, "lon": -7.4380, "provincia": "Ourense"},
    {"nombre": "O Barco de Valdeorras",     "lat": 42.4160, "lon": -6.9870, "provincia": "Ourense"},
    # --- Pontevedra ---
    {"nombre": "Vigo",                      "lat": 42.2406, "lon": -8.7207, "provincia": "Pontevedra"},
    {"nombre": "Pontevedra",                "lat": 42.4310, "lon": -8.6444, "provincia": "Pontevedra"},
    {"nombre": "Vilagarcía de Arousa",      "lat": 42.5966, "lon": -8.7656, "provincia": "Pontevedra"},
    {"nombre": "Sanxenxo",                  "lat": 42.4000, "lon": -8.8070, "provincia": "Pontevedra"},
    {"nombre": "Lalín",                     "lat": 42.6610, "lon": -8.1130, "provincia": "Pontevedra"},
]


def get_concello(nombre: str):
    """Devuelve el dict del concello por nombre (sin distinguir mayúsculas/acentos
    de forma estricta: comparación case-insensitive). None si no existe."""
    if not nombre:
        return None
    objetivo = nombre.strip().lower()
    for c in CONCELLOS:
        if c["nombre"].lower() == objetivo:
            return c
    return None
