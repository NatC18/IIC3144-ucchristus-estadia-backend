# 🏥 UC Christus Backend API

Backend dockerizado para el sistema de gestión de pacientes y episodios UC Christus, construido con Django REST Framework, PostgreSQL y autenticación Auth0.

## 🚀 Características Técnicas

- **🐍 Python 3.13.7** con Django 5.2.7 y Django REST Framework 3.16.1
- **🗄️ PostgreSQL 16** como base de datos principal
- **⚡ Redis 7** para caché y sesiones
- **🐳 Completamente Dockerizado** con docker-compose
- **🔐 Autenticación OAuth** con Auth0 + JWT tokens
- **📊 Sistema de carga de Excel** para administradores (pandas + openpyxl)
- **📖 API Documentation** automática con Swagger/OpenAPI (drf-spectacular)
- **🚀 Listo para producción** en Render, Railway, Heroku
- **🧪 Testing** con 15 casos de prueba (35.45% cobertura)
- **🔄 CI/CD Pipeline** con GitHub Actions (calidad, seguridad, tests)

## ⚡ Inicio Rápido

### 1. Prerrequisitos
- **Docker Desktop** instalado y funcionando
- **Git**

### 2. Instalación
```bash
# Clonar repositorio
git clone https://github.com/NatC18/IIC3144-ucchristus-estadia-backend.git
cd IIC3144-ucchristus-estadia-backend

# Iniciar servicios
docker-compose up --build -d
```

### 3. Crear superusuario
```bash
# Crear admin para el panel Django
docker-compose exec web python manage.py createsuperuser
```

### 4. Acceder al sistema
- **🌐 API Base**: http://localhost:8000
- **📖 Documentación Swagger**: http://localhost:8000/api/docs/
- **⚙️ Panel Admin**: http://localhost:8000/admin/
- **💓 Health Check**: http://localhost:8000/api/health/

## 📋 API Endpoints

### 📖 Documentación
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/docs/` | 📊 Documentación Swagger UI |
| `GET /api/redoc/` | 📚 Documentación ReDoc |
| `GET /api/schema/` | 🔧 Esquema OpenAPI |

### 💓 Health & Status
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/health/` | 💚 Health check general |
| `GET /api/auth/health/` | 🔐 Health check autenticación |

### ⚙️ Administración
| Endpoint | Descripción |
|----------|-------------|
| `/admin/` | 🛠️ Panel administración Django |
| `/admin/data_loader/` | 📊 Gestión de cargas Excel |

## 🐳 Servicios Docker

### 📦 Contenedores incluidos
| Servicio | Imagen | Puerto | Descripción |
|----------|--------|--------|-------------|
| **web** | `python:3.13-slim` | 8000 | 🐍 Aplicación Django |
| **db** | `postgres:16` | 5432 | 🗄️ Base de datos PostgreSQL |
| **redis** | `redis:7-alpine` | 6379 | ⚡ Caché y sesiones |

### 🔧 Comandos útiles
```bash
# Estado de contenedores
docker-compose ps

# Logs específicos
docker-compose logs -f web
docker-compose logs -f db

# Comandos Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test

# Acceso a PostgreSQL
docker-compose exec db psql -U ucchristus_user -d ucchristus_db

# Gestión de servicios
docker-compose down              # Parar servicios
docker-compose down -v           # Parar + eliminar volúmenes
docker-compose restart web       # Reiniciar servicio específico
```

## 🧪 Testing

### 📊 Suite de Tests
```bash
# Ejecutar todos los tests
docker-compose exec web python manage.py test --verbosity=2

# Coverage report
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### 🔍 Análisis de Calidad
```bash
# Análisis completo (CI/CD)
docker-compose exec web flake8 --max-line-length=120 .
docker-compose exec web bandit -r . --exclude ./venv
docker-compose exec web safety check
```

## 🔄 CI/CD Pipeline

### 🚀 GitHub Actions configurado
El pipeline se ejecuta automáticamente en:
- ✅ **Push a `main`** → CI completo + CD 

### 📋 Checks automatizados
```yaml
🔍 Code Quality:
  ├── flake8      # Estilo PEP8
  ├── bandit      # Vulnerabilidades seguridad
  └── safety      # Dependencias vulnerables

🧪 Test & Build:
  ├── 15 tests    # Django test suite
  ├── migrations  # Aplicación migraciones
  ├── collectstatic # Archivos estáticos
  └── docker build # Construcción imagen

🚀 Deploy (solo main):
  ├── build production image
  └── deployment summary
