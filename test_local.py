"""
test_local.py — pruebas rápidas SIN llamar a la API real.
Valida:
  1) La lógica evaluar_deporte con varios escenarios.
  2) El parseo de una respuesta JSON simulada con la estructura de OpenWeather API.
  3) El endpoint Flask /api/galicia/deporte (con la API mockeada).
"""
import json
from unittest.mock import patch

from evaluator import evaluar_deporte
import weather_client


# ---------- 1) Lógica de evaluación ----------
print("== Lógica evaluar_deporte ==")
casos = [
    (18, 0.0, 10),   # ideal
    (18, 0.5, 10),   # lluvia
    (2,  0.0, 10),   # frío
    (35, 0.0, 10),   # calor
    (18, 0.0, 40),   # viento
    (None, None, None),  # sin datos
]
for temp, lluvia, viento in casos:
    print(f"  T={temp} P={lluvia} V={viento} -> {evaluar_deporte(temp, lluvia, viento)}")


# ---------- 2) Parser sobre payload simulado de OpenWeather ----------
print("\n== Parser OpenWeather API (payload simulado) ==")
# Simulamos la respuesta real de OpenWeather (viento en m/s, como devuelve la API,
# para probar la conversión a km/h que hace weather_client.py).
fake_openweather_response = {
    "main": {"temp": 19.4},
    "wind": {"speed": 3.0},          # m/s -> se espera conversión a 10.8 km/h
    "rain": {"1h": 0.0},
}


class FakeResp:
    def raise_for_status(self): pass
    def json(self): return fake_openweather_response


with patch.object(weather_client._session, "get", return_value=FakeResp()):
    temp, lluvia, viento = weather_client._consultar_openweather(-8.5457, 42.8805)
print(f"  Parseado -> temp={temp}ºC  lluvia={lluvia}mm  viento={viento}km/h (3 m/s -> esperado 10.8)")
assert viento == 10.8, "La conversión m/s -> km/h falló"
assert lluvia == 0.0 and temp == 19.4, "El parseo de la respuesta falló"
print("  OK parser")


# ---------- 3) Endpoint Flask (API mockeada) ----------
print("\n== Endpoint /api/galicia/deporte ==")
import main

with patch.object(weather_client, "obtener_clima", return_value=(19.4, 0.0, 10.8)):
    client = main.app.test_client()

    # Un municipio
    r = client.get("/api/galicia/deporte?municipio=Santiago de Compostela")
    data = r.json
    print("  ?municipio=Santiago ->", json.dumps(data[0], ensure_ascii=False))
    assert r.status_code == 200 and len(data) == 1
    assert data[0]["ciudad"] == "Santiago de Compostela"
    assert data[0]["apto"] == 1

    # Todos
    r = client.get("/api/galicia/deporte")
    data = r.json
    print(f"  (todos) -> {len(data)} concellos, primero: {data[0]['ciudad']}")
    assert all("latitud" in d and "longitud" in d for d in data)

    # Municipio inexistente
    r = client.get("/api/galicia/deporte?municipio=Madrid")
    print("  ?municipio=Madrid ->", r.status_code, r.json)
    assert r.status_code == 404

print("\n✅ TODAS LAS PRUEBAS PASARON")
