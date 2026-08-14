import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import BASE_DIR
from app.rutas.api import router

app = FastAPI(title="API Transporte Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
