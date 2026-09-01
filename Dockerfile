# Usar una imagen oficial de Python ligera
FROM python:3.11-slim
 
# Evitar que Python escriba archivos .pyc y asegurar logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
# Directorio de trabajo en el contenedor
WORKDIR /app
 
# Instalar dependencias necesarias
RUN pip install --no-cache-dir fastapi uvicorn[standard] requests
 
# Copiar todos los archivos del proyecto al contenedor
COPY . /app/

# Descargar los PDFs de horarios de cada parada en tiempo de build, para
# que queden "horneados" dentro de la imagen. Si el endpoint de Girona
# falla puntualmente durante el build, no queremos que rompa el build
# entero (la app funciona igual sin PDFs, el botón simplemente no
# aparece), así que se ejecuta con "|| true".
RUN python3 scripts/descargar_pdfs_paradas.py || true

# Guardar una copia "de fábrica" de libs/ y pdfs/ en rutas separadas.
# Esto es necesario porque, si en docker-compose.yaml el usuario monta
# ./libs o ./pdfs como bind mount, ese volumen TAPA por completo lo que
# haya en /app/libs y /app/pdfs dentro de la imagen. Guardando una copia
# aparte, el entrypoint puede rellenar el volumen del host la primera vez
# que esté vacío, sin depender de lo que quede "debajo" del mount.
RUN cp -a /app/libs /app/libs_default \
    && cp -a /app/pdfs /app/pdfs_default

RUN chmod +x /app/entrypoint.sh
 
# Exponer el puerto donde correrá la API
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# Comando para arrancar el servidor web
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]