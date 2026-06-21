"""
evaluator.py
------------
Lógica de negocio pura (sin dependencias de Flask ni de la API).

Dada la temperatura, la precipitación y el viento, decide si es buen momento
para hacer deporte al aire libre y devuelve un veredicto estructurado.

Al estar aislada, esta función es trivial de testear y de reutilizar
(p. ej. desde un bot de Telegram que consuma las mismas reglas).
"""

import config


def evaluar_deporte(temp, lluvia, viento):
    """
    Parámetros
    ----------
    temp   : float | None  -> temperatura en ºC
    lluvia : float | None  -> precipitación en mm
    viento : float | None  -> velocidad del viento en km/h

    Retorna
    -------
    dict con:
        apto          : int  (1 = sí, 0 = no)  -> formato cómodo para Grafana
        recomendacion : str  -> texto legible para el ciudadano
    """
    # Si falta algún dato no podemos garantizar nada: marcamos NO apto.
    if temp is None or lluvia is None or viento is None:
        return {"apto": 0, "recomendacion": "Sin datos suficientes"}

    if lluvia > config.UMBRAL_LLUVIA_MM:
        return {"apto": 0, "recomendacion": "No recomendado · Lluvia"}
    if temp < config.UMBRAL_TEMP_MIN:
        return {"apto": 0, "recomendacion": "No recomendado · Frío extremo"}
    if temp > config.UMBRAL_TEMP_MAX:
        return {"apto": 0, "recomendacion": "No recomendado · Calor extremo"}
    if viento > config.UMBRAL_VIENTO_KMH:
        return {"apto": 0, "recomendacion": "No recomendado · Mucho viento"}

    return {"apto": 1, "recomendacion": "¡Ideal para deporte!"}
