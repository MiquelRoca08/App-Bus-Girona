from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
import csv
import math
import os

app = FastAPI(title="API Transporte Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIBS_DIR = os.path.join(BASE_DIR, "libs")

RUTA_STOPS = os.path.join(LIBS_DIR, "stops.txt")
RUTA_STOP_TIMES = os.path.join(LIBS_DIR, "stop_times.txt")
RUTA_TRIPS = os.path.join(LIBS_DIR, "trips.txt")
RUTA_ROUTES = os.path.join(LIBS_DIR, "routes.txt")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(d_lam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def obtener_info_lineas():
    rutas = {}
    if os.path.exists(RUTA_ROUTES):
        with open(RUTA_ROUTES, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                rutas[row['route_id']] = row.get('route_short_name') or row.get('route_long_name', 'Bus')

    viajes_a_linea = {}
    if os.path.exists(RUTA_TRIPS):
        with open(RUTA_TRIPS, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                route_id = row['route_id']
                viajes_a_linea[row['trip_id']] = {
                    'linea': rutas.get(route_id, 'Bus'),
                    'destino': row.get('trip_headsign', '')
                }
    return viajes_a_linea


def obtener_proximos_horarios(stop_id, limite=5):
    if not os.path.exists(RUTA_STOP_TIMES):
        return []

    info_viajes = obtener_info_lineas()
    hora_actual = datetime.now().strftime("%H:%M:%S")
    horarios = []

    with open(RUTA_STOP_TIMES, mode='r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['stop_id'] == stop_id:
                hora_paso = row['departure_time']
                
                if hora_paso >= "24:00:00":
                    continue

                if hora_paso >= hora_actual:
                    detalles_viaje = info_viajes.get(row['trip_id'], {'linea': 'Bus', 'destino': ''})
                    horarios.append({
                        'linea': detalles_viaje['linea'],
                        'destino': detalles_viaje['destino'],
                        'hora': hora_paso[:5]
                    })

    horarios.sort(key=lambda x: x['hora'])

    horarios_unicos = []
    vistos = set()
    for h in horarios:
        clave = (h['linea'], h['destino'], h['hora'])
        if clave not in vistos:
            vistos.add(clave)
            horarios_unicos.append(h)

    return horarios_unicos[:limite]


@app.get("/api/proxima-parada")
def proxima_parada(
    lat: float = Query(..., description="Latitud GPS del móvil"),
    lon: float = Query(..., description="Longitud GPS del móvil"),
    radio: float = Query(100.0, description="Radio de búsqueda en metros")
):
    if not os.path.exists(RUTA_STOPS):
        return {"error": f"No se encontró stops.txt en {RUTA_STOPS}"}

    parada_cercana = None
    distancia_minima = float('inf')

    with open(RUTA_STOPS, mode='r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try:
                s_lat, s_lon = float(row['stop_lat']), float(row['stop_lon'])
            except (KeyError, ValueError):
                continue

            dist = haversine(lat, lon, s_lat, s_lon)
            if dist < distancia_minima:
                distancia_minima = dist
                parada_cercana = {
                    'stop_id': row['stop_id'],
                    'stop_name': row['stop_name'],
                    'stop_lat': s_lat,
                    'stop_lon': s_lon,
                    'distancia_m': round(dist, 1)
                }

    if not parada_cercana or parada_cercana['distancia_m'] > radio:
        return {
            "encontrada": False,
            "mensaje": f"No hay paradas a menos de {radio}m",
            "parada_mas_cercana_m": parada_cercana['distancia_m'] if parada_cercana else None
        }

    proximos_buses = obtener_proximos_horarios(parada_cercana['stop_id'])

    return {
        "encontrada": True,
        "parada": parada_cercana,
        "proximos_autobuses": proximos_buses
    }

@app.get("/")
def servir_frontend():
    return FileResponse("index.html")