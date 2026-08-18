# App Bus Girona

Aplicación web para consultar la próxima salida de autobuses urbanos de
Girona utilizando la ubicación GPS del usuario, datos GTFS y la
información de tiempo real proporcionada por TMG.

---

## 1. Descripción general

Girona Bus Tracker permite al usuario conocer qué autobús puede coger
en la parada más cercana a su posición.

El funcionamiento general es:

```
┌──────────────────────┐
│   Ubicación GPS       │
│      usuario          │
└──────────┬────────────┘
           │
           ▼
┌──────────────────────┐
│ Buscar parada GTFS     │
│ más cercana            │
└──────────┬────────────┘
           │
           ▼
┌──────────────────────┐
│ Identificar líneas      │
│ de la parada            │
└──────────┬────────────┘
           │
           ▼
┌──────────────────────┐
│ Consultar TMG            │
│ tiempo real               │
└──────────┬────────────┘
           │
      ┌────┴─────┐
      │          │
      ▼          ▼
  Hay datos   Sin datos
      │          │
      ▼          ▼
    X min       GTFS
                 │
                 ▼
               HH:MM
```

La prioridad es siempre **tiempo real de TMG**. Los horarios GTFS se
utilizan como alternativa cuando TMG no proporciona información.

---

## 2. Arquitectura

El proyecto está dividido en dos partes:

```
┌───────────────────────────────┐
│          Navegador            │
│                               │
│         index.html            │
│                               │
│  GPS + Leaflet + interfaz JS  │
│      (módulos ES6)            │
└──────────────┬────────────────┘
               │ HTTP
               ▼
┌──────────────────────────────┐
│        FastAPI / Uvicorn     │
│                              │
│   main.py + paquete app/     │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌────────────┐   ┌──────────────┐
│    GTFS    │   │     TMG      │
│            │   │ AppBus API   │
│ libs/*.txt │   │              │
└────────────┘   └──────────────┘
```

### 2.1 Backend: `main.py` + `app/`

El backend está modularizado por responsabilidad. `main.py` solo crea
la aplicación FastAPI, registra el middleware CORS, incluye el router
de la API y monta `/static`:

```
main.py
app/
├── config.py           # Rutas de archivos, constantes, timezone, logger
├── utils/
│   └── geo.py            # Distancia Haversine
├── gtfs/
│   ├── loader.py           # Carga y caché de routes.txt / trips.txt
│   ├── paradas.py           # Destinos y líneas por parada, parada más cercana
│   └── horarios.py           # Fallback a horarios programados GTFS
├── tmg/
│   ├── parser.py             # Parseo del HTML/JSON que devuelve AppBus
│   └── cliente.py             # Sesión HTTP + consulta combinada por parada
└── rutas/
    └── api.py                  # Endpoints HTTP (APIRouter)
```

### 2.2 Frontend: `index.html` + `static/js/`

El frontend usa módulos ES6 nativos (`<script type="module">`), sin
bundler ni build step:

```
static/
├── styles.css
└── js/
    ├── main.js           # Punto de entrada: registra listeners y expone
    │                       funciones en window para los onclick del HTML
    ├── utils.js          # escaparHTML
    ├── mapa.js           # Estado y control del minimapa Leaflet
    ├── render.js         # Construcción del HTML de resultados
    └── ubicacion.js      # GPS + fetch al backend
```

Dependencias externas: **Leaflet** (mapa) y la **Geolocation API** del
navegador. No hay `npm`, `package.json` ni proceso de build: los
módulos se sirven tal cual desde `/static/js/`.

---

## 3. Backend en detalle

### 3.1 Obtener ubicación (frontend)

`static/js/ubicacion.js` usa:

```js
navigator.geolocation.getCurrentPosition(callback, errorCallback, {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 0,
});
```

### 3.2 Mapa (frontend)

`static/js/mapa.js` usa Leaflet para mostrar la posición del usuario,
la parada detectada y el mapa de OpenStreetMap. El botón 🎯
(`recentrarUbicacion`) vuelve a centrar el mapa en la posición actual.

### 3.3 API interna

```
GET /api/proxima-parada
```

| Parámetro | Descripción                        |
|-----------|-------------------------------------|
| `lat`     | Latitud del usuario                  |
| `lon`     | Longitud del usuario                  |
| `radio`   | Radio máximo de búsqueda, en metros    |

Ejemplo:

```
/api/proxima-parada?lat=41.97909563627919&lon=2.8179344907402992&radio=100
```

La búsqueda de la parada más cercana usa la distancia **Haversine**
(`app/utils/geo.py`) contra todas las filas de `libs/stops.txt`
(`app/gtfs/paradas.py :: buscar_parada_cercana`), y descarta el
resultado si supera el `radio` indicado.

### 3.4 Sistema GTFS

`app/gtfs/loader.py` carga y cachea en memoria, una sola vez por
proceso, `routes.txt` y `trips.txt`:

```
libs/
├── stops.txt
├── routes.txt
├── trips.txt
├── stop_times.txt
├── calendar.txt
└── ...
```

`stops.txt` contiene, entre otros campos: `stop_id`, `stop_name`,
`stop_lat`, `stop_lon`. Parada usada como referencia en pruebas:

```
15040
Estació d'Autobusos / RENFE
41.9791062170036
2.81791852377473
```

### 3.5 Integración con TMG (AppBus)

`app/tmg/cliente.py` consulta el endpoint interno que usa la web de
AppBus de TMG:

```
https://web2.girona.cat/appbus/cat/busos_json.php
```

Ejemplo real observado:

