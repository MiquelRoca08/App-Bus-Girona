"""Cliente HTTP contra AppBus/TMG: consulta por línea+dirección y
combina los resultados de todas las líneas de una parada."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

from app.config import TMG_DEBUG, TMG_REALTIME_URL, TMG_TIMEOUT, TZ_MADRID, logger
from app.gtfs.paradas import obtener_destino_por_direccion, obtener_lineas_de_parada
from app.tmg.parser import _parsear_contingut_tmg


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
