"""Endpoints HTTP: búsqueda de la próxima parada y frontend."""

import os
import logging

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.config import BASE_DIR, RUTA_STOPS, VERSION
from app.gtfs.horarios import obtener_proximos_horarios
from app.gtfs.paradas import buscar_paradas_cercanas
from app.gtfs.loader import cargar_gtfs
from app.tmg.cliente import obtener_horarios_tiempo_real

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/proxima-parada")
def proxima_parada(
    lat: float = Query(..., description="Latitud GPS del móvil"),
    lon: float = Query(..., description="Longitud GPS del móvil"),
    radio: float = Query(100.0, description="Radio de búsqueda en metros"),
    max_paradas: int = Query(
        1, ge=1, le=20, description="Número máximo de paradas a devolver"
    ),
):
    logger.info(
        "/api/proxima-parada called: lat=%s lon=%s radio=%s max_paradas=%s",
        lat,
        lon,
        radio,
        max_paradas,
    )

    if not os.path.exists(RUTA_STOPS):
        return {"error": f"No se encontró stops.txt en {RUTA_STOPS}"}

    paradas_cercanas = buscar_paradas_cercanas(lat, lon, radio, max_paradas)

    if not paradas_cercanas:
        return {
            "encontrada": False,
            "mensaje": f"No hay paradas a menos de {radio}m",
            "paradas": [],
        }

    resultado_paradas = []

    for parada in paradas_cercanas:
        # 1. Intentar tiempo real TMG.
        tiempo_real = obtener_horarios_tiempo_real(
            parada["stop_id"],
            limite=5,
        )

        # 2. Siempre calculamos GTFS como fallback.
        programados = obtener_proximos_horarios(
            parada["stop_id"],
            limite=5,
        )

        if tiempo_real:
            proximos_buses = tiempo_real
            fuente_horarios = "tmg_tiempo_real"
        else:
            proximos_buses = programados
            fuente_horarios = "gtfs"

        resultado_paradas.append({
            "parada": parada,
            "proximos_autobuses": proximos_buses,
            "fuente_horarios": fuente_horarios,
            "tiempo_real_disponible": bool(tiempo_real),
        })

    return {
        "encontrada": True,
        "paradas": resultado_paradas,
    }


@router.get("/")
def servir_frontend():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@router.get("/api/about")
def about():
    """Devuelve información sencilla sobre la aplicación."""
    # Contar paradas
    num_paradas = 0
    if os.path.exists(RUTA_STOPS):
        try:
            with open(RUTA_STOPS, mode="r", encoding="utf-8-sig") as f:
                for _ in f:
                    num_paradas += 1
            # Substraer la cabecera si existe
            if num_paradas > 0:
                num_paradas -= 1
        except Exception:
            num_paradas = 0

    # Cargar rutas GTFS
    _, rutas = cargar_gtfs()
    num_rutas = len(rutas) if rutas else 0

    return {
        "version": VERSION,
        "num_paradas": num_paradas,
        "num_rutas": num_rutas,
    }
