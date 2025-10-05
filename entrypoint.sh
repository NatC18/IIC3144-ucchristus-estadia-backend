#!/bin/bash

# Inicialización del contenedor Django
# Este script se ejecuta dentro del contenedor para preparar la aplicación

set -e

echo "🔥 Iniciando UC Christus Backend..."

# Esperar a que PostgreSQL esté disponible
echo "⏳ Esperando PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "PostgreSQL no está disponible - durmiendo"
  sleep 1
done

echo "✅ PostgreSQL está disponible"

# Aplicar migraciones
echo "📋 Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

# Crear superusuario si no existe
echo "👤 Creando superusuario..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ucchristus.cl', 'admin123')
    print("Superusuario creado: admin/admin123")
else:
    print("Superusuario ya existe")
END

# Recopilar archivos estáticos
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 ¡UC Christus Backend listo!"

# Ejecutar el comando pasado como argumentos
exec "$@"