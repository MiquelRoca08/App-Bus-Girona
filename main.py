import os

from fastapi import FastAPI
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

app.include_router(router)

# Servir archivos estáticos (CSS, JS, assets) desde /static/
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
