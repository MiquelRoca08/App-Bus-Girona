"""Configuración centralizada del proyecto: rutas, constantes y logger."""

import logging
import os
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS_DIR = os.path.join(BASE_DIR, "libs")
RUTA_STOPS = os.path.join(LIBS_DIR, "stops.txt")
RUTA_STOP_TIMES = os.path.join(LIBS_DIR, "stop_times.txt")
RUTA_TRIPS = os.path.join(LIBS_DIR, "trips.txt")
RUTA_ROUTES = os.path.join(LIBS_DIR, "routes.txt")

# Versión de la aplicación
VERSION = "v0.1.0"

# Endpoint utilizado por la aplicación AppBus de TMG.
TMG_REALTIME_URL = "https://web2.girona.cat/appbus/cat/busos_json.php"
TMG_TIMEOUT = 8
TMG_DEBUG = os.getenv("TMG_DEBUG", "0") == "1"

logger = logging.getLogger("girona_bus_tracker")
