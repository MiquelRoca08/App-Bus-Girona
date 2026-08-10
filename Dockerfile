# Usar una imagen oficial de Python ligera
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y asegurar logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias necesarias
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# Copiar todos los archivos del proyecto al contenedor
COPY . /app/

# Exponer el puerto donde correrá la API
EXPOSE 8000

# Comando para arrancar el servidor web
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]