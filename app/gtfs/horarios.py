"""Horarios GTFS programados: fallback cuando TMG no da tiempo real."""

import csv
import os
from datetime import datetime

from app.config import RUTA_STOP_TIMES, TZ_MADRID
from app.gtfs.loader import obtener_info_lineas


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
