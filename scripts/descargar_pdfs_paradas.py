#!/usr/bin/env python3
"""
Descarga automáticamente el PDF de horarios de cada parada de Girona Bus.

Para cada stop_id de libs/stops.txt:
  1. Se calculan (a partir de trips.txt + routes.txt + stop_times.txt) las
     líneas GTFS que pasan por esa parada.
  2. Para cada línea, se consulta:
       https://umat.girona.cat/apps/bus/cerca_pdf/parada/<stop_id>_L<linea>
     Ese endpoint hace un redirect a la URL final del PDF (o falla si no
     existe combinación parada+línea).
  3. Se guarda el PRIMER PDF que responda con éxito como:
       pdfs/<stop_id>.pdf
     y se pasa a la siguiente parada (una parada = un único PDF).

Uso:
    python3 scripts/descargar_pdfs_paradas.py
    python3 scripts/descargar_pdfs_paradas.py --forzar        # re-descarga aunque ya exista el PDF
    python3 scripts/descargar_pdfs_paradas.py --stops 15040 15041
    python3 scripts/descargar_pdfs_paradas.py --libs-dir /ruta/a/libs --pdfs-dir /ruta/a/pdfs

Solo depende de la librería `requests`:
    pip install requests
"""

import argparse
import csv
import os
import sys
import time

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

DEFAULT_LIBS_DIR = os.path.join(PROJECT_DIR, "libs")
DEFAULT_PDFS_DIR = os.path.join(PROJECT_DIR, "pdfs")

URL_TEMPLATE = "https://umat.girona.cat/apps/bus/cerca_pdf/parada/{stop_id}_L{linea}"
TIMEOUT = 15
PAUSA_ENTRE_PETICIONES = 0.3  # segundos, para no machacar el servidor


def normalizar_linea(linea):
    """Quita una posible 'L' inicial de route_short_name (route_short_name
    ya suele venir como 'L1', 'L12', etc. en routes.txt)."""
    linea = str(linea or "").strip()
    if linea.upper().startswith("L"):
        linea = linea[1:]
    return linea


