# 🏥 UC Christus Backend - Migración a PostgreSQL + Docker

## 📋 Resumen de Cambios

✅ **Completado:**
- ✅ Migración de SQLite a PostgreSQL
- ✅ Configuración completa de Docker
- ✅ Variables de entorno para múltiples ambientes
- ✅ Configuración de producción (Render/Railway/Heroku)
- ✅ Backup de datos existentes
- ✅ Archivos estáticos con WhiteNoise

## 🚀 Cómo ejecutar el proyecto

### 1. **Iniciar Docker Desktop**
Asegúrate de que Docker Desktop esté corriendo en tu Mac.

### 2. **Construir y ejecutar contenedores**
```bash
cd /Users/jeronimoinfante/Desktop/Desarrollo/IIC3144-ucchristus-estadia-backend

# Construir e iniciar todos los servicios
docker-compose up --build -d

# Ver logs
docker-compose logs -f web

# Parar servicios
docker-compose down

# Parar y limpiar todo (incluyendo volúmenes)
docker-compose down -v
```

### 3. **Importar datos existentes** (después del primer start)
```bash
# Acceder al contenedor Django
docker-compose exec web bash

# Importar datos del backup
python manage.py loaddata backup_data.json

# Salir del contenedor
exit
```

## 🔧 Estructura de servicios

### 📦 **Servicios incluidos:**
- **web**: Django application (Puerto 8000)
- **db**: PostgreSQL 15 (Puerto 5432)
- **redis**: Redis para caché (Puerto 6379)

### 🌍 **Acceso:**
- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Docs**: http://localhost:8000/api/docs/
- **PostgreSQL**: localhost:5432

### 👤 **Credenciales por defecto:**
- **Admin Django**: admin / admin123
- **PostgreSQL**: ucchristus_user / ucchristus_secure_password_2024

## 🔑 Variables de Entorno

### **Para desarrollo** (archivo `.env`):
```env
DEBUG=1
POSTGRES_DB=ucchristus_db
POSTGRES_USER=ucchristus_user
POSTGRES_PASSWORD=ucchristus_secure_password_2024
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Auth0 (reemplazar con valores reales)
AUTH0_DOMAIN=tu-dominio.auth0.com
AUTH0_AUDIENCE=tu-api-audience
AUTH0_CLIENT_ID=tu-client-id
AUTH0_CLIENT_SECRET=tu-client-secret
```

### **Para producción** (Render/Railway):
```env
DEBUG=0
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=tu-secret-key-super-seguro
ALLOWED_HOSTS=tu-app.onrender.com
RENDER_EXTERNAL_HOSTNAME=tu-app.onrender.com

# Auth0 (valores reales de producción)
AUTH0_DOMAIN=tu-dominio-real.auth0.com
AUTH0_AUDIENCE=tu-audience-real
AUTH0_CLIENT_ID=tu-client-id-real
AUTH0_CLIENT_SECRET=tu-client-secret-real
```

## 🚀 Deployment a Render

### 1. **Crear archivo `render.yaml`** (opcional):
```yaml
services:
  - type: web
    name: ucchristus-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn ucchristus_backend.wsgi:application
    envVars:
      - key: DEBUG
        value: 0
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: ucchristus-db
          property: connectionString

databases:
  - name: ucchristus-db
    databaseName: ucchristus_db
```

### 2. **Pasos en Render:**
1. Conectar repositorio GitHub
2. Crear PostgreSQL database
3. Crear Web Service con:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn ucchristus_backend.wsgi:application`
4. Configurar variables de entorno
5. Deploy automático

### 3. **Después del primer deploy:**
```bash
# Acceder a shell de Render
render shell

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Importar datos (si es necesario)
python manage.py loaddata backup_data.json
```

## 🛠️ Comandos útiles

### **Desarrollo local con Docker:**
```bash
# Ver estado de servicios
docker-compose ps

# Acceder a base de datos
docker-compose exec db psql -U ucchristus_user -d ucchristus_db

# Ejecutar comandos Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Ver logs específicos
docker-compose logs web
docker-compose logs db

# Reconstruir solo el servicio web
docker-compose up --build web
```

### **Backup y restore:**
```bash
# Backup de PostgreSQL
docker-compose exec db pg_dump -U ucchristus_user ucchristus_db > backup.sql

# Restore de PostgreSQL
docker-compose exec -T db psql -U ucchristus_user -d ucchristus_db < backup.sql

# Backup de Django (datos)
docker-compose exec web python manage.py dumpdata > backup_django.json

# Restore de Django (datos)
docker-compose exec web python manage.py loaddata backup_django.json
```

## 📁 Archivos clave creados/modificados

### **Nuevos archivos:**
- `Dockerfile` - Imagen de Django
- `docker-compose.yml` - Orquestación de servicios
- `init.sql` - Configuración inicial de PostgreSQL
- `entrypoint.sh` - Script de inicialización
- `.dockerignore` - Archivos a ignorar en build
- `backup_data.json` - Datos exportados de SQLite

### **Archivos modificados:**
- `requirements.txt` - Nuevas dependencias (psycopg, gunicorn, whitenoise)
- `ucchristus_backend/settings.py` - Configuración multi-ambiente
- `.env` / `.env.example` - Variables de entorno

## 🔒 Seguridad

### **En desarrollo:**
- ✅ Contraseñas por defecto (está bien para desarrollo)
- ✅ DEBUG=True habilitado
- ✅ CORS permisivo

### **En producción:**
- 🔴 Cambiar todas las contraseñas
- 🔴 DEBUG=False
- 🔴 Configurar CORS específico
- 🔴 Usar SECRET_KEY seguro
- 🔴 HTTPS habilitado

## 📈 Próximos pasos sugeridos

1. **Configurar Auth0** con valores reales
2. **Deploy a Render/Railway** para testing
3. **Configurar CI/CD** con GitHub Actions
4. **Monitoreo** con Sentry o similar
5. **Tests automatizados** con pytest

---

¡Tu aplicación ahora está completamente dockerizada y lista para producción! 🎉