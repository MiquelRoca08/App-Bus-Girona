from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from html.parser import HTMLParser
import csv
import html
import logging
import math
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from zoneinfo import ZoneInfo
import requests

TZ_MADRID = ZoneInfo("Europe/Madrid")

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

# Endpoint utilizado por la aplicación AppBus de TMG.
TMG_REALTIME_URL = "https://web2.girona.cat/appbus/cat/busos_json.php"
TMG_TIMEOUT = 8
TMG_DEBUG = os.getenv("TMG_DEBUG", "0") == "1"

logger = logging.getLogger("girona_bus_tracker")


# ---------------------------------------------------------------------------
# GTFS
# ---------------------------------------------------------------------------

_cache_info_viajes = None
_cache_rutas = None
_cache_destinos_parada = None
_cache_lineas_parada = {}


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


# ---------------------------------------------------------------------------
# Distancias
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Parser de AppBus / TMG
# ---------------------------------------------------------------------------

class _TextoHTMLParser(HTMLParser):
    """Extrae únicamente texto visible de un fragmento HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self._ocultar = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self._ocultar += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self._ocultar:
            self._ocultar -= 1

    def handle_data(self, data):
        if not self._ocultar and data.strip():
            self.partes.append(data)


def _extraer_texto_contingut(contingut):
    """Convierte el HTML de 'contingut' a texto visible de forma segura."""
    if not contingut:
        return ""

    texto = html.unescape(str(contingut))
    parser = _TextoHTMLParser()

    try:
        parser.feed(texto)
        texto = " ".join(parser.partes)
    except Exception:
        # Fallback para HTML incompleto.
        texto = re.sub(r"<[^>]+>", " ", texto)

    return re.sub(r"\s+", " ", texto).strip()


def _extraer_contingut(payload):
    """Obtiene contingut incluso si AppBus cambia ligeramente la envoltura."""
    if isinstance(payload, dict):
        for clave in ("contingut", "contenido", "content", "html", "result"):
            valor = payload.get(clave)
            if isinstance(valor, str):
                return valor

        # Algunas respuestas podrían envolver el resultado en otro objeto.
        for valor in payload.values():
            if isinstance(valor, dict):
                resultado = _extraer_contingut(valor)
                if resultado:
                    return resultado

    elif isinstance(payload, str):
        return payload

    return ""


def _parsear_contingut_tmg(payload):
    """Extrae llegadas de AppBus.

    Admite:
      - '5 min', '12 minuts', etc.
      - '5m' / '5 min.'
      - '5\'' como abreviatura de minutos
      - horas absolutas HH:MM

    Devuelve una lista ordenada y sin duplicados.
    """
    contingut = _extraer_contingut(payload)
    texto = _extraer_texto_contingut(contingut)

    if not texto:
        return []

    texto_lower = texto.lower()
    if "sense informaci" in texto_lower or "sin información" in texto_lower:
        return []

    resultados = []

    # Tiempos relativos.
    patrones_minutos = [
        r"(?<!\d)(\d{1,3})\s*(?:min|mins|minut|minuts)\.?\b",
        r"(?<!\d)(\d{1,3})\s*m\b",
        r"(?<!\d)(\d{1,3})\s*[′']\b",
    ]

    for patron in patrones_minutos:
        for match in re.finditer(patron, texto, re.I):
            minutos = int(match.group(1))
            if minutos > 240:
                continue

            llegada = datetime.now(TZ_MADRID) + timedelta(minutes=minutos)
            resultados.append({
                "minutos": minutos,
                "hora": llegada.strftime("%H:%M"),
            })

    # Horas absolutas.
    for match in re.finditer(
        r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)",
        texto,
    ):
        hora = f"{int(match.group(1)):02d}:{match.group(2)}"
        resultados.append({
            "minutos": None,
            "hora": hora,
        })

    # Elimina duplicados y ordena por hora/minutos.
    unicos = []
    vistos = set()

    for item in resultados:
        clave = (item["hora"], item["minutos"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(item)

    unicos.sort(
        key=lambda item: (
            item["minutos"] is None,
            item["minutos"] if item["minutos"] is not None else 9999,
            item["hora"],
        )
    )

    return unicos


# ---------------------------------------------------------------------------
# TMG
# ---------------------------------------------------------------------------

TMG_SESSION = requests.Session()
TMG_SESSION.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://web2.girona.cat/appbus/cat/app_index.php",
    "User-Agent": "Mozilla/5.0 (compatible; Girona-Bus-Tracker/1.0)",
    "X-Requested-With": "XMLHttpRequest",
})


def _consultar_tmg(linea, stop_id, direccion):
    """Consulta una dirección de una línea en AppBus."""
    params = {
        "linia": str(linea),
        "dir": direccion,
        "codi": str(stop_id),
        "_": int(datetime.now(TZ_MADRID).timestamp() * 1000),
    }

    try:
        response = TMG_SESSION.get(
            TMG_REALTIME_URL,
            params=params,
            timeout=TMG_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        llegadas = _parsear_contingut_tmg(payload)

        if TMG_DEBUG:
            logger.info(
                "TMG %s %s/%s -> %d llegadas | payload=%s",
                stop_id,
                linea,
                direccion,
                len(llegadas),
                str(payload)[:1000],
            )

        return direccion, llegadas

    except (requests.RequestException, ValueError, TypeError) as exc:
        if TMG_DEBUG:
            logger.warning(
                "Error TMG %s %s/%s: %s",
                stop_id,
                linea,
                direccion,
                exc,
            )
        return direccion, []


def obtener_horarios_tiempo_real(stop_id, limite=5):
    """Obtiene próximos buses desde AppBus."""
    lineas = obtener_lineas_de_parada(stop_id)

    if not lineas:
        return []

    consultas = [
        (linea, direccion)
        for linea in sorted(lineas, key=lambda x: int(x))
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

            destino = obtener_destino_por_direccion(
                linea,
                dir_resultado,
                stop_id,
            )

            for llegada in llegadas:
                resultados.append({
                    "linea": f"L{linea}",
                    "destino": destino,
                    "hora": llegada["hora"],
                    "minutos": llegada["minutos"],
                    "fuente": "tmg_tiempo_real",
                    "tiempo_real": True,
                })

    resultados.sort(
        key=lambda item: (
            item["minutos"] is None,
            item["minutos"] if item["minutos"] is not None else 9999,
            item["hora"],
            item["linea"],
        )
    )

    unicos = []
    vistos = set()

    for item in resultados:
        clave = (
            item["linea"],
            item["hora"],
            item["minutos"],
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        unicos.append(item)

    return unicos[:limite]


# ---------------------------------------------------------------------------
# GTFS fallback
# ---------------------------------------------------------------------------


def obtener_proximos_horarios(stop_id, limite=5):
    """Fallback a horarios GTFS si AppBus no proporciona datos."""
    if not os.path.exists(RUTA_STOP_TIMES):
        return []

    info_viajes = obtener_info_lineas()
    ahora = datetime.now(TZ_MADRID)
    hora_actual = ahora.strftime("%H:%M:%S")
    horarios = []

    with open(RUTA_STOP_TIMES, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("stop_id") != str(stop_id):
                continue

            hora_paso = row.get("departure_time", "")
            if not hora_paso or hora_paso >= "24:00:00":
                continue

            if hora_paso >= hora_actual:
                detalles_viaje = info_viajes.get(
                    row.get("trip_id"),
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


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/proxima-parada")
def proxima_parada(
    lat: float = Query(..., description="Latitud GPS del móvil"),
    lon: float = Query(..., description="Longitud GPS del móvil"),
    radio: float = Query(100.0, description="Radio de búsqueda en metros"),
):
    if not os.path.exists(RUTA_STOPS):
        return {"error": f"No se encontró stops.txt en {RUTA_STOPS}"}

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

    if not parada_cercana or parada_cercana["distancia_m"] > radio:
        return {
            "encontrada": False,
            "mensaje": f"No hay paradas a menos de {radio}m",
            "parada_mas_cercana_m": (
                parada_cercana["distancia_m"] if parada_cercana else None
            ),
        }

    # 1. Intentar tiempo real TMG.
    tiempo_real = obtener_horarios_tiempo_real(
        parada_cercana["stop_id"],
        limite=5,
    )

    # 2. Siempre calculamos GTFS como fallback.
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
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# Servir archivos estáticos (CSS, JS, assets) desde /static/
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
