# Girona Bus Tracker

Aplicación web para localizar la parada de autobús más cercana en Girona y mostrar los próximos horarios, combinando datos GTFS y información en tiempo real del sistema de la ciudad.

## Descripción general

Girona Bus Tracker es una pequeña app web pensada para móvil y escritorio que:

- obtiene la ubicación del usuario mediante GPS desde el navegador;
- busca la parada más cercana a esa posición;
- consulta qué líneas pasan por esa parada;
- intenta obtener horarios en tiempo real desde el servicio de AppBus de TMG;
- si el servicio en tiempo real no está disponible, usa un fallback con los horarios programados del GTFS;
- muestra todo en un mapa sencillo con Leaflet y una lista de próximos autobuses.

La aplicación está diseñada para ser útil en la práctica diaria: si estás en la calle y quieres saber qué autobús llega antes, solo tienes que permitir el acceso a la ubicación y la app te indica la parada más cercana y los próximos horarios.

## Qué hace exactamente

### 1. Geolocalización
La interfaz web usa la API de geolocalización del navegador para obtener la latitud y la longitud del usuario.

Una vez disponible la ubicación, se envía una petición a la API interna del backend:

- latitud
- longitud
- radio de búsqueda (por defecto 100 metros)

### 2. Búsqueda de la parada más cercana
En el backend, el proyecto lee el fichero GTFS `stops.txt` y calcula la distancia entre la posición del usuario y cada parada disponible usando la fórmula de Haversine.

Se selecciona la parada con mínima distancia dentro del radio configurado.

### 3. Consulta de líneas y destinos
A partir del identificador de la parada, la app revisa los horarios GTFS y deduce qué líneas pasan por esa parada y qué destinos suelen asociarse a cada una.

Esto sirve para poder mapear cada línea con su destino correcto y hacer una respuesta más útil al usuario.

### 4. Horarios en tiempo real
La app intenta consultar el servicio de AppBus/TMG de la ciudad a través de una petición HTTP con parámetros como:

- línea
- dirección (anada/torna)
- código de la parada

La API parsea la respuesta para extraer tiempos de llegada, por ejemplo:

- `5 min`
- `12 minuts`
- `5m`
- `HH:MM`

Estos tiempos se ordenan y se muestran con formato amigable al usuario.

### 5. Fallback GTFS
Si el servicio en tiempo real no devuelve información o falla por red o cambios en la respuesta, la app usa los horarios programados desde `stop_times.txt` y `trips.txt`.

Esto asegura que la app siga funcionando aunque la fuente en vivo no responda.

### 6. Mapa y visualización
La parte frontal usa Leaflet para:

- mostrar la posición del usuario;
- mostrar la parada seleccionada;
- ajustar el mapa para ver ambas ubicaciones a la vez;
- mostrar las líneas con destino, hora y minutos aproximados.

## Arquitectura del proyecto

### Backend
El servidor principal está en `main.py` y usa FastAPI.

Sus responsabilidades son:

- servir la interfaz web en `/`;
- montar archivos estáticos en `/static`;
- exponer la API `/api/proxima-parada`;
- leer GTFS y calcular la parada más cercana;
- consultar AppBus/TMG para obtener información en vivo;
- devolver una respuesta JSON con la parada y los próximos autobuses.

### Frontend
La interfaz web está compuesta por:

- `index.html`: estructura base de la página;
- `static/styles.css`: estilos para la app;
- `static/js/app.js`: lógica del cliente, geolocalización, fetch a la API y renderizado de resultados.

### Datos
La carpeta `libs/` contiene los archivos GTFS del transporte:

- `stops.txt`: paradas geolocalizadas
- `stop_times.txt`: horarios de paso por parada
- `trips.txt`: viajes y relaciones con rutas
- `routes.txt`: nombre y códigos de las rutas
- `calendar.txt`, `calendar_dates.txt`, `agency.txt`, `feed_info.txt`, `shapes.txt`: metadatos y datos complementarios del GTFS

## API

### Endpoint principal

`GET /api/proxima-parada`

#### Parámetros

- `lat` (obligatorio): latitud del usuario
- `lon` (obligatorio): longitud del usuario
- `radio` (opcional): radio en metros para buscar paradas cercanas. Por defecto `100`

#### Ejemplo

```bash
curl "http://localhost:8000/api/proxima-parada?lat=41.983112&lon=2.824932&radio=100"
```

#### Respuesta esperada

```json
{
  "encontrada": true,
  "parada": {
    "stop_id": "1234",
    "stop_name": "Plaça de la Independència",
    "stop_lat": 41.9831,
    "stop_lon": 2.8249,
    "distancia_m": 42.8
  },
  "proximos_autobuses": [
    {
      "linea": "L1",
      "destino": "Montjuïc",
      "hora": "18:42",
      "minutos": 5,
      "fuente": "tmg_tiempo_real",
      "tiempo_real": true
    }
  ],
  "fuente_horarios": "tmg_tiempo_real",
  "tiempo_real_disponible": true
}
```