def cargar_rutas(libs_dir):
    """route_id -> línea normalizada (sin 'L'), ej. 'L12' -> '12'."""
    ruta_routes = os.path.join(libs_dir, "routes.txt")
    rutas = {}
    with open(ruta_routes, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            linea = row.get("route_short_name") or row.get("route_long_name", "")
            rutas[row["route_id"]] = normalizar_linea(linea)
    return rutas


def cargar_trip_a_linea(libs_dir, rutas):
    """trip_id -> línea normalizada."""
    ruta_trips = os.path.join(libs_dir, "trips.txt")
    trip_a_linea = {}
    with open(ruta_trips, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            route_id = row.get("route_id")
            trip_a_linea[row["trip_id"]] = rutas.get(route_id, "")
    return trip_a_linea


def cargar_lineas_por_parada(libs_dir):
    """stop_id -> set de líneas normalizadas que pasan por esa parada,
    calculado recorriendo stop_times.txt una sola vez."""
    rutas = cargar_rutas(libs_dir)
    trip_a_linea = cargar_trip_a_linea(libs_dir, rutas)

    ruta_stop_times = os.path.join(libs_dir, "stop_times.txt")
    lineas_por_parada = {}

    with open(ruta_stop_times, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            stop_id = row.get("stop_id")
            linea = trip_a_linea.get(row.get("trip_id"), "")

            if not stop_id or not linea:
                continue

            lineas_por_parada.setdefault(stop_id, set()).add(linea)

    return lineas_por_parada


def cargar_stop_ids(libs_dir):
    ruta_stops = os.path.join(libs_dir, "stops.txt")
    stop_ids = []
    with open(ruta_stops, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            stop_id = row.get("stop_id")
            if stop_id:
                stop_ids.append(stop_id)
    return stop_ids


def descargar_pdf_parada(stop_id, lineas, pdfs_dir, sesion, debug=False):
    """Prueba cada línea de la parada contra el endpoint de umat.girona.cat
    y guarda el primer PDF que responda con éxito como pdfs/<stop_id>.pdf.

    Devuelve una tupla (ok: bool, detalle: str) para poder resumir al final.
    """
    if not lineas:
        return False, "sin líneas GTFS conocidas para esta parada"

    # Orden estable y "humano" (numérico si es posible).
    def clave_orden(linea):
        return (0, int(linea)) if linea.isdigit() else (1, linea)

    lineas_ordenadas = sorted(lineas, key=clave_orden)

    for linea in lineas_ordenadas:
        url = URL_TEMPLATE.format(stop_id=stop_id, linea=linea)

        try:
            respuesta = sesion.get(url, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException as e:
            print(f"    L{linea}: error de red ({e})")
            continue

        content_type = respuesta.headers.get("Content-Type", "")

        if respuesta.status_code == 200 and "pdf" in content_type.lower():
            destino = os.path.join(pdfs_dir, f"{stop_id}.pdf")
            with open(destino, "wb") as f:
                f.write(respuesta.content)
            return True, f"L{linea} -> {respuesta.url} ({len(respuesta.content)} bytes)"

        print(
            f"    L{linea}: sin PDF válido "
            f"(status={respuesta.status_code}, content-type={content_type or 'desconocido'})"
        )

        if debug:
            print(f"      URL solicitada: {url}")
            print(f"      URL final tras redirects: {respuesta.url}")
            print(f"      Headers: {dict(respuesta.headers)}")
            cuerpo = respuesta.content[:300]
            print(f"      Primeros bytes del cuerpo: {cuerpo!r}")

    return False, "ninguna línea devolvió un PDF válido"


def main():
    parser = argparse.ArgumentParser(
        description="Descarga el PDF de horarios de cada parada de Girona Bus."
    )
    parser.add_argument(
        "--libs-dir",
        default=DEFAULT_LIBS_DIR,
        help=f"Carpeta con los ficheros GTFS (por defecto: {DEFAULT_LIBS_DIR})",
    )
    parser.add_argument(
        "--pdfs-dir",
        default=DEFAULT_PDFS_DIR,
        help=f"Carpeta donde guardar los PDFs (por defecto: {DEFAULT_PDFS_DIR})",
    )
    parser.add_argument(
        "--stops",
        nargs="+",
        default=None,
        help="Procesar solo estos stop_id (por defecto: todas las paradas de stops.txt)",
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Re-descargar aunque ya exista pdfs/<stop_id>.pdf",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mostrar detalle (headers, URL final, cuerpo) de cada intento fallido",
    )
    args = parser.parse_args()

    os.makedirs(args.pdfs_dir, exist_ok=True)

    print(f"Cargando GTFS desde: {args.libs_dir}")
    lineas_por_parada = cargar_lineas_por_parada(args.libs_dir)
    todos_los_stop_ids = cargar_stop_ids(args.libs_dir)

    stop_ids = args.stops if args.stops else todos_los_stop_ids
    print(f"Paradas a procesar: {len(stop_ids)}")

    ok_count = 0
    saltadas_count = 0
    fallidas = []

    with requests.Session() as sesion:
        sesion.headers.update({"User-Agent": "GironaBusTracker-DescargaPDFs/1.0"})

        for i, stop_id in enumerate(stop_ids, start=1):
            destino = os.path.join(args.pdfs_dir, f"{stop_id}.pdf")

            if os.path.exists(destino) and not args.forzar:
                print(f"[{i}/{len(stop_ids)}] {stop_id}: ya existe, se omite (usa --forzar para re-descargar)")
                saltadas_count += 1
                continue

            lineas = lineas_por_parada.get(stop_id, set())
            print(f"[{i}/{len(stop_ids)}] {stop_id}: probando líneas {sorted(lineas) or '(ninguna)'}")

            ok, detalle = descargar_pdf_parada(stop_id, lineas, args.pdfs_dir, sesion, debug=args.debug)

            if ok:
                print(f"    ✔ guardado: {detalle}")
                ok_count += 1
            else:
                print(f"    ✘ sin PDF: {detalle}")
                fallidas.append(stop_id)

            time.sleep(PAUSA_ENTRE_PETICIONES)

    print("\n" + "=" * 60)
    print(f"Completado. PDFs descargados: {ok_count}")
    print(f"Paradas omitidas (ya tenían PDF): {saltadas_count}")
    print(f"Paradas sin PDF encontrado: {len(fallidas)}")
    if fallidas:
        print("Stop_ids sin PDF:", ", ".join(fallidas))

    return 0


if __name__ == "__main__":
    sys.exit(main())
