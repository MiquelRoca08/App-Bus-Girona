import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import BASE_DIR
from app.rutas.api import router

app = FastAPI(title="API Transporte Local")

# El frontend se sirve desde el mismo dominio, así que CORS solo hace falta
# para el dominio público (y localhost en desarrollo). Ninguna web de
# terceros necesita leer esta API desde el navegador de un visitante.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bus.rocanode.com", "http://localhost:8000"],
    allow_methods=["GET"],
    allow_headers=[],
)

# Límite por IP para /api/: cada consulta de horarios llama a la API de TMG,
# así que sin límite cualquiera puede generar carga sostenida. El frontend
# refresca cada 60 s y el mapa pide horarios al tocar paradas: 120/min deja
# margen de sobra a varios usuarios detrás de la misma IP (wifi de la UdG).
RATE_LIMIT = 120
RATE_WINDOW = 60
_hits: dict[str, tuple[float, int]] = {}


@app.middleware("http")
async def rate_limit_api(request: Request, call_next):
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    # Detrás de Cloudflare Tunnel request.client es el túnel, compartido por
    # todos; la IP real viene en CF-Connecting-IP (que Cloudflare sobrescribe).
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")
    now = time.monotonic()
    start, count = _hits.get(ip, (now, 0))
    if now - start >= RATE_WINDOW:
        start, count = now, 0
    if count >= RATE_LIMIT:
        retry = int(RATE_WINDOW - (now - start)) + 1
        return JSONResponse({"detail": "Demasiadas peticiones"}, status_code=429, headers={"Retry-After": str(retry)})
    _hits[ip] = (start, count + 1)
    if len(_hits) > 10000:  # purga ventanas caducadas para acotar memoria
        for k in [k for k, (s, _) in _hits.items() if now - s >= RATE_WINDOW]:
            del _hits[k]
    return await call_next(request)


@app.middleware("http")
async def no_cache_frontend(request: Request, call_next):
    """
    Evita que el navegador (o una PWA instalada) se quede sirviendo
    versiones viejas de index.html / JS / CSS después de un deploy.

    En vez de dejar que el navegador decida cuánto tiempo cachear estos
    ficheros (comportamiento por defecto de StaticFiles/FileResponse),
    obligamos a que SIEMPRE revalide con el servidor antes de usar la
    copia en caché. Como el servidor sigue enviando ETag/Last-Modified,
    si el fichero no ha cambiado la revalidación es una respuesta 304
    barata; si ha cambiado, el navegador se descarga la versión nueva.
    """
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


app.include_router(router)

# Servir archivos estáticos (CSS, JS, assets) desde /static/
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