Si no se encuentra ninguna parada dentro del radio configurado, la API devuelve algo como:

```json
{
  "encontrada": false,
  "mensaje": "No hay paradas a menos de 100m",
  "parada_mas_cercana_m": 154.2
}
```

## Cómo funciona el flujo completo

1. El navegador pide permiso para acceder a la geolocalización.
2. Se obtiene latitud/longitud del usuario.
3. El frontend llama a `GET /api/proxima-parada` con esos datos.
4. El backend lee el GTFS y calcula la parada más cercana.
5. El backend consulta AppBus/TMG para obtener llegadas reales.
6. Si no hay tiempo real, usa el GTFS programado.
7. El frontend recibe el JSON y renderiza:
   - nombre de la parada;
   - distancia a la parada;
   - fuente de horarios (real o programada);
   - mapa con ubicaciones;
   - lista de autobuses.

## Estructura del repositorio

```text
.
├── main.py                 # API FastAPI + lógica del backend
├── index.html              # página principal de la app
├── buscar_parada.py        # script auxiliar para buscar parada a mano
├── Dockerfile              # imagen Docker de la app
├── docker-compose.yaml     # ejecución con Docker Compose
├── static/
│   ├── styles.css          # estilos de la interfaz
│   └── js/
│       └── app.js          # lógica del frontend
├── libs/
│   ├── agency.txt
│   ├── calendar.txt
│   ├── calendar_dates.txt
│   ├── feed_info.txt
│   ├── routes.txt
│   ├── shapes.txt
│   ├── stops.txt
│   ├── stop_times.txt
│   └── trips.txt
├── README.md               # documentación del proyecto
└── .gitignore              # archivos excluidos del control de versiones
```

## Requisitos

### Localmente

- Python 3.11+
- FastAPI
- Uvicorn
- Requests
- Datos GTFS en `libs/`

### Docker

- Docker
- Docker Compose

## Instalación local

1. Clona el repositorio:

```bash
git clone https://github.com/MiquelRoca08/Girona-Bus-Tracker.git
cd Girona-Bus-Tracker
```

2. Crea un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install fastapi uvicorn[standard] requests
```

4. Asegúrate de que en la carpeta `libs/` existen los archivos GTFS necesarios.

5. Ejecuta la app:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. Abre en el navegador:

```text
http://localhost:8000
```

## Ejecución con Docker

### Opción 1: Docker Compose

```bash
docker compose up --build
```

Esto levantará la aplicación en:

```text
http://localhost:8000
```

El archivo `docker-compose.yaml` monta la carpeta `libs` del proyecto dentro del contenedor para poder actualizar los datos GTFS sin reconstruir la imagen completa.

### Opción 2: construir la imagen manualmente

```bash
docker build -t girona-bus-tracker .
docker run -p 8000:8000 --name girona-bus-tracker girona-bus-tracker
```

## Variables de entorno

La app usa estas variables:

- `TMG_DEBUG=1`: activa logs de depuración para consultar el servicio AppBus/TMG
- `TZ=Europe/Madrid`: configura la zona horaria para cálculos de hora local

## Dependencias clave

- `fastapi`: servidor API
- `uvicorn`: servidor ASGI
- `requests`: peticiones HTTP al servicio de AppBus
- `csv`: lectura de archivos GTFS
- `Leaflet`: mapa interactivo en el navegador

## Casos de uso

La app es útil para:

- ver qué autobús está más cerca de ti;
- consultar la próxima parada en una zona desconocida;
- identificar rápidamente la línea adecuada en Girona;
- comprobar horarios reales cuando la información de la ciudad está disponible;
- usar la app desde un móvil con geolocalización.

## Limitaciones y consideraciones

- La app depende de que el archivo `libs/stops.txt` exista y esté bien formateado.
- Si los datos de AppBus cambian su estructura HTML o JSON, puede requerir ajustes en el parser.
- La precisión del cálculo depende de la calidad y disponibilidad del GPS del dispositivo.
- El servicio en tiempo real puede fallar si la API externa deja de responder o cambia la respuesta.
- La app está pensada para uso local o en un entorno de despliegue sencillo, no como sistema de transporte empresarial completo.

## Solución de problemas

### Error: no se encontró `stops.txt`
Asegúrate de que la carpeta `libs` existe y contiene los archivos GTFS válidos.

### La app no muestra horarios
Comprueba si hay conexión a internet y si el servicio AppBus responde correctamente.

### El GPS no funciona
Verifica que el navegador tiene permiso para acceder a la ubicación y que el dispositivo tiene señal GPS.

### La app no carga en Docker
Revisa que el puerto 8000 esté libre y que los volúmenes de `libs` estén montados correctamente.

## Licencia

Este proyecto se distribuye con fines educativos y de uso personal. Si quieres reutilizarlo en producción o adaptarlo a un entorno real, conviene revisar las condiciones del uso de los datos de transporte y del servicio externo.