```

## 🚀 Deployment Producción

### 🔧 Steps deployment:
1. **Push código** a GitHub
2. **Conectar repo** en Render
3. **Configurar variables** de entorno
4. **Deploy automático** ✨

## 📁 Arquitectura del Proyecto

```
📦 IIC3144-ucchristus-estadia-backend/
├── 🐳 docker-compose.yml           # Orquestación servicios
├── 🐳 Dockerfile                   # Imagen Django
├── 📋 requirements.txt             # Dependencias Python 3.13
├── 🌍 .env.example                 # Template variables entorno
├── 📊 .coveragerc                  # Configuración coverage
├── 🔧 .vscode/settings.json        # Configuración VS Code
│
├── 👥 usuarios/                    # App: Modelo usuario personalizado
│   ├── models.py                   # User model integrado Auth0
│   ├── admin.py                    # Interface admin usuarios
│   └── migrations/                 # Migraciones DB
│
├── 🔐 autenticacion/               # App: Auth0 + Middleware
│   ├── authentication.py          # DRF Auth0 integration
│   ├── middleware.py               # JWT validation middleware  
│   ├── views.py                    # Auth endpoints
│   └── urls.py                     # Auth routing
│
├── 📊 data_loader/                 # App: Sistema carga Excel
│   ├── models.py                   # ExcelUpload model
│   ├── services.py                 # Excel processor (pandas)
│   ├── admin.py                    # Interface admin cargas
│   └── forms.py                    # Validación formularios
│
├── ⚙️ config/                     # Configuración Django
│   ├── settings/                   # Settings multi-environment
│   │   ├── base.py                 # Configuración común
│   │   ├── development.py          # Desarrollo local
│   │   └── production.py           # Producción
│   ├── urls.py                     # URL routing principal
│   ├── wsgi.py                     # WSGI production
│   └── asgi.py                     # ASGI async
│
├── 📱 apps/                        # Django Apps organizadas
│   ├── core/                       # App: Utilidades comunes
│   ├── usuarios/                   # App: Gestión usuarios
│   ├── autenticacion/              # App: Auth0 JWT
│   └── data_loader/                # App: Sistema carga Excel
│
├── 📋 requirements/                # Dependencias organizadas
│   ├── base.txt                    # Dependencias comunes
│   ├── development.txt             # Dependencias desarrollo
│   └── production.txt              # Dependencias producción
│
├── 🧪 tests.py                     # Test suite (15 casos)
├── 🗄️ init.sql                     # Configuración PostgreSQL
├── 📋 render.yaml                  # Deployment config
└── 🔄 .github/workflows/ci-cd.yml  # Pipeline GitHub Actions
```

## 🔧 Stack Tecnológico

### 🐍 Backend Core
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Python** | 3.13.7 | 🐍 Lenguaje base |
| **Django** | 5.2.7 | 🌐 Framework web |
| **Django REST Framework** | 3.16.1 | 🔗 API REST |
| **drf-spectacular** | 0.28.0 | 📖 Documentación OpenAPI |

### 🗄️ Base de Datos & Caché
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **PostgreSQL** | 16 | 🗄️ Base datos principal |
| **Redis** | 7-alpine | ⚡ Caché y sesiones |
| **psycopg** | 3.2.10 | 🔌 Driver PostgreSQL |

### 🔐 Autenticación & Seguridad
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Auth0** | OAuth 2.0 | 🔐 Gestión identidad |
| **PyJWT** | 2.10.1 | 🎫 Validación JWT |
| **django-cors-headers** | 4.9.0 | 🌐 Política CORS |

### 📊 Procesamiento Datos
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **pandas** | 2.3.3 | 📊 Procesamiento Excel |
| **openpyxl** | 3.1.5 | 📄 Lectura Excel |
| **xlsxwriter** | 3.2.9 | ✏️ Escritura Excel |

### 🚀 DevOps & Deploy
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Docker** | Latest | 🐳 Containerización |
| **Gunicorn** | 23.0.0 | 🔥 Servidor WSGI |
| **WhiteNoise** | 6.11.0 | 📁 Archivos estáticos |
| **GitHub Actions** | - | 🔄 CI/CD Pipeline |

### 🧪 Testing & Calidad
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **coverage.py** | 7.6.1 | 📊 Cobertura tests |
| **flake8** | 6.0.0 | 🔍 Linting PEP8 |
| **bandit** | 1.7.5 | 🛡️ Análisis seguridad |
| **safety** | 2.3.4 | 🔒 Vulnerabilidades deps |

## 🛠️ Flujo de Trabajo

### 📋 Proceso de Desarrollo

**🌿 Estrategia de Branches:**
```
main         ← Producción
├── develop  ← Integración y testing  
└── feature/ ← Desarrollo funcionalidades
```

**✅ Pull Requests y Revisión:**
- **CI Automático** ejecuta todos los checks de calidad
- **Revisión manual** de código y arquitectura
- **Merge** solo después de aprobación