# 🏥 UC Christus Backend API

Backend dockerizado para el sistema de gestión de pacientes y episodios UC Christus, construido con Django REST Framework, PostgreSQL y autenticación Auth0.

## 🚀 Características

- **🐳 Completamente Dockerizado** con PostgreSQL, Redis y Django
- **Django 4.2.7** con Dja## 📝 Próximos Pasos

### ✅ Completado
- ✅ **Sistema dockerizado** con PostgreSQL + Redis
- ✅ **Autenticación Auth0** funcionando sin recursión
- ✅ **CI/CD Pipeline completo** con GitHub Actions
- ✅ **Tests automatizados** (15 test cases)
- ✅ **Análisis de código** (flake8, bandit, safety)
- ✅ **Listo para deployment** en cualquier plataforma

### 🚧 Próximas Iteraciones
- [ ] **Modelos UC Christus** - Pacientes, Episodios, Camas
- [ ] **Endpoints CRUD** - API completa para el dominio
- [ ] **Tests expandidos** - Coverage 90%+
- [ ] **Deployment automático** - CD a Render/Railway
- [ ] **Monitoreo** - Sentry + logging estructurado
- [ ] **Performance** - Optimizaciones de queries + cache
- [ ] **Documentación API** - Swagger UI con ejemplos realesework
- **🗄️ PostgreSQL 15** como base de datos principal
- **🔐 Autenticación Auth0** con JWT tokens (sin recursión)
- **📊 Modelo de Usuario personalizado** integrado con Auth0
- **📖 API Documentation** automática con Swagger/OpenAPI
- **🚀 Listo para producción** en Render, Railway, Heroku
- **⚡ Redis** para caché y sesiones
- **🌐 CORS** configurado para desarrollo frontend

## ⚡ Inicio Rápido con Docker

### 1. Prerrequisitos
- Docker Desktop instalado y funcionando
- Git

### 2. Clonar y ejecutar
```bash
git clone <repository-url>
cd IIC3144-ucchristus-estadia-backend

# Construir e iniciar todos los servicios
docker-compose up --build -d

# Ver logs en tiempo real
docker-compose logs -f web
```

### 3. Acceder al sistema
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

### 4. Credenciales por defecto
- **Usuario Admin**: `admin`
- **PostgreSQL**: `ucchristus_user` / `ucchristus_secure_password_2024`

## 📋 Endpoints Disponibles

### 📖 Documentación
- `GET /api/docs/` - Documentación Swagger UI
- `GET /api/redoc/` - Documentación ReDoc
- `GET /api/schema/` - Esquema OpenAPI

### 💓 Health Checks
- `GET /api/health/` - Health check general
- `GET /api/auth/health/` - Health check de autenticación

### 🔐 Autenticación (requiere token Auth0)
- `GET /api/auth/profile/` - Perfil del usuario autenticado
- `GET /api/auth/users/` - Lista de usuarios (solo admin)
- `GET /api/auth/users/{id}/` - Detalle de usuario (solo admin)
- `POST /api/auth/logout/` - Logout

### ⚙️ Admin
- `GET /admin/` - Panel de administración Django

## � Servicios Docker

### Servicios incluidos:
- **`web`**: Django application (Puerto 8000)
- **`db`**: PostgreSQL 15 (Puerto 5432)
- **`redis`**: Redis para caché (Puerto 6379)

### Comandos útiles:
```bash
# Ver estado de contenedores
docker-compose ps

# Logs de servicio específico
docker-compose logs web
docker-compose logs db

# Ejecutar comandos Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Acceder a PostgreSQL
docker-compose exec db psql -U ucchristus_user -d ucchristus_db

# Parar servicios
docker-compose down

# Parar y limpiar todo (¡cuidado con los datos!)
docker-compose down -v
```

## ⚙️ Configuración

### Variables de entorno (archivo `.env`)
```env
# Django
DEBUG=1
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# PostgreSQL
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

# Redis
REDIS_URL=redis://redis:6379/0
```

