"""Carga y caché de los datos estáticos GTFS (routes.txt, trips.txt)."""

import csv
import os

from app.config import RUTA_ROUTES, RUTA_TRIPS


_cache_info_viajes = None
_cache_rutas = None


def cargar_gtfs():
    """Carga la información estática GTFS una sola vez por proceso."""
    global _cache_info_viajes, _cache_rutas

    if _cache_info_viajes is not None:
        return _cache_info_viajes, _cache_rutas

    rutas = {}
    if os.path.exists(RUTA_ROUTES):
        with open(RUTA_ROUTES, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rutas[row["route_id"]] = {
                    "linea": row.get("route_short_name") or row.get("route_long_name", "Bus"),
                    "nombre": row.get("route_long_name", ""),
                }

    viajes_a_linea = {}
    if os.path.exists(RUTA_TRIPS):
        with open(RUTA_TRIPS, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                route_id = row["route_id"]
                ruta = rutas.get(route_id, {})
                viajes_a_linea[row["trip_id"]] = {
                    "route_id": route_id,
                    "linea": ruta.get("linea", "Bus"),
                    "route_long_name": ruta.get("nombre", ""),
                    "destino": (row.get("trip_headsign") or "").strip(),
                }

    _cache_info_viajes = viajes_a_linea
    _cache_rutas = rutas
    return viajes_a_linea, rutas


def obtener_info_lineas():
    return cargar_gtfs()[0]


def _normalizar_linea(linea):
    linea = str(linea or "").strip()
    if linea.upper().startswith("L"):
        linea = linea[1:]
    return linea
