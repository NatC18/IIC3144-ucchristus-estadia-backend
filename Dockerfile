# Dockerfile para UC Christus Backend
FROM python:3.13-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app

# Copiar código de la aplicación
COPY . /app/

# Crear directorio staticfiles con permisos correctos
RUN mkdir -p /app/staticfiles && \
    chown -R app:app /app

USER app

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]