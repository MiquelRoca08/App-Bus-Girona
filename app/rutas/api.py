"""Endpoints HTTP: búsqueda de la próxima parada y frontend."""

import os

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.config import BASE_DIR, RUTA_STOPS
from app.gtfs.horarios import obtener_proximos_horarios
from app.gtfs.paradas import buscar_parada_cercana
from app.tmg.cliente import obtener_horarios_tiempo_real

router = APIRouter()


@router.get("/api/proxima-parada")
def proxima_parada(
    lat: float = Query(..., description="Latitud GPS del móvil"),
    lon: float = Query(..., description="Longitud GPS del móvil"),
    radio: float = Query(100.0, description="Radio de búsqueda en metros"),
):
    if not os.path.exists(RUTA_STOPS):
        return {"error": f"No se encontró stops.txt en {RUTA_STOPS}"}

    parada_cercana = buscar_parada_cercana(lat, lon)

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


@router.get("/")
def servir_frontend():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))
