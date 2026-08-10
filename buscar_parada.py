import csv
import math
import os

# Define la ruta relativa a la carpeta libs desde la ubicación del script
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_STOPS = os.path.join(DIRECTORIO_BASE, "libs", "stops.txt")


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos puntos geográficos (lat, lon)
    utilizando la fórmula de Haversine.
    """
    R = 6371000  # Radio medio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distancia en metros


def buscar_parada_mas_cercana(archivo_stops, lat_usuario, lon_usuario, radio_max_m=50):
    """
    Lee un archivo stops.txt y devuelve la parada más cercana dentro del radio especificado.
    """
    if not os.path.exists(archivo_stops):
        print(f"❌ Error: No se encontró el archivo en la ruta '{archivo_stops}'")
        return None

    parada_cercana = None
    distancia_minima = float('inf')

    # encoding='utf-8-sig' previene errores si el archivo CSV tiene BOM
    with open(archivo_stops, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                stop_id = row['stop_id']
                stop_name = row['stop_name']
                stop_lat = float(row['stop_lat'])
                stop_lon = float(row['stop_lon'])
            except (KeyError, ValueError):
                continue

            # Calcular distancia en metros desde el móvil
            distancia = haversine(lat_usuario, lon_usuario, stop_lat, stop_lon)

            if distancia < distancia_minima:
                distancia_minima = distancia
                parada_cercana = {
                    'stop_id': stop_id,
                    'stop_name': stop_name,
                    'lat': stop_lat,
                    'lon': stop_lon,
                    'distancia_m': round(distancia, 2)
                }

    if parada_cercana and parada_cercana['distancia_m'] <= radio_max_m:
        return parada_cercana
    elif parada_cercana:
        print(f"⚠️ La parada más cercana ('{parada_cercana['stop_name']}') está a {parada_cercana['distancia_m']}m (fuera del margen de {radio_max_m}m).")
        return None
    else:
        return None


# --- Ejemplo de prueba con coordenadas de Girona ---
if __name__ == "__main__":
    # Coordenadas de ejemplo (Plaça de Catalunya / Pont de Pedra en Girona)
    lat_movil = 41.983112
    lon_movil = 2.824932

    print(f"Buscando en: {RUTA_STOPS}")
    print(f"Coordenadas del móvil: Lat {lat_movil}, Lon {lon_movil}\n")
    
    # Busca la parada usando la ruta configurada en ./libs/stops.txt
    resultado = buscar_parada_mas_cercana(RUTA_STOPS, lat_movil, lon_movil, radio_max_m=50)

    if resultado:
        print("✅ Parada detectada:")
        print(f" - Nombre: {resultado['stop_name']}")
        print(f" - ID Parada: {resultado['stop_id']}")
        print(f" - Distancia: {resultado['distancia_m']} metros")