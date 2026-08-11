from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import csv
import html
import math
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

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

# Endpoint interno que utiliza la aplicación oficial AppBus de TMG.
TMG_REALTIME_URL = "https://web2.girona.cat/appbus/cat/busos_json.php"
TMG_TIMEOUT = 8

TMG_SESSION = requests.Session()
TMG_SESSION.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://web2.girona.cat/appbus/cat/app_index.php",
    "User-Agent": "Mozilla/5.0 (compatible; Girona-Bus-Tracker/1.0)",
    "X-Requested-With": "XMLHttpRequest",
})


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def obtener_info_lineas():
    rutas = {}
    if os.path.exists(RUTA_ROUTES):
        with open(RUTA_ROUTES, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rutas[row["route_id"]] = (
                    row.get("route_short_name")
                    or row.get("route_long_name", "Bus")
                )

    viajes_a_linea = {}
    if os.path.exists(RUTA_TRIPS):
        with open(RUTA_TRIPS, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                route_id = row["route_id"]
                viajes_a_linea[row["trip_id"]] = {
                    "linea": rutas.get(route_id, "Bus"),
                    "destino": row.get("trip_headsign", ""),
                }
    return viajes_a_linea


def obtener_lineas_de_parada(stop_id):
    """Obtiene las líneas GTFS que pasan por una parada.

    AppBus necesita el número de línea sin la 'L', por ejemplo:
    route_short_name=L1 -> linia=1.
    """
    lineas = set()
    if not os.path.exists(RUTA_STOP_TIMES):
        return lineas

    info_viajes = obtener_info_lineas()

    with open(RUTA_STOP_TIMES, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["stop_id"] != stop_id:
                continue

            info = info_viajes.get(row["trip_id"])
            if not info:
                continue

            linea = str(info["linea"]).strip()
            if linea.startswith("L"):
                linea = linea[1:]

            if linea.isdigit():
                lineas.add(linea)

    return lineas


def _extraer_texto_contingut(contingut):
    """Convierte el HTML contenido en 'contingut' a texto visible."""
    texto = html.unescape(contingut or "")
    texto = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        texto,
        flags=re.I | re.S,
    )
    texto = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        texto,
        flags=re.I | re.S,
    )
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _parsear_contingut_tmg(payload):
    """Extrae tiempos de llegada del JSON de AppBus.

    AppBus devuelve JSON, pero el campo 'contingut' contiene HTML.
    Se aceptan tanto tiempos relativos ('5 min') como horas ('21:42').
    """
    if not isinstance(payload, dict):
        return []

    texto = _extraer_texto_contingut(payload.get("contingut", ""))

    if not texto or "sense informaci" in texto.lower():
        return []

    resultados = []

    # Tiempos relativos: "5 min", "12 minuts", etc.
    for match in re.finditer(
        r"(?<!\d)(\d{1,3})\s*(?:min|mins|minut|minuts)\b",
        texto,
        re.I,
    ):
        minutos = int(match.group(1))
        if minutos > 240:
            continue

        llegada = datetime.now() + timedelta(minutes=minutos)
        resultados.append({
            "minutos": minutos,
            "hora": llegada.strftime("%H:%M"),
        })

    # Horas absolutas, por si una versión de AppBus las devuelve.
    for match in re.finditer(
        r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)",
        texto,
    ):
        hora = f"{int(match.group(1)):02d}:{match.group(2)}"
        if not any(item["hora"] == hora for item in resultados):
            resultados.append({
                "minutos": None,
                "hora": hora,
            })

    unicos = []
    vistos = set()

    for item in resultados:
        clave = (item["hora"], item["minutos"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(item)

    return unicos


def _consultar_tmg(linea, stop_id, direccion):
    """Consulta una dirección de una línea en AppBus."""
    params = {
        "linia": str(linea),
        "dir": direccion,
        "codi": str(stop_id),
        # El frontend oficial utiliza este parámetro como cache-buster.
        "_": int(datetime.now().timestamp() * 1000),
    }

    try:
        response = TMG_SESSION.get(
            TMG_REALTIME_URL,
            params=params,
            timeout=TMG_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        return direccion, _parsear_contingut_tmg(payload)

    except (requests.RequestException, ValueError, TypeError):
        return direccion, []


def obtener_horarios_tiempo_real(stop_id, limite=5):
    """Obtiene próximos buses desde AppBus.

    Se consultan las dos direcciones ('anada' y 'torna') para cada
    línea que el GTFS local identifica en la parada.
    """
    lineas = obtener_lineas_de_parada(stop_id)

    if not lineas:
        return []

    consultas = [
        (linea, direccion)
        for linea in sorted(lineas, key=int)
        for direccion in ("anada", "torna")
    ]

    resultados = []

    with ThreadPoolExecutor(max_workers=min(6, len(consultas))) as executor:
        futures = {
            executor.submit(
                _consultar_tmg,
                linea,
                stop_id,
                direccion,
            ): (linea, direccion)
            for linea, direccion in consultas
        }

        for future in as_completed(futures):
            linea, direccion = futures[future]

            try:
                dir_resultado, llegadas = future.result()
            except Exception:
                continue

            for llegada in llegadas:
                resultados.append({
                    "linea": f"L{linea}",
                    "destino": "",
                    "hora": llegada["hora"],
                    "minutos": llegada["minutos"],
                    "fuente": "tmg_tiempo_real",
                    "tiempo_real": True,
                    "direccion": dir_resultado,
                })

    resultados.sort(
        key=lambda item: (
            item["hora"],
            item["minutos"] if item["minutos"] is not None else 999,
            item["linea"],
        )
    )

    unicos = []
    vistos = set()

    for item in resultados:
        clave = (
            item["linea"],
            item["direccion"],
            item["hora"],
            item["minutos"],
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        unicos.append(item)

    return unicos[:limite]


def obtener_proximos_horarios(stop_id, limite=5):
    """Fallback a horarios GTFS si AppBus no proporciona datos."""
    if not os.path.exists(RUTA_STOP_TIMES):
        return []

    info_viajes = obtener_info_lineas()
    hora_actual = datetime.now().strftime("%H:%M:%S")
    horarios = []

    with open(RUTA_STOP_TIMES, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["stop_id"] != stop_id:
                continue

            hora_paso = row["departure_time"]

            if hora_paso >= "24:00:00":
                continue

            if hora_paso >= hora_actual:
                detalles_viaje = info_viajes.get(
                    row["trip_id"],
                    {"linea": "Bus", "destino": ""},
                )

                horarios.append({
                    "linea": detalles_viaje["linea"],
                    "destino": detalles_viaje["destino"],
                    "hora": hora_paso[:5],
                    "minutos": None,
                    "fuente": "gtfs",
                    "tiempo_real": False,
                })

    horarios.sort(key=lambda item: item["hora"])

    horarios_unicos = []
    vistos = set()

    for horario in horarios:
        clave = (
            horario["linea"],
            horario["destino"],
            horario["hora"],
        )

        if clave not in vistos:
            vistos.add(clave)
            horarios_unicos.append(horario)

    return horarios_unicos[:limite]


@app.get("/api/proxima-parada")
def proxima_parada(
    lat: float = Query(..., description="Latitud GPS del móvil"),
    lon: float = Query(..., description="Longitud GPS del móvil"),
    radio: float = Query(
        100.0,
        description="Radio de búsqueda en metros",
    ),
):
    if not os.path.exists(RUTA_STOPS):
        return {
            "error": f"No se encontró stops.txt en {RUTA_STOPS}"
        }

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

    if (
        not parada_cercana
        or parada_cercana["distancia_m"] > radio
    ):
        return {
            "encontrada": False,
            "mensaje": f"No hay paradas a menos de {radio}m",
            "parada_mas_cercana_m": (
                parada_cercana["distancia_m"]
                if parada_cercana
                else None
            ),
        }

    # Primero intentamos datos reales.
    tiempo_real = obtener_horarios_tiempo_real(
        parada_cercana["stop_id"],
        limite=5,
    )

    # Si AppBus no responde o no tiene información, mantenemos
    # exactamente el comportamiento anterior basado en GTFS.
    programados = obtener_proximos_horarios(
        parada_cercana["stop_id"],
        limite=5,
    )

    if tiempo_real:
        proximos_buses = tiempo_real
        fuente_horarios = "tmg_tiempo_real"
    else:
        proximos_buses = programados
        fuente_horarios = "gtfs"

    return {
        "encontrada": True,
        "parada": parada_cercana,
        "proximos_autobuses": proximos_buses,
        "fuente_horarios": fuente_horarios,
        "tiempo_real_disponible": bool(tiempo_real),
    }


@app.get("/")
def servir_frontend():
    return FileResponse("index.html")
