# Girona Bus Tracker

Aplicación simple para encontrar la parada de autobús más cercana en Girona y mostrar los próximos horarios desde datos GTFS.

## Descripción

- Proyecto en Python usando FastAPI.
- Busca la parada más cercana según latitud/longitud del usuario.
- Devuelve el nombre de la parada, distancia y próximos autobuses.
- Incluye una interfaz web ligera con Leaflet para mostrar la parada y la ubicación del usuario.

https://hub.docker.com/repository/docker/miquelroca08/app-bus-girona

## Estructura del proyecto

- `main.py` - servidor FastAPI con endpoints API y frontend.
- `index.html` - interfaz web para móvil/desktop.
- `libs/` - datos GTFS usados para calcular paradas y horarios.
- `Dockerfile` - imagen Docker para ejecutar la app.
- `docker-compose.yaml` - configuración para ejecutar con Docker Compose.
- `buscar_parada.py` - script auxiliar para buscar la parada más cercana desde línea de comandos.

## Requisitos

- Python 3.11+
- FastAPI
- Uvicorn

## Instalación local

1. Clonar el repositorio.
2. Crear un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install fastapi uvicorn[standard]
```

4. Ejecutar la aplicación:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Abrir `http://localhost:8000` en el navegador.

## Uso con Docker

Construir y ejecutar con Docker Compose:

```bash
docker compose up --build
```

La aplicación estará disponible en `http://localhost:8000`.

## API

### GET `/api/proxima-parada`

Parámetros de consulta:

- `lat` (float, obligatorio) - latitud.
- `lon` (float, obligatorio) - longitud.
- `radio` (float, opcional) - radio de búsqueda en metros (por defecto `100`).

Ejemplo:

```bash
curl "http://localhost:8000/api/proxima-parada?lat=41.983112&lon=2.824932&radio=100"
```

Respuesta:

- `encontrada`: `true`/`false`
- `parada`: detalles de la parada más cercana
- `proximos_autobuses`: lista de salidas próximas

## Datos GTFS

La carpeta `libs/` debe contener los archivos GTFS necesarios:

- `stops.txt`
- `stop_times.txt`
- `trips.txt`
- `routes.txt`

## Notas

- `index.html` usa la geolocalización del navegador para obtener la ubicación.
- Si no se encuentra el archivo `stops.txt`, la API devuelve un error.
- El proyecto está pensado para ser usado localmente o en Docker con datos GTFS montados.
