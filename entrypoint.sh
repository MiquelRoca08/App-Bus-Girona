#!/bin/sh
# Entrypoint del contenedor.
#
# Si el usuario monta ./libs o ./pdfs como bind mount desde el host y esa
# carpeta está vacía (por ejemplo, la primera vez que se despliega), este
# script la rellena automáticamente con el contenido "de fábrica" que trae
# la imagen (guardado aparte en /app/libs_default y /app/pdfs_default para
# no chocar con el propio volumen).
#
# Si la carpeta del host YA tiene contenido, no se toca nada: así no se
# sobreescriben libs/pdfs que el usuario haya actualizado o añadido a mano.

set -e

rellenar_si_vacio() {
    origen="$1"
    destino="$2"
    nombre="$3"

    if [ ! -d "$origen" ]; then
        # No hay contenido "de fábrica" para este directorio (build sin red, etc.)
        return
    fi

    mkdir -p "$destino"

    if [ -z "$(ls -A "$destino" 2>/dev/null)" ]; then
        echo "[entrypoint] $destino está vacío, copiando contenido de fábrica de $nombre..."
        cp -a "$origen"/. "$destino"/
    else
        echo "[entrypoint] $destino ya tiene contenido, no se toca ($nombre)."
    fi
}

rellenar_si_vacio /app/libs_default /app/libs "libs"
rellenar_si_vacio /app/pdfs_default /app/pdfs "pdfs"

exec "$@"
