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

# Versión de la aplicación: preferir variable de entorno, luego `.env`, luego archivo `VERSION`.
VERSION = os.environ.get("VERSION")

if not VERSION:
	# intentar leer .env en la raíz del proyecto (soporte para despliegues que solo usan .env)
	try:
		DOTENV_FILE = os.path.join(BASE_DIR, ".env")
		if os.path.exists(DOTENV_FILE):
			with open(DOTENV_FILE, mode="r", encoding="utf-8") as df:
				for line in df:
					line = line.strip()
					if not line or line.startswith("#"):
						continue
					if "=" in line:
						k, v = line.split("=", 1)
						if k.strip() == "VERSION":
							VERSION = v.strip().strip('"').strip("'")
							break
	except Exception:
		VERSION = None

if not VERSION:
	# fallback al archivo VERSION para compatibilidad
	VERSION = "v0.0.0"
	try:
		VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
		if os.path.exists(VERSION_FILE):
			with open(VERSION_FILE, mode="r", encoding="utf-8") as vf:
				raw = vf.read().strip()
				if raw:
					VERSION = raw
	except Exception:
		# dejar el valor por defecto si hay cualquier problema
		pass

# Endpoint utilizado por la aplicación AppBus de TMG.
TMG_REALTIME_URL = "https://web2.girona.cat/appbus/cat/busos_json.php"
TMG_TIMEOUT = 8
TMG_DEBUG = os.getenv("TMG_DEBUG", "0") == "1"

logger = logging.getLogger("girona_bus_tracker")
