"""Funciones relacionadas con paradas: destinos, líneas que pasan por
ellas, y localización de la parada GTFS más cercana."""

import csv
import os

from app.config import RUTA_STOP_TIMES, RUTA_STOPS
from app.gtfs.loader import cargar_gtfs, obtener_info_lineas, _normalizar_linea
from app.utils.geo import haversine


_cache_destinos_parada = None
_cache_lineas_parada = {}


def obtener_destinos_de_parada(stop_id, linea):
    """Devuelve los destinos GTFS que pasan por una parada y línea."""
    global _cache_destinos_parada

    if _cache_destinos_parada is None:
        _cache_destinos_parada = {}

    clave = (str(stop_id), _normalizar_linea(linea))
    if clave in _cache_destinos_parada:
        return _cache_destinos_parada[clave]

    if not os.path.exists(RUTA_STOP_TIMES):
        _cache_destinos_parada[clave] = []
        return []

    info_viajes = obtener_info_lineas()
    destinos = set()

    with open(RUTA_STOP_TIMES, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("stop_id") != str(stop_id):
                continue

            info = info_viajes.get(row.get("trip_id"))
            if not info:
                continue

            if _normalizar_linea(info["linea"]) != _normalizar_linea(linea):
                continue

            destino = info.get("destino", "").strip()
            if destino:
                destinos.add(destino)

    resultado = sorted(destinos)
    _cache_destinos_parada[clave] = resultado
    return resultado

def obtener_destino_por_direccion(linea, direccion, stop_id):
    """Determina un destino útil para una respuesta TMG.

    Primero usa el GTFS de la propia parada. Si la parada solo tiene un
    destino para esa línea (caso de la 15040 -> Avellaneda), ese destino es
    inequívoco y se utiliza para ambos sentidos consultados a TMG.

    Si hay varios destinos, se intenta usar el orden de extremos de
    route_long_name como aproximación a anada/torna.
    """
    destinos = obtener_destinos_de_parada(stop_id, linea)

    if len(destinos) == 1:
        return destinos[0]

    info_viajes, rutas = cargar_gtfs()
    route_id = None
    linea_normalizada = _normalizar_linea(linea)

    for info in info_viajes.values():
        if _normalizar_linea(info.get("linea")) == linea_normalizada:
            route_id = info.get("route_id")
            break

    if route_id:
        nombre = rutas.get(route_id, {}).get("nombre", "")
        extremos = [x.strip() for x in nombre.split("-") if x.strip()]
        if len(extremos) >= 2:
            if direccion == "anada":
                return extremos[0]
            if direccion == "torna":
                return extremos[-1]

    if destinos:
        return destinos[0]

    return ""

def obtener_lineas_de_parada(stop_id):
    """Obtiene las líneas GTFS que pasan por una parada."""
    stop_id = str(stop_id)
    if stop_id in _cache_lineas_parada:
        return _cache_lineas_parada[stop_id]

    if not os.path.exists(RUTA_STOP_TIMES):
        _cache_lineas_parada[stop_id] = set()
        return set()

    info_viajes = obtener_info_lineas()
    lineas = set()

    with open(RUTA_STOP_TIMES, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("stop_id") != stop_id:
                continue

            info = info_viajes.get(row.get("trip_id"))
            if not info:
                continue

            linea = _normalizar_linea(info["linea"])
            if linea.isdigit():
                lineas.add(linea)

    _cache_lineas_parada[stop_id] = lineas
    return lineas

def buscar_parada_cercana(lat, lon):
    """Recorre stops.txt y devuelve el dict de la parada GTFS más cercana
    a (lat, lon), junto con su distancia en metros, o None si stops.txt
    no contiene ninguna fila válida."""
    parada_cercana = None
    distancia_minima = float("inf")

    with open(RUTA_STOPS, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                s_lat = float(row["stop_lat"])
                s_lon = float(row["stop_lon"])
            except (KeyError, ValueError):
                continue

            dist = haversine(lat, lon, s_lat, s_lon)

            if dist < distancia_minima:
                distancia_minima = dist
                parada_cercana = {
                    "stop_id": row["stop_id"],
                    "stop_name": row["stop_name"],
                    "stop_lat": s_lat,
                    "stop_lon": s_lon,
                    "distancia_m": round(dist, 1),
                }

    return parada_cercana