```
https://web2.girona.cat/appbus/cat/busos_json.php?linia=1&dir=anada&codi=15014&_=1786392261197
```

Parámetros relevantes:

- `linia` — identifica la línea (p. ej. `1`).
- `dir` — sentido de circulación (`anada` o `torna`); se sigue
  consultando internamente para cubrir ambos casos, pero el resultado
  ya **no** se etiqueta ni se muestra en la interfaz (ver sección 1).
- `codi` — identifica la parada (`stop_id`).
- `_` — cache-buster con timestamp; no aporta información.

`app/tmg/parser.py` extrae del HTML embebido en la respuesta JSON
tanto tiempos relativos (`5 min`, `12 minuts`, `5'`) como horas
absolutas (`HH:MM`), soportando pequeñas variaciones de formato.

### 3.6 Prioridad de datos

```
1. TMG tiempo real
       │
       ├── disponible → mostrar X min
       │
       └── no disponible
                 │
                 ▼
2. GTFS
       │
       └── mostrar HH:MM
```

Si TMG falla (timeout, error de red, o devuelve
`"sense informació"`), la aplicación no queda inutilizable: recurre
automáticamente a `app/gtfs/horarios.py`, que calcula los próximos
horarios programados a partir de `stop_times.txt`.

### 3.7 Respuesta del backend

```jsonc
{
  "encontrada": true,
  "parada": {
    "stop_id": "15040",
    "stop_name": "Estació d'Autobusos / RENFE",
    "stop_lat": 41.9791062170036,
    "stop_lon": 2.81791852377473,
    "distancia_m": 0.0
  },
  "proximos_autobuses": [
    {
      "linea": "L2",
      "destino": "Avellaneda",
      "hora": "11:10",
      "minutos": null,
      "fuente": "gtfs",
      "tiempo_real": false
    }
  ],
  "fuente_horarios": "gtfs",
  "tiempo_real_disponible": false
}
```

---

## 4. Ejecución local (sin Docker)

```bash
pip install fastapi "uvicorn[standard]" requests
uvicorn main:app --reload --port 8000
```

La app queda disponible en `http://localhost:8000`. Asegúrate de que
la carpeta `libs/` con los archivos GTFS está presente en la raíz del
proyecto, al mismo nivel que `main.py`.

---

## 5. Despliegue con Docker

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

`docker-compose.yaml` monta `./libs` como volumen
(`./libs:/app/libs`), de modo que los archivos GTFS se pueden
actualizar sin reconstruir la imagen. La variable de entorno
`TMG_DEBUG=1` activa logs detallados de cada consulta a TMG
(`logger.info` en `app/tmg/cliente.py`).

| Variable    | Descripción                                  | Por defecto      |
|-------------|-----------------------------------------------|------------------|
| `TMG_DEBUG` | Activa logs detallados de las consultas a TMG   | `0` (desactivado) |
| `TZ`        | Zona horaria del contenedor                      | —                 |

---

## 6. Estado del proyecto

| Componente                                | Estado             |
|-------------------------------------------|--------------------|
| GPS                                       | ✅ Funciona        |
| Leaflet                                   | ✅ Funciona        |
| Backend FastAPI (modularizado)            | ✅ Funciona        |
| `/api/proxima-parada`                     | ✅ Funciona        |
| Docker                                    | ✅ Funciona        |
| GTFS                                      | ✅ Funciona        |
| API TMG                                   | ✅ Funciona        |
| Tiempo real (X min)                       | ✅ Funciona        |
| Fallback HH:MM                            | ✅ Funciona        |
| Control de frecuencia de peticiones GPS   | ⚠️ Pendiente       |
| Comparación de retraso GTFS/TMG           | ⏳ Futuro          |

---

## 7. Notas conocidas / mejoras futuras

- **Peticiones GPS excesivas**: el frontend puede lanzar muchas
  consultas al backend mientras el usuario se desplaza, incluso con
  coordenadas repetidas. Mejora prevista: separar la actualización de
  GPS (frecuente) de la consulta de autobuses (solo si el usuario se
  ha desplazado lo suficiente, p. ej. 50 m / 10 s de cooldown).
- **Mostrar horario oficial (PDF / web)** además del calculado.
- **Radio de detección y número de paradas configurables** por el
  usuario.
- **Buscador de paradas.**
- **Colores de línea** (assets).
- **Mapa general de todas las líneas.**
- **Click en una parada del mapa** para ver sus horarios directamente.
- **Comparar GTFS vs TMG** para detectar y mostrar retrasos
  (`08:10 → 08:13, +3 min`).

Estas features requieren backend (parsing GTFS más extenso, más
paradas/ciudades, caché), por lo que la arquitectura actual
(Python/FastAPI en el servidor + JS en el navegador) se mantiene: no
está prevista una migración completa a JavaScript.

---

## 8. Reglas de negocio a conservar

```
¿Parada encontrada?
                           │
                    ┌──────┴──────┐
                    │             │
                   NO            SÍ
                    │             │
                 error       buscar líneas
                                  │
                                  ▼
                         consultar TMG
                                  │
                           ┌──────┴──────┐
                           │             │
                      información    sin información
                           │             │
                           ▼             ▼
                         X min          GTFS
                                         │
                                         ▼
                                       HH:MM
```

**En una frase:** Girona Bus Tracker detecta la parada más cercana
mediante GTFS y utiliza la API interna de AppBus de TMG para mostrar
el tiempo real en minutos; cuando TMG no proporciona datos, recurre a
los horarios programados GTFS en formato HH:MM.