### Configurar Auth0
1. Crea una aplicación en [Auth0 Dashboard](https://manage.auth0.com/)
2. Configura tu API en Auth0 Dashboard
3. Actualiza las variables en `.env` con tus valores reales

## 🔐 Autenticación

### Para desarrollo
```bash
# Sin token (endpoints públicos)
curl http://localhost:8000/api/health/

# Con token Auth0 (endpoints protegidos)
curl -H "Authorization: Bearer {tu-jwt-token}" \
     http://localhost:8000/api/auth/profile/
```

### Panel Admin
- URL: http://localhost:8000/admin/
- Usuario: `admin` (contraseña: la configurada)

## 🚀 Deployment a Producción

### Render/Railway/Heroku
El proyecto incluye `render.yaml` para deployment automático:

```yaml
# Variables de entorno para producción
DEBUG=0
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=tu-secret-key-super-seguro
ALLOWED_HOSTS=tu-app.onrender.com
```

### Pasos de deployment:
1. Push a GitHub
2. Conectar repositorio en Render
3. Configurar variables de entorno
4. Deploy automático

## 📁 Estructura del Proyecto

```
├── 🐳 docker-compose.yml     # Orquestación de servicios
├── 🐳 Dockerfile            # Imagen Django
├── 📊 usuarios/             # Modelo de usuario personalizado
├── 🔐 autenticacion/        # Middleware y autenticación Auth0
├── ⚙️ ucchristus_backend/   # Configuración Django
├── 🗄️ init.sql             # Configuración inicial PostgreSQL
├── 📋 requirements.txt      # Dependencias Python
├── 🌍 .env.example          # Variables de entorno template
├── 📚 DOCKER_MIGRATION_GUIDE.md # Guía detallada de Docker
└── 📖 README.md             # Este archivo
```

## 🔧 Stack Tecnológico

### Backend
- **Django 4.2.7** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL 15** - Base de datos principal
- **Redis 7** - Caché y sesiones
- **drf-spectacular** - Documentación OpenAPI

### Autenticación & Seguridad
- **Auth0** - Gestión de usuarios e identidad
- **PyJWT** - Validación de tokens JWT
- **WhiteNoise** - Archivos estáticos en producción

### DevOps & Deployment
- **Docker & Docker Compose** - Contenerización
- **Gunicorn** - Servidor WSGI para producción
- **psycopg** - Driver PostgreSQL para Python
- **django-cors-headers** - Soporte CORS

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/api/health/
# Respuesta: {"status":"ok","message":"UC Christus Backend API funcionando correctamente","version":"1.0.0"}

# Endpoint protegido sin token
curl http://localhost:8000/api/auth/users/
# Respuesta: {"detail":"Authentication credentials were not provided."}

# Verificar PostgreSQL
docker-compose exec db psql -U ucchristus_user -d ucchristus_db -c "SELECT count(*) FROM usuarios_usuario;"
```

## 📊 Backup y Restauración

```bash
# Backup de PostgreSQL
docker-compose exec db pg_dump -U ucchristus_user ucchristus_db > backup.sql

# Restore de PostgreSQL
docker-compose exec -T db psql -U ucchristus_user -d ucchristus_db < backup.sql

# Backup de datos Django
docker-compose exec web python manage.py dumpdata > backup_django.json

# Restore de datos Django
docker-compose exec web python manage.py loaddata backup_django.json
```

## � CI/CD Pipeline

### GitHub Actions configurado para:
- **🔍 Análisis de código** con flake8, bandit y safety
- **🧪 Tests automatizados** en cada push/PR
- **🐳 Build de Docker** y validación
- **🚀 Preparación** para deployment automático

### Estado del pipeline:
![CI/CD Status](https://github.com/NatC18/IIC3144-ucchristus-estadia-backend/workflows/🚀%20CI/CD%20Pipeline%20-%20UC%20Christus%20Backend/badge.svg)

### Tests incluidos:
```bash
## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/api/health/

# API documentation
curl http://localhost:8000/api/docs/
```

### Ejecutar Tests
```bash
# Ejecutar tests localmente
docker-compose exec web python manage.py test

# Análisis de código
flake8 .
bandit -r .
safety check
```

## 🔄 CI/CD Pipeline

El proyecto incluye un **pipeline completo de CI/CD con GitHub Actions** que se ejecuta automáticamente en cada push y pull request.

### Pipeline Overview
```yaml
# .github/workflows/ci-cd.yml
- 🔍 Code Quality     # flake8 + bandit + safety
- 🧪 Test & Build     # Django tests + Docker build
- 🚀 Prepare Deploy   # Deployment preparation
- 📊 Report Status    # Results summary
```

### Checks Automatizados
✅ **Calidad de Código**
- PEP8 compliance (flake8)
- Security analysis (bandit) 
- Dependency vulnerabilities (safety)

✅ **Testing Completo**
- 15 test cases covering:
  - Health endpoints
  - Authentication system
  - User models & database
  - API documentation
  - Security configurations

✅ **Build Validation**
- Docker image builds successfully
- All dependencies install correctly
- Environment configurations validated

### Status Badges
Una vez configurado el repositorio en GitHub, puedes añadir estos badges:

```markdown
![CI/CD Pipeline](https://github.com/tu-usuario/tu-repo/workflows/CI-CD/badge.svg)
![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-bandit%20checked-blue)
```
```

## �📝 Próximos Pasos

- ✅ Sistema dockerizado con PostgreSQL
- ✅ Autenticación Auth0 funcionando
- ✅ CI/CD Pipeline configurado
- ✅ Tests automatizados básicos
- ✅ Listo para deployment
- [ ] Crear modelos para Pacientes
- [ ] Crear modelos para Episodios 
- [ ] Implementar endpoints CRUD
- [ ] Expandir suite de tests
- [ ] Deployment automático a Render
- [ ] Monitoreo con Sentry

## 🆘 Troubleshooting

### Problemas comunes:
```bash
# Reiniciar servicios
docker-compose restart

# Ver logs de errores
docker-compose logs web

# Limpiar y reconstruir
docker-compose down -v
docker-compose up --build
```

---

**¿Necesitas ayuda?** Consulta el [DOCKER_MIGRATION_GUIDE.md](./DOCKER_MIGRATION_GUIDE.md) para instrucciones detalladas.
