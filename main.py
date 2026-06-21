"""
main.py
-------
Punto de entrada de Santi & Go (backend Flask).

Endpoints
---------
GET /api/galicia/deporte
    -> Devuelve un ARRAY con TODOS los concellos del catálogo.
       Pensado para el panel Geomap (pinta todos los puntos a la vez).

GET /api/galicia/deporte?municipio=<nombre>
    -> Devuelve un ARRAY con UN único concello.
       Pensado para los paneles de detalle (gauges/stats) filtrados por $municipio.

GET /health
    -> Comprobación rápida de que el servicio está vivo.

La respuesta SIEMPRE es una lista de objetos (aunque tenga un solo elemento),
con los campos que consume el plugin Infinity de Grafana:
    ciudad, latitud, longitud, temperatura, precipitacion, lluvia,
    viento, apto, recomendacion, trigger_alerta, actualizado
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

import config
import weather_client
from evaluator import evaluar_deporte

app = Flask(__name__)
# CORS abierto: necesario si el datasource Infinity opera en modo navegador.
CORS(app)


def _construir_registro(concello: dict) -> dict:
    """Consulta el clima de un concello y arma el objeto JSON para Grafana."""
    try:
        temp, lluvia, viento = weather_client.obtener_clima(concello)
    except Exception as e:
        # Ante un fallo puntual de la API, no tiramos toda la respuesta:
        # devolvemos el concello con datos nulos y marcado como no apto.
        temp, lluvia, viento = None, None, None
        veredicto = {"apto": 0, "recomendacion": f"Error de datos: {e}"}
    else:
        veredicto = evaluar_deporte(temp, lluvia, viento)

    return {
        "ciudad": concello["nombre"],
        "provincia": concello.get("provincia"),
        "latitud": concello["lat"],
        "longitud": concello["lon"],
        "temperatura": temp,
        "precipitacion": lluvia,
        "lluvia": lluvia,                       # alias para compatibilidad
        "viento": viento,
        "apto": veredicto["apto"],
        "recomendacion": veredicto["recomendacion"],
        # Saca el 1 fijo y haz que dependa de si el concello es apto o no
        "trigger_alerta": 1 if veredicto["apto"] == 0 else 0,
        "actualizado": datetime.now().isoformat(timespec="seconds"),
    }


@app.route("/api/galicia/deporte", methods=["GET"])
def obtener_datos():
    municipio = request.args.get("municipio")

    if municipio:
        # --- Modo detalle: un único concello ---
        concello = config.get_concello(municipio)
        if concello is None:
            return jsonify({"error": f"Concello '{municipio}' no encontrado"}), 404
        registros = [_construir_registro(concello)]
    else:
        # --- Modo regional: todos los concellos (en paralelo) ---
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
            registros = list(pool.map(_construir_registro, config.CONCELLOS))

    res = jsonify(registros)
    # Cabecera para que ngrok no inyecte su página de aviso (rompería el JSON).
    res.headers.add("ngrok-skip-browser-warning", "true")
    return res


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "concellos": len(config.CONCELLOS)})


if __name__ == "__main__":
    # host 0.0.0.0 -> accesible desde ngrok/red local. Puerto estándar de Flask.
    app.run(host="0.0.0.0", port=5000